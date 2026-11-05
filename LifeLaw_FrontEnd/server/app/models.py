from datetime import date
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

Category = Literal['중고사기', '전세사기', '소음공해', '교통사고', '보이스피싱', '폭행', '임금체불', '명예훼손', '상속', '기타']
CATEGORIES = list(Category.__args__)
FIRST_QUESTIONS = ['거래 약속과 입금 내역이 남아 있나요?', '임대차 계약서를 가지고 있나요?', '소음이 발생한 날짜와 시간을 기록했나요?', '사고 당시 사진이나 영상이 있나요?', '상대방에게 돈이나 정보를 전달했나요?', '피해 상황을 확인할 자료가 있나요?', '약속한 급여와 지급일을 확인할 수 있나요?', '문제가 된 게시물이나 발언 기록이 있나요?', '가족관계와 재산 정보를 확인했나요?', '상황을 확인할 수 있는 자료가 있나요?']

class ConsultationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    category: Category
    date: date
    amount: str = Field(default='', max_length=12, pattern=r'^\d*$')
    description: str = Field(min_length=1, max_length=1000)
    answers: list[str] = Field(default_factory=list, max_length=3)

    @field_validator('date')
    @classmethod
    def not_future(cls, value):
        if value > date.today():
            raise ValueError('발생일은 미래일 수 없습니다.')
        return value

    @field_validator('answers')
    @classmethod
    def bound_answers(cls, values):
        if any(len(v) > 1000 for v in values):
            raise ValueError('답변은 1,000자 이하이어야 합니다.')
        return values

class Precedent(BaseModel):
    id: str
    title: str
    caseNumber: str
    court: str
    judgmentDate: str
    summary: str
    sourceUrl: str

class ConsultationResult(BaseModel):
    mode: Literal['demo', 'retrieval', 'rag']
    summary: str
    precedents: list[Precedent] = Field(default_factory=list)
    notice: str

class GeneratedAnswer(BaseModel):
    summary: str = Field(min_length=1, max_length=6000)
    citedIds: list[str] = Field(min_length=1, max_length=3)
