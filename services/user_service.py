# 사용자 인증 관련 로직 (비밀번호 해싱/검증, 최초 관리자 계정 시딩)

import os

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def seed_default_admin(db: Session) -> None:
    """
    컨테이너 최초 기동 시 관리자 계정이 하나도 없으면 .env 값으로 1개 생성.
    실습/데모 편의용이며, 실제 운영에서는 회원가입 절차나 별도 관리 도구로 대체해야 한다.
    """
    if db.query(User).count() > 0:
        return

    admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "changeme123")

    db.add(User(
        username=admin_username,
        hashed_password=hash_password(admin_password),
        role="admin",
    ))
    db.commit()
