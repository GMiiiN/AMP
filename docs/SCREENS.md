# 모바일 화면 명세 (11개)

사건 수정은 사건 상세 화면 안의 편집 상태로 구현하여 별도 화면 수에 포함하지 않습니다.

| 번호 | 화면 | Expo Router 파일 | 주요 동작 |
|---|---|---|---|
|1|회원가입|app/src/app/signup.tsx|이름·이메일·비밀번호 확인·3개 필수 동의|
|2|로그인|app/src/app/login.tsx|메모리 체험 계정 검증·회원가입 이동|
|3|홈|app/src/app/(tabs)/index.tsx|상담 시작·상황 검색 입력·최근 사건|
|4|상담 분야|app/src/app/categories.tsx|9개 분야와 기타 선택|
|5|상황 입력|app/src/app/situation.tsx|분야·날짜·금액·1,000자 설명·파일 선택|
|6|추가 질문|app/src/app/questions.tsx|3단계 보기/직접 입력·이전·건너뛰기·재시도|
|7|상담 결과|app/src/app/result.tsx|요약·근거 판례·원문 링크·체크리스트|
|8|사건 저장|app/src/app/save.tsx|제목·메모·기한·저장할 항목 선택|
|9|내 사건|app/src/app/(tabs)/cases.tsx|전체·진행 중·완료 필터|
|10|사건 상세|app/src/app/case-detail.tsx|개요·증거·기록 탭, 상태·할 일·수정·삭제·이어 상담|
|11|마이페이지|app/src/app/(tabs)/profile.tsx|프로필·약관·로그아웃·JSON 텍스트 공유·기기 데이터 삭제|

## 모바일 동작

- 하단 탭 3개: 홈 / 내 사건 / 마이페이지.
- 상담은 상단 뒤로가기 가능한 네이티브 스택으로 진행합니다.
- SafeAreaProvider로 노치·하단 안전 영역을 처리합니다.
- iOS KeyboardAvoidingView와 Android resize 설정을 적용합니다.
- 주요 동작 버튼 최소 높이 52, 입력·본문 스크롤 지원.
- 실제 파일 선택 UI는 expo-document-picker를 사용합니다. 원본은 보관하지 않습니다.
- 웹 미리보기는 보조 경로입니다. Android/iOS 입력기·안전 영역·파일 선택은 실기기 검증이 필요합니다.
