"""요청·응답 형식 정의 (구 models.py)."""
from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

Category = Literal['중고사기', '전세사기', '소음공해', '교통사고', '보이스피싱', '폭행', '임금체불', '명예훼손', '상속', '기타']
CATEGORIES = list(Category.__args__)
# 생성 실패 시 대체용 고정 질문. 앱 src/domain/model.ts 와 같은 순서·문구를 유지한다.
FIRST_QUESTIONS = ['거래 약속과 입금 내역이 남아 있나요?', '임대차 계약서를 가지고 있나요?', '소음이 발생한 날짜와 시간을 기록했나요?', '사고 당시 사진이나 영상이 있나요?', '상대방에게 돈이나 정보를 전달했나요?', '피해 상황을 확인할 자료가 있나요?', '약속한 급여와 지급일을 확인할 수 있나요?', '문제가 된 게시물이나 발언 기록이 있나요?', '가족관계와 재산 정보를 확인했나요?', '상황을 확인할 수 있는 자료가 있나요?']
SECOND_QUESTION = '상대방에게 상황을 알리거나 대화를 시도했나요?'
THIRD_QUESTION = '지금 가장 먼저 정리하고 싶은 것은 무엇인가요?'


# ---------- 상담 ----------

class ConsultationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    category: Category
    date: date
    amount: str = Field(default='', max_length=12, pattern=r'^\d*$')
    description: str = Field(min_length=1, max_length=1000)
    answers: list[str] = Field(default_factory=list, max_length=3)
    # 선택 항목. 생성 질문을 쓰면 서버가 질문을 기억하지 않으므로, 앱이 보낸 질문과 답을 짝지어 AI에 전달한다.
    questions: list[str] = Field(default_factory=list, max_length=3)

    @field_validator('date')
    @classmethod
    def not_future(cls, value):
        if value > date.today():
            raise ValueError('발생일은 미래일 수 없습니다.')
        return value

    @field_validator('answers', 'questions')
    @classmethod
    def bound_items(cls, values):
        if any(len(v) > 1000 for v in values):
            raise ValueError('항목은 1,000자 이하이어야 합니다.')
        return values


class QuestionsResponse(BaseModel):
    questions: list[str] = Field(min_length=3, max_length=3)
    mode: Literal['generated', 'template']


class Precedent(BaseModel):
    id: str
    title: str
    caseNumber: str
    court: str
    judgmentDate: str
    summary: str
    sourceUrl: str
    cited: bool = False  # rag 모드에서 AI 답변이 근거로 인용한 판례


class WebSource(BaseModel):
    """기타 분야 웹 검색(Google Search grounding)이 참고한 웹 문서."""
    title: str
    url: str


class ConsultationResult(BaseModel):
    mode: Literal['demo', 'retrieval', 'rag']
    summary: str
    precedents: list[Precedent] = Field(default_factory=list)
    notice: str
    # 판례 검색에 쓴 방식. 임베딩 장애로 TF-IDF로 대체되면 'tfidf' (보고서 13장).
    searchMethod: Literal['embedding', 'tfidf'] | None = None
    # 기타 분야를 웹 검색으로 답했을 때만 채운다.
    sources: list[WebSource] = Field(default_factory=list)
    # 웹 검색 답변과 함께 보여 줘야 하는 Google Search Suggestions HTML(searchEntryPoint.renderedContent).
    # Gemini API 약관상 웹 검색 답변은 이 Search Suggestions 와 함께 표시한다. 일반 답변으로 대체되면 null.
    searchSuggestionsHtml: str | None = None


# ---------- 생성형 AI 응답 (서버 내부 검증용) ----------

class GeneratedAnswer(BaseModel):
    summary: str = Field(min_length=1, max_length=6000)
    citedIds: list[str] = Field(min_length=1, max_length=3)


class GeneralAnswer(BaseModel):
    summary: str = Field(min_length=1, max_length=6000)


class SearchAnswer(BaseModel):
    summary: str = Field(min_length=1, max_length=6000)
    sources: list[WebSource] = Field(min_length=1, max_length=5)
    suggestionsHtml: str = Field(min_length=1)


class GeneratedQuestions(BaseModel):
    questions: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=120)]] = Field(min_length=2, max_length=2)
