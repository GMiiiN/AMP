"""생활법률(AMP) 개발 환경 점검. 표준 라이브러리만 사용하므로 아무 Python 3.8 이상으로 실행할 수 있다.

저장소 루트를 기준으로 동작하므로 어느 폴더에서 실행해도 된다.
  python scripts/check_env.py                         설정 파일·판례 DB·설치 상태 점검
  python scripts/check_env.py --health                + app/.env 의 API 주소로 /health 확인
  python scripts/check_env.py --health http://127.0.0.1:8000

비밀 값(키)은 출력하지 않고 '있음/없음'만 표시한다.
종료 코드: 0 = 실패 항목 없음, 1 = 실패 항목 있음 (경고는 실패로 치지 않음)

모드 판단은 서버 코드와 맞춘다.
  - server/app/config.py: CONSULTATION_MODE 기본 demo, VECTOR_DB_PATH 기본 data/vector_db/precedents.sqlite3
    (상대 경로는 저장소 루트 기준), OS 환경변수가 server/.env 보다 우선(python-dotenv 기본 동작)
  - server/app/services/consultation.py: demo/rag 외의 모드는 503 CONFIG_ERROR,
    rag 에서 판례 DB가 없으면 503 INDEX_UNAVAILABLE
  - server/app/deps.py: rag + GEMINI_API_KEY 일 때만 Gemini 사용, 키가 없으면 고정 질문 + TF-IDF 검색 결과만 반환
  - server/app/services/rag.py: 색인과 서버의 임베딩 모델·차원이 다르면 TF-IDF로 대체
  - data/scripts/collect.py: LAW_API_OC 는 판례 수집에만 필요
  - app/src/services/consultation.ts: EXPO_PUBLIC_USE_API === "true" 일 때만 서버 호출, 주소는 http(s):// 로 시작
"""
from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from contextlib import closing
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / 'server'
APP_DIR = REPO_ROOT / 'app'
SERVER_ENV = SERVER_DIR / '.env'
SERVER_ENV_EXAMPLE = SERVER_DIR / '.env.example'
APP_ENV = APP_DIR / '.env'

DEFAULT_MODE = 'demo'
VALID_MODES = ('demo', 'rag')
DEFAULT_DB = 'data/vector_db/precedents.sqlite3'
DEFAULT_EMBEDDING_MODEL = 'gemini-embedding-001'
DEFAULT_EMBEDDING_DIMENSIONS = 768
EXAMPLE_API_URL = 'http://192.168.0.10:8000'
SECRET_NAME = re.compile(r'KEY|SECRET|TOKEN|PASSW|CREDENTIAL|PRIVATE|(^|_)OC$')
MIN_SERVER_PYTHON = (3, 11)
MIN_NODE = (22, 13)
SERVER_PACKAGES = ('fastapi', 'uvicorn', 'dotenv', 'numpy', 'sklearn', 'google/genai')

counts = {'OK': 0, 'INFO': 0, 'WARN': 0, 'FAIL': 0}


def report(level: str, message: str) -> None:
    counts[level] += 1
    print(f'  [{level}]'.ljust(9) + message)


def section(title: str) -> None:
    print(f'\n[{title}]')


def relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


def has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def presence(value: str | None) -> str:
    return '있음' if has_text(value) else '없음'


# ---------------------------------------------------------------- .env 읽기

def read_env_file(path: Path, label: str) -> dict[str, str]:
    """KEY=VALUE 를 읽는다. 인코딩 문제는 보고만 하고 최대한 읽는다."""
    raw = path.read_bytes()
    if raw.startswith(b'\xef\xbb\xbf'):
        report('WARN', f'{label} 맨 앞에 BOM이 있습니다. 첫 줄의 키가 무시될 수 있으니 "BOM 없는 UTF-8"로 다시 저장하세요.')
        raw = raw[3:]
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        level = 'FAIL' if path == SERVER_ENV else 'WARN'
        report(level, f'{label} 가 UTF-8이 아닙니다(메모장 ANSI 저장 등). 읽는 프로그램이 오류를 낼 수 있으니 UTF-8로 다시 저장하세요.')
        text = raw.decode('utf-8', errors='replace')
    return parse_env(text)


def parse_env(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[len('export '):].lstrip()
        key, sep, value = line.partition('=')
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if value[:1] in ('"', "'"):
            end = value.find(value[0], 1)
            if end > 0:
                value = value[1:end]
        else:
            match = re.search(r'\s#', value)  # 따옴표 없는 값의 " #" 뒤는 주석 (python-dotenv 와 같음)
            if match:
                value = value[:match.start()].rstrip()
        values[key] = value
    return values


class ServerSettings:
    """server/.env 와 OS 환경변수를 서버(config.py)와 같은 우선순위로 합친다."""

    def __init__(self, file_values: dict[str, str] | None):
        self.file_values = file_values or {}

    def source(self, name: str) -> str:
        if name in os.environ:
            return 'OS 환경변수'
        return 'server/.env' if name in self.file_values else '기본값'

    def get(self, name: str, default: str = '') -> str:
        """config.env 와 같다: 키가 있으면 빈 값이라도 그 값을 쓰고, 키가 없을 때만 기본값을 쓴다."""
        if name in os.environ:
            return os.environ[name].strip()
        if name in self.file_values:
            return self.file_values[name].strip()
        return default

    def get_int(self, name: str, default: int) -> int:
        try:
            return int(self.get(name) or default)
        except ValueError:
            return default


# ---------------------------------------------------------------- 서버 설정

def check_server() -> str:
    section('서버 설정  server/.env')
    file_values = None
    if not SERVER_ENV.is_file():
        report('WARN', 'server/.env 가 없습니다. 서버는 기본값(demo 모드)으로 뜹니다. '
                       'scripts/setup.ps1(또는 setup.sh)을 실행하거나 server/.env.example 을 복사하세요.')
    else:
        report('OK', 'server/.env 있음')
        file_values = read_env_file(SERVER_ENV, 'server/.env')
        if not SERVER_ENV_EXAMPLE.is_file():
            report('WARN', 'server/.env.example 이 없습니다. git checkout -- server/.env.example 로 되살리세요.')
        else:
            example_values = read_env_file(SERVER_ENV_EXAMPLE, 'server/.env.example')
            missing = [k for k in example_values if k not in file_values]
            if missing:
                report('INFO', 'server/.env 에 없는 키(서버 기본값 사용): ' + ', '.join(missing))

    settings = ServerSettings(file_values)
    for name in ('CONSULTATION_MODE', 'GEMINI_API_KEY', 'VECTOR_DB_PATH', 'LAW_API_OC'):
        if name in os.environ:
            report('INFO', f'{name}: OS 환경변수에 설정되어 있어 server/.env 보다 우선합니다.')

    mode = settings.get('CONSULTATION_MODE', DEFAULT_MODE)
    if not mode:
        report('FAIL', 'CONSULTATION_MODE 가 비어 있습니다. demo 또는 rag 를 적으세요(줄을 지우면 demo). '
                       '그대로면 상담 결과 요청이 503 CONFIG_ERROR 로 실패합니다.')
    elif mode not in VALID_MODES:
        shown = mode if re.fullmatch(r'[A-Za-z_-]{1,16}', mode) else '(알 수 없는 값)'
        report('FAIL', f'CONSULTATION_MODE = {shown}: demo 또는 rag 여야 합니다(소문자). '
                       '그대로면 상담 결과 요청이 503 CONFIG_ERROR 로 실패합니다.')
    elif mode == 'demo':
        report('OK', 'CONSULTATION_MODE = demo (외부 호출 없음, 키·판례 DB 불필요)')
    else:
        report('OK', 'CONSULTATION_MODE = rag (판례 DB 검색 + Gemini)')

    api_key = settings.get('GEMINI_API_KEY')
    key_source = f', {settings.source("GEMINI_API_KEY")}' if has_text(api_key) else ''
    if mode == 'rag':
        if has_text(api_key):
            report('OK', f'GEMINI_API_KEY: 있음{key_source} (질문 생성·임베딩 검색·AI 답변 사용)')
        else:
            report('WARN', 'GEMINI_API_KEY: 없음 (rag 모드지만 고정 질문 + TF-IDF 검색 결과만 반환, AI 답변 없음)')
    else:
        report('INFO', f'GEMINI_API_KEY: {presence(api_key)}{key_source} (demo 모드에서는 쓰지 않음)')

    report('INFO', f'LAW_API_OC: {presence(settings.get("LAW_API_OC"))} (판례 수집 data/scripts/collect.py 에만 필요)')
    for name in ('GEMINI_API_KEY', 'LAW_API_OC'):
        if settings.get(name).startswith('#'):
            report('WARN', f"{name} 값이 '#'로 시작합니다. python-dotenv 는 'KEY= # 메모'의 '# 메모'를 값으로 읽습니다. "
                           '메모는 다른 줄에 쓰세요.')

    check_database(settings, mode, has_text(api_key))
    return mode


def check_database(settings: ServerSettings, mode: str, has_key: bool) -> None:
    value = settings.get('VECTOR_DB_PATH', DEFAULT_DB)
    if not value:
        report('FAIL' if mode == 'rag' else 'INFO',
               'VECTOR_DB_PATH 가 비어 있습니다. 기본 경로(data/vector_db/precedents.sqlite3)를 쓰려면 그 줄을 지우세요.')
        return
    path = Path(value) if Path(value).is_absolute() else REPO_ROOT / value
    label = f'판례 DB {relative(path)}'
    if not path.is_file():
        if mode == 'rag':
            report('FAIL', f'{label}: 없음. rag 모드의 상담 결과 요청이 503 INDEX_UNAVAILABLE 로 실패합니다. '
                           '팀 비공개 Drive에서 받아 data/vector_db/ 에 두세요.')
        else:
            report('INFO', f'{label}: 없음 (demo 모드에서는 쓰지 않음, rag 전환 시 필요)')
        return
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)) as db:
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'metadata', 'documents'} <= tables:
                raise sqlite3.DatabaseError('필요한 테이블(metadata, documents)이 없음')
            total = db.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
            row = db.execute("SELECT value FROM metadata WHERE key='embedding'").fetchone()
            embedding = json.loads(row[0]) if row else None
    except (sqlite3.Error, ValueError, TypeError) as error:
        report('FAIL', f'{label}: 열 수 없습니다({type(error).__name__}). 파일이 손상되었거나 형식이 다릅니다. 다시 받으세요.')
        return
    if embedding:
        detail = f'임베딩 {embedding.get("model")}/{embedding.get("dimensions")}차원 포함'
    else:
        detail = 'TF-IDF만 (임베딩 없음)'
    level = 'OK' if total else 'WARN'
    report(level, f'{label}: 있음, 판례 {total}건, {detail}')
    if mode == 'rag' and has_key and embedding:
        server_model = settings.get('GEMINI_EMBEDDING_MODEL', DEFAULT_EMBEDDING_MODEL)
        server_dims = settings.get_int('GEMINI_EMBEDDING_DIMENSIONS', DEFAULT_EMBEDDING_DIMENSIONS)
        try:
            index_dims = int(embedding.get('dimensions') or 0)
        except (TypeError, ValueError):
            index_dims = 0
        if (embedding.get('model'), index_dims) != (server_model, server_dims):
            report('WARN', f'색인의 임베딩({embedding.get("model")}/{embedding.get("dimensions")})과 서버 설정'
                           f'({server_model}/{server_dims})이 달라 TF-IDF 검색으로 대체됩니다.')


# ---------------------------------------------------------------- 앱 설정

def check_api_url(url: str, required: bool) -> str | None:
    """형식이 맞으면 끝의 / 를 뺀 주소를 돌려준다."""
    if not has_text(url):
        if required:
            report('FAIL', 'EXPO_PUBLIC_API_URL: 비어 있습니다. 앱이 "API 주소를 설정해 주세요." 오류를 냅니다.')
        else:
            report('INFO', 'EXPO_PUBLIC_API_URL: 비어 있음 (USE_API=true 로 바꿀 때 필요)')
        return None
    level_bad = 'FAIL' if required else 'WARN'
    parsed = urllib.parse.urlsplit(url)
    try:
        port = parsed.port
    except ValueError:
        port = -1
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or port == -1
            or any(ch.isspace() for ch in url) or not re.match(r'^https?://', url)):
        # 키를 잘못 붙여 넣은 경우가 있을 수 있으므로 틀린 값은 화면에 보이지 않는다.
        report(level_bad, f'EXPO_PUBLIC_API_URL: 형식이 틀렸습니다(값은 표시하지 않음, {len(url)}자). '
                          'http:// 또는 https:// 로 시작해야 합니다. 예) http://192.168.0.23:8000, https://xxxx.trycloudflare.com')
        return None

    # 출력·요청에는 사용자 정보(user:pass@)와 쿼리를 뺀 주소만 쓴다.
    base = f'{parsed.scheme}://{parsed.netloc.rsplit("@", 1)[-1]}{parsed.path}'.rstrip('/')
    host = parsed.hostname
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None

    notes = []
    level = 'OK'
    if url == EXAMPLE_API_URL:
        level, notes = 'WARN', ['예시 값 그대로입니다. 실제 PC IPv4가 맞는지 확인하세요(setup 스크립트가 자동으로 바꿉니다)']
    elif host == 'localhost' or (address is not None and address.is_loopback):
        level, notes = 'WARN', ['휴대폰(실기기)에서는 휴대폰 자신을 가리킵니다. iOS 시뮬레이터·웹 전용']
    elif host == '10.0.2.2':
        notes = ['Android 에뮬레이터 전용 주소']
    elif address is not None and address.is_link_local:
        level, notes = 'WARN', ['169.254.x.x 는 네트워크 연결이 안 됐을 때 붙는 주소입니다. Wi-Fi 연결을 확인하세요']
    elif address is not None and address.is_private:
        notes = ['같은 네트워크(LAN) 주소']
    elif parsed.scheme == 'https':
        notes = ['HTTPS 주소(터널 등)']
    else:
        level, notes = 'WARN', ['외부 주소는 HTTPS를 쓰세요. 휴대폰 OS가 HTTP를 막을 수 있습니다']
    if parsed.scheme == 'http' and parsed.port is None:
        notes.append('포트가 없어 80번으로 접속합니다(서버 기본 포트는 8000)')
        level = 'WARN'
    if parsed.path not in ('', '/') or parsed.query or parsed.fragment:
        notes.append('주소 뒤 경로는 보통 필요 없습니다(앱이 /api/... 를 붙임)')
        level = 'WARN'
    if not required and level == 'WARN':
        level = 'INFO'  # 서버를 쓰지 않는 설정이면 참고로만 알린다
    report(level, f'EXPO_PUBLIC_API_URL = {base} (' + ', '.join(notes) + ')')
    return base


def check_app() -> str | None:
    section('앱 설정  app/.env')
    if not APP_ENV.is_file():
        report('WARN', 'app/.env 가 없습니다. 앱은 서버 없이 로컬 데모로 동작합니다. '
                       '서버에 붙이려면 setup 스크립트를 실행하거나 app/.env.example 을 복사하세요.')
        return None
    values = read_env_file(APP_ENV, 'app/.env')

    use_api = values.get('EXPO_PUBLIC_USE_API', '')
    if use_api == 'true':
        report('OK', 'EXPO_PUBLIC_USE_API = true (서버 API 사용)')
    elif use_api.strip().lower() in ('true', '1', 'yes', 'on'):
        report('WARN', f'EXPO_PUBLIC_USE_API = {use_api}: 앱은 소문자 true 만 인식합니다. 지금은 로컬 데모로 동작합니다.')
    else:
        report('INFO', 'EXPO_PUBLIC_USE_API 가 true 가 아니라 로컬 데모로 동작합니다(서버 호출 안 함).')

    base = check_api_url(values.get('EXPO_PUBLIC_API_URL', ''), required=use_api == 'true')

    for name, value in values.items():
        if not has_text(value) or not SECRET_NAME.search(name.upper()):
            continue
        if name.startswith('EXPO_PUBLIC_'):
            report('FAIL', f'{name}: 비밀 값으로 보입니다. EXPO_PUBLIC_* 는 앱 번들에 그대로 들어갑니다. 지우고 server/.env 로 옮기세요.')
        else:
            report('WARN', f'{name}: 비밀 값은 app/.env 가 아니라 server/.env 에 두세요.')
    return base


# ---------------------------------------------------------------- 설치 상태

def venv_python_version(venv: Path) -> tuple[int, ...] | None:
    cfg = venv / 'pyvenv.cfg'
    if not cfg.is_file():
        return None
    for line in cfg.read_text(encoding='utf-8', errors='replace').splitlines():
        key, _, value = line.partition('=')
        if key.strip() in ('version', 'version_info'):
            numbers = re.findall(r'\d+', value)
            if len(numbers) >= 2:
                return tuple(int(n) for n in numbers[:3])
    return None


def check_install() -> None:
    section('설치 상태')
    venv = SERVER_DIR / '.venv'
    if not venv.is_dir():
        report('WARN', 'server/.venv 없음. setup 스크립트를 실행하세요(-SkipServer 로 건너뛴 경우 정상).')
    else:
        version = venv_python_version(venv)
        shown = '.'.join(map(str, version)) if version else '버전 미확인'
        site_dirs = [venv / 'Lib' / 'site-packages', *sorted(venv.glob('lib/python3*/site-packages'))]
        missing = [p for p in SERVER_PACKAGES if not any((d / p).is_dir() for d in site_dirs)]
        if version and version[:2] < MIN_SERVER_PYTHON:
            report('FAIL', f'server/.venv 가 Python {shown} 입니다. 3.11 이상(3.12 권장)으로 venv를 다시 만드세요.')
        elif missing:
            report('WARN', f'server/.venv (Python {shown}): 패키지 미설치 {", ".join(missing)}. '
                           'pip install -r server/requirements.txt 를 실행하세요.')
        else:
            report('OK', f'server/.venv (Python {shown}), 필수 패키지 설치됨')

    expo = APP_DIR / 'node_modules' / 'expo' / 'package.json'
    if not expo.is_file():
        report('WARN', 'app/node_modules 없음. app 폴더에서 npm ci 를 실행하세요(-SkipApp 으로 건너뛴 경우 정상).')
    else:
        try:
            version = json.loads(expo.read_text(encoding='utf-8')).get('version', '?')
        except ValueError:
            version = '?'
        report('OK', f'app/node_modules 설치됨 (expo {version})')

    node = shutil.which('node')
    if not node:
        report('WARN', 'Node.js 를 찾지 못했습니다. 22.13 이상을 설치하세요.')
        return
    try:
        output = subprocess.run([node, '--version'], capture_output=True, text=True, timeout=15).stdout.strip()
        version = tuple(int(n) for n in re.findall(r'\d+', output)[:2])
    except (OSError, subprocess.SubprocessError, ValueError):
        output, version = '?', ()
    if len(version) == 2 and version >= MIN_NODE:
        report('OK', f'Node.js {output}')
    else:
        report('WARN', f'Node.js {output}: 22.13 이상을 권장합니다.')


# ---------------------------------------------------------------- /health

def check_health(base: str, local_mode: str) -> None:
    section('서버 응답  /health')
    url = base.rstrip('/') + '/health'
    host = urllib.parse.urlsplit(url).hostname or ''
    try:
        address = ipaddress.ip_address(host)
        direct = address.is_private or address.is_loopback
    except ValueError:
        direct = host == 'localhost'
    handlers = [urllib.request.ProxyHandler({})] if direct else []  # LAN 주소는 프록시를 거치지 않는다
    opener = urllib.request.build_opener(*handlers)
    request = urllib.request.Request(url, headers={'User-Agent': 'amp-check-env', 'Accept': 'application/json'})
    try:
        with opener.open(request, timeout=8) as response:
            status = response.status
            body = response.read()
    except urllib.error.HTTPError as error:
        report('FAIL', f'{url} → HTTP {error.code}. 주소가 이 프로젝트 서버가 맞는지 확인하세요.')
        return
    except (urllib.error.URLError, OSError, ValueError) as error:
        reason = getattr(error, 'reason', error)
        report('FAIL', f'{url} → 연결 실패({reason}). 서버 실행 여부, 같은 Wi-Fi 여부, '
                       'Windows 방화벽의 Python 개인 네트워크 허용을 확인하세요.')
        return
    try:
        payload = json.loads(body.decode('utf-8'))
    except ValueError:
        payload = None
    server_mode = payload.get('mode') if isinstance(payload, dict) else None
    if status == 200 and isinstance(payload, dict) and payload.get('status') == 'ok':
        report('OK', f'{url} → 200 status=ok mode={server_mode}')
        if server_mode != local_mode:
            report('INFO', f'응답 모드({server_mode})가 이 PC의 server/.env 모드({local_mode})와 다릅니다. '
                           '다른 PC의 서버이거나, .env 수정 후 서버를 다시 시작하지 않은 경우입니다.')
    else:
        report('FAIL', f'{url} → 응답 형식이 예상과 다릅니다(HTTP {status}).')


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='생활법률 개발 환경 점검 (키 값은 출력하지 않음)')
    parser.add_argument('--health', nargs='?', const='', metavar='URL',
                        help='서버 /health 확인. URL 을 생략하면 app/.env 의 EXPO_PUBLIC_API_URL, 그것도 없으면 http://127.0.0.1:8000')
    args = parser.parse_args(argv)

    print('== 생활법률 개발 환경 점검 ==')
    print(f'저장소: {REPO_ROOT}')
    mode = check_server()
    app_base = check_app()
    check_install()
    if args.health is not None:
        target = args.health.strip() or app_base or 'http://127.0.0.1:8000'
        if not re.match(r'^https?://[^\s/]+', target):
            section('서버 응답  /health')
            report('FAIL', f'--health 주소 형식이 틀렸습니다: {target}')
        else:
            check_health(target, mode)

    print(f"\n결과: 실패 {counts['FAIL']} · 경고 {counts['WARN']} · 확인 {counts['OK']} · 참고 {counts['INFO']}")
    if counts['FAIL']:
        print('실패 항목을 고친 뒤 다시 실행하세요. 안내: docs/SETUP.md')
    return 1 if counts['FAIL'] else 0


if __name__ == '__main__':
    sys.exit(main())
