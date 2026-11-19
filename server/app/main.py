"""서버 진입점. 실행: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

구성 (QUR-004)
- routers/      요청 처리부: API 경로, 입력 검증
- services/     검색·생성부: 상담 흐름, 판례 검색(rag), Gemini 연계, 개인정보 가림
- repositories/ 저장소: 판례 색인(SQLite)
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import config
from .errors import install_error_handlers
from .routers import consultations

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
# HTTP 클라이언트의 요청별 로그는 끈다(외부 API 주소·요청 정보가 로그에 쌓이지 않도록).
for noisy in ('httpx', 'httpx2', 'google_genai'):
    logging.getLogger(noisy).setLevel(logging.WARNING)

app = FastAPI(title='생활법률 API', version='1.1.0',
              description='판례 기반 실생활 법률 상담 앱의 서버 API. 상담 기록과 사건은 기기에 저장하며 서버에는 판례 색인만 둔다.')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in config.env('CORS_ORIGINS', 'http://localhost:8081').split(',') if x.strip()],
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
    allow_headers=['Content-Type'],
)
install_error_handlers(app)
app.include_router(consultations.router)


@app.get('/health')
def health():
    return {'status': 'ok', 'mode': config.consultation_mode()}
