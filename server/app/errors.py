"""공통 오류 응답. 형식: {"error": {"code": ..., "message": ...}} (INR-002).

오류 응답과 로그에는 사용자 입력 원문을 넣지 않는다 (SER-004, QUR-005).
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger('lifelaw')


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(code)
        self.status = status
        self.code = code
        self.message = message


def error_body(code: str, message: str) -> dict:
    return {'error': {'code': code, 'message': message}}


def ai_unavailable() -> ApiError:
    return ApiError(502, 'AI_UNAVAILABLE', 'AI 응답을 받지 못했습니다. 잠시 후 다시 시도해 주세요.')


_STATUS_CODES = {404: 'NOT_FOUND', 405: 'METHOD_NOT_ALLOWED'}
_STATUS_MESSAGES = {404: '요청한 주소를 찾을 수 없습니다.', 405: '허용되지 않은 요청 방식입니다.'}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(_: Request, exc: ApiError):
        if exc.status >= 500:
            logger.warning('api error status=%s code=%s', exc.status, exc.code)
        headers = {'WWW-Authenticate': 'Bearer'} if exc.status == 401 else None
        return JSONResponse(status_code=exc.status, content=error_body(exc.code, exc.message), headers=headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, __: RequestValidationError):
        # 검증 실패 내용에는 입력값이 들어 있으므로 돌려주지 않는다.
        return JSONResponse(status_code=422, content=error_body('VALIDATION_ERROR', '입력 항목과 형식을 확인해 주세요.'))

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException):
        code = _STATUS_CODES.get(exc.status_code, 'SERVICE_ERROR')
        message = _STATUS_MESSAGES.get(exc.status_code, '요청을 처리하지 못했습니다.')
        return JSONResponse(status_code=exc.status_code, content=error_body(code, message))

    @app.exception_handler(Exception)
    async def unexpected_error(_: Request, exc: Exception):
        logger.error('unexpected error type=%s', type(exc).__name__)
        return JSONResponse(status_code=500, content=error_body('SERVER_ERROR', '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'))
