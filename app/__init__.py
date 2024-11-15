from litestar import Litestar, get
from app.config import settings
from app.database import sqlalchemy_plugin
from app.services.accounts.controllers import accounts_router
from app.services.accounts.security import oauth2_auth
from app.services.expenses.controllers import expenses_router

@get("/", exclude_from_auth=True)
async def root() -> dict:
    return {"message": "API is working!"}

app = Litestar(
    route_handlers=[accounts_router, expenses_router, root],  # Añadimos el endpoint de prueba
    plugins=[sqlalchemy_plugin],
    on_app_init=[oauth2_auth.on_app_init],
    debug=settings.debug,
)