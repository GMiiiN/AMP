import unittest

from app.services.privacy import mask_text


class PrivacyMaskTests(unittest.TestCase):
    def test_masks_personal_identifiers(self):
        cases = {
            '주민번호 900101-1234567 입니다': '주민번호 [주민등록번호] 입니다',
            '전화 010-1234-5678 로': '전화 [전화번호] 로',
            '전화 01012345678 로': '전화 [전화번호] 로',
            '전화 +82 10-1234-5678': '전화 [전화번호]',
            '사무실 02-123-4567 번': '사무실 [전화번호] 번',
            '메일 hong.gd@example.co.kr 로': '메일 [이메일] 로',
            '계좌 110-123-456789 로 입금': '계좌 [계좌번호] 로 입금',
            '계좌 3333012345678 로 입금': '계좌 [계좌번호] 로 입금',
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(mask_text(text), expected)

    def test_keeps_dates_amounts_and_case_numbers(self):
        text = '2026-01-01에 1,500,000원과 20000원을 받기로 했고 2020다12345 판례를 봤어요. 3개월 근무.'
        self.assertEqual(mask_text(text), text)


if __name__ == '__main__':
    unittest.main()
