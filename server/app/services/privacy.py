"""외부 AI로 보내기 전에 개인정보 형태의 문자열을 가린다 (SER-004).

대상: 주민등록번호, 전화번호, 이메일, 계좌번호.
날짜(2026-01-01), 금액(1,500,000원), 사건번호(2020다12345)는 가리지 않는다.
"""
import re

_RRN = re.compile(r'(?<!\d)\d{6}\s?-\s?[1-8]\d{6}(?!\d)')
_EMAIL = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
_MOBILE = re.compile(r'(?<!\d)(?:\+82[-\s]?1[016789]|01[016789])[-\s.]?\d{3,4}[-\s.]?\d{4}(?!\d)')
# 지역번호·070 번호는 구분자가 있을 때만 전화번호로 본다(숫자열 오탐 방지).
_LANDLINE = re.compile(r'(?<!\d)(?:02|0[3-6][1-5]|070)[-\s.)]\s?\d{3,4}[-\s.]\d{4}(?!\d)')
# 계좌번호 후보: 하이픈으로 묶인 숫자 묶음 또는 10자리 이상 연속 숫자. 숫자 개수 10~16개만 가린다.
_ACCOUNT = re.compile(r'(?<![\d-])\d{2,8}(?:-\d{1,8}){1,4}(?![\d-])|(?<!\d)\d{10,16}(?!\d)')

PLACEHOLDERS = {
    'rrn': '[주민등록번호]',
    'email': '[이메일]',
    'phone': '[전화번호]',
    'account': '[계좌번호]',
}


def _mask_account(match: re.Match) -> str:
    digits = sum(ch.isdigit() for ch in match.group(0))
    return PLACEHOLDERS['account'] if 10 <= digits <= 16 else match.group(0)


def mask_text(text: str) -> str:
    text = _RRN.sub(PLACEHOLDERS['rrn'], text)
    text = _EMAIL.sub(PLACEHOLDERS['email'], text)
    text = _MOBILE.sub(PLACEHOLDERS['phone'], text)
    text = _LANDLINE.sub(PLACEHOLDERS['phone'], text)
    return _ACCOUNT.sub(_mask_account, text)
