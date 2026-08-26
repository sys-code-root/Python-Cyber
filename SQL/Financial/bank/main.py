from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI

from database import engine, Base
from router import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="Automated Bank Reconciliation System", lifespan=lifespan)
app.include_router(router)