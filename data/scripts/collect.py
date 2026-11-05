"""Official law.go.kr XML API -> summary-only JSONL. Never writes full judgment body."""
import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'server'))
from app.models import CATEGORIES


def collect(category, query, pages, output):
    load_dotenv(ROOT / 'server' / '.env')
    oc = os.getenv('LAW_API_OC', '').strip()
    if not oc:
        raise ValueError('server/.env의 LAW_API_OC를 설정하세요.')
    rows = []
    seen = set()
    with httpx.Client(timeout=30) as client:
        for page in range(1, pages + 1):
            response = client.get('https://www.law.go.kr/DRF/lawSearch.do', params={'OC': oc, 'target': 'prec', 'type': 'XML', 'query': query, 'search': 2, 'display': 20, 'page': page})
            response.raise_for_status()
            root = ET.fromstring(response.content)
            if root.find('totalCnt') is None:
                raise ValueError('목록 응답 형식이 다릅니다. API 인증/승인 상태를 확인하세요.')
            for item in root.findall('.//prec'):
                seq = item.findtext('판례일련번호', '').strip()
                if not seq.isdigit() or seq in seen:
                    continue
                detail = client.get('https://www.law.go.kr/DRF/lawService.do', params={'OC': oc, 'target': 'prec', 'type': 'XML', 'ID': seq})
                detail.raise_for_status()
                info = ET.fromstring(detail.content)
                def field(name):
                    return info.findtext(name, '') or item.findtext(name, '')
                rows.append({'id': seq, 'category': category, 'title': field('사건명'), 'caseNumber': field('사건번호'), 'court': field('법원명'), 'judgmentDate': field('선고일자'), 'issues': field('판시사항'), 'summary': field('판결요지'), 'sourceUrl': 'https://www.law.go.kr/precInfoP.do?precSeq=' + seq, 'reviewed': False})
                seen.add(seq)
                time.sleep(0.2)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    print(f'{len(rows)}건 요지 저장. category 및 reviewed 필드를 검토한 뒤 전처리하세요: {output}')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--category', required=True, choices=[c for c in CATEGORIES if c != '기타'])
    p.add_argument('--query', required=True)
    p.add_argument('--pages', type=int, default=1)
    p.add_argument('--output', type=Path, default=ROOT / 'data/raw/precedents.jsonl')
    a = p.parse_args()
    if not 1 <= a.pages <= 10:
        p.error('--pages는 1~10입니다.')
    try:
        collect(a.category, a.query, a.pages, a.output)
    except Exception:
        # URLs in HTTP exception strings can contain OC; do not print raw exceptions.
        raise SystemExit('수집 실패: 인증값/권한, 네트워크, API 응답 형식 및 출력 경로를 확인하세요. 인증값은 로그에 출력하지 않습니다.') from None
