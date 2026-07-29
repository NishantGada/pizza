from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models import BudgetSettings, User
from app.services.errors import Conflict, InvalidInput


def _normalize_email(raw: str) -> str:
    try:
        return validate_email(raw, check_deliverability=False).normalized.lower()
    except EmailNotValidError as exc:
        raise InvalidInput(str(exc)) from exc


async def register(session: AsyncSession, email: str, password: str) -> User:
    clean_email = _normalize_email(email)
    if len(password) < 8:
        raise InvalidInput("Password must be at least 8 characters.")

    exists = await session.scalar(select(User.id).where(User.email == clean_email))
    if exists:
        raise Conflict("An account with that email already exists.")

    user = User(email=clean_email, hashed_password=hash_password(password))
    session.add(user)
    await session.flush()

    session.add(
        BudgetSettings(
            user_id=user.id,
            savings_pct=settings.default_savings_pct,
            retirement_401k_pct=settings.default_retirement_401k_pct,
            hsa_per_cycle=settings.default_hsa_per_cycle,
        )
    )
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate(session: AsyncSession, email: str, password: str) -> User:
    clean_email = _normalize_email(email)
    user = await session.scalar(select(User).where(User.email == clean_email))
    if not user or not verify_password(password, user.hashed_password):
        raise InvalidInput("Invalid email or password.")
    return user


async def get_user(session: AsyncSession, user_id) -> User | None:
    return await session.get(User, user_id)
