"""Standalone, opt-in FastAPI authentication preview.

Run from the existing server directory:
  uvicorn auth_preview.app:app --port 8001
No existing server source files are imported or modified.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import DateTime, Integer, String, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    rounds = 310_000
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, rounds)
    return f'pbkdf2_sha256${rounds}${salt.hex()}${digest.hex()}'


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, salt, digest = encoded.split('$')
        if algorithm != 'pbkdf2_sha256':
            return False
        iterations = int(n)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        test = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), bytes.fromhex(salt), iterations)
        return hmac.compare_digest(test, bytes.fromhex(digest))
    except (ValueError, TypeError):
        return False


def build_app(db_url: str | None = None, jwt_secret: str | None = None) -> FastAPI:
    # Config is mandatory; never create tokens using a public fallback secret.
    secret = jwt_secret or os.getenv('AMP_AUTH_JWT_SECRET', '')
    if len(secret) < 32:
        raise RuntimeError('Set AMP_AUTH_JWT_SECRET to a random secret of at least 32 characters.')
    path = Path(__file__).resolve().parent / '.local' / 'auth.sqlite3'
    url = db_url or os.getenv('AMP_AUTH_DB_URL', f'sqlite:///{path.as_posix()}')
    if url.startswith('sqlite:///') and ':memory:' not in url:
        # Only create the preview DB path, not any original project directories.
        Path(url.removeprefix('sqlite:///')).parent.mkdir(parents=True, exist_ok=True)
    connect_args = {'check_same_thread': False} if url.startswith('sqlite:') else {}
    engine = create_engine(url, connect_args=connect_args)
    Base.metadata.create_all(engine)  # Preview-only auto-create; migrate for production.
    session_factory = sessionmaker(engine, expire_on_commit=False)
    app = FastAPI(title='AMP 회원 인증 단독 미리보기', version='0.1.0')
    bearer = HTTPBearer(auto_error=False)

    def db_session():
        with session_factory() as session:
            yield session

    def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), session: Session = Depends(db_session)) -> User:
        if credentials is None or credentials.scheme.lower() != 'bearer':
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, '인증이 필요합니다.')
        try:
            claims = jwt.decode(credentials.credentials, secret, algorithms=['HS256'], options={'require': ['sub', 'exp', 'iat']})
            user_id = int(claims['sub'])
        except (jwt.PyJWTError, KeyError, ValueError, TypeError):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, '유효하지 않은 인증 토큰입니다.') from None
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, '유효하지 않은 사용자입니다.')
        return user

    @app.get('/health')
    def health():
        return {'status': 'ok', 'component': 'auth-preview'}

    @app.post('/api/auth/register', response_model=UserResponse, status_code=201)
    def register(payload: RegisterRequest, session: Session = Depends(db_session)):
        email = str(payload.email).lower()
        if session.scalar(select(User.id).where(User.email == email)) is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, '이미 가입된 이메일입니다.')
        record = User(name=payload.name, email=email, password_hash=hash_password(payload.password))
        session.add(record)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status.HTTP_409_CONFLICT, '이미 가입된 이메일입니다.') from None
        session.refresh(record)
        return record

    @app.post('/api/auth/login', response_model=TokenResponse)
    def login(payload: LoginRequest, session: Session = Depends(db_session)):
        record = session.scalar(select(User).where(User.email == str(payload.email).lower()))
        if record is None or not verify_password(payload.password, record.password_hash):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, '이메일 또는 비밀번호가 올바르지 않습니다.')
        now = datetime.now(timezone.utc)
        token = jwt.encode({'sub': str(record.id), 'iat': now, 'exp': now + timedelta(minutes=30)}, secret, algorithm='HS256')
        return TokenResponse(access_token=token)

    @app.get('/api/users/me', response_model=UserResponse)
    def me(user: User = Depends(current_user)):
        return user

    return app


# For isolated smoke tests import build_app directly. For normal uvicorn use `app`.
# Startup refuses to run without AMP_AUTH_JWT_SECRET.
if os.getenv('AMP_AUTH_PREVIEW_AUTOSTART') == '1':
    app = build_app()
