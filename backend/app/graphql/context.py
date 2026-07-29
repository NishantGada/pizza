from dataclasses import dataclass
from uuid import UUID

import strawberry
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import BaseContext

from app.core.security import decode_access_token
from app.services.errors import NotAuthenticated


@dataclass
class Context(BaseContext):
    session: AsyncSession
    user_id: UUID | None = None


def require_user(info: strawberry.Info) -> UUID:
    user_id = info.context.user_id
    if user_id is None:
        raise NotAuthenticated()
    return user_id


async def get_context(session: AsyncSession, authorization: str | None) -> Context:
    user_id: UUID | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        sub = decode_access_token(token)
        if sub:
            try:
                user_id = UUID(sub)
            except ValueError:
                user_id = None
    return Context(session=session, user_id=user_id)
