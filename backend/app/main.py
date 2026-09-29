from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config.cors import configure_cors
from app.config.database import Base, engine
from app.config.settings import get_settings
from app.controllers.gasto_controller import router as gasto_router
from app.exceptions.handlers import register_exception_handlers
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Controle de Gastos Pessoais", lifespan=lifespan)
register_exception_handlers(app)
configure_cors(app, get_settings())
app.include_router(gasto_router)
