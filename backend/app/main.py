from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from strawberry.fastapi import GraphQLRouter

from app.core.config import settings
from app.db.session import get_session
from app.graphql.context import Context, get_context
from app.graphql.schema import schema


async def build_context(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> Context:
    return await get_context(session=session, authorization=request.headers.get("Authorization"))


def create_app() -> FastAPI:
    app = FastAPI(title="pizza", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    graphql_router: GraphQLRouter = GraphQLRouter(schema, context_getter=build_context)
    app.include_router(graphql_router, prefix="/graphql")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
