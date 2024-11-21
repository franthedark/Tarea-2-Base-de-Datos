from typing import Annotated, Any

from advanced_alchemy.exceptions import IntegrityError, NotFoundError
from litestar import Controller, Request, Response, Router, delete, get, patch, post
from litestar.di import Provide
from litestar.dto import DTOData
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from litestar.security.jwt import Token
from litestar.status_codes import HTTP_400_BAD_REQUEST, HTTP_200_OK
from pydantic import BaseModel
from typing import Annotated


from .dtos import Login, LoginDTO, UserCreateDTO, UserDTO, UserFullDTO, UserUpdateDTO
from .models import User
from .repositories import UserRepository, password_hasher, provide_user_repository
from .security import oauth2_auth

from datetime import datetime
from pydantic import BaseModel

class ChangePasswordRequest(BaseModel):
    username: str
    current_password: str
    new_password: str


class UserController(Controller):
    """Controller for user management."""

    path = "/users"
    tags = ["accounts | users"]
    return_dto = UserDTO
    dependencies = {"users_repo": Provide(provide_user_repository)}

    @get()
    async def list_users(self, users_repo: UserRepository) -> list[User]:
        return users_repo.list()

    @post(dto=UserCreateDTO, dependencies=None)
    async def create_user(self, users_repo: UserRepository, data: User) -> User:
        try:
            data.password = password_hasher.hash(data.password)  # Hashear la contraseña antes de guardar
            return users_repo.add_with_password_hash(data)
        except IntegrityError:
            raise HTTPException(detail="Username and/or email already in use", status_code=400)

    @get("/me", return_dto=UserFullDTO)
    async def get_my_user(self, request: "Request[User, Token, Any]", users_repo: UserRepository) -> User:
        # request.user does not have a session attached, so we need to fetch the user from the database
        return users_repo.get(request.user.id)
    
    @patch("/me/change-password")
    async def change_password(self, data: Annotated[ChangePasswordRequest, Body()], users_repo: UserRepository,) -> Response[None]:
    # Buscar el usuario en la base de datos
        user = users_repo.get_one_or_none(username=data.username)
        if not user:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Usuario no encontrado.")

    # Verificar que la contraseña actual sea correcta
        if not password_hasher.verify(data.current_password, user.password):
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="La contraseña actual es incorrecta.")
    
    # Verificar que la nueva contraseña no coincida con las últimas tres contraseñas
        if any(password_hasher.verify(data.new_password, old_password) for old_password in user.previous_passwords):
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="La nueva contraseña no debe coincidir con las últimas tres contraseñas.")

    # Actualizar la contraseña y el campo `previous_passwords`
        user.previous_passwords = ([user.password] + user.previous_passwords)[:3]  # Guardar el hash actual en `previous_passwords`
        user.password = password_hasher.hash(data.new_password)  # Guardar el nuevo hash en `password`

    # Actualizar el usuario en la base de datos
        users_repo.update(user)
        return Response(content=None, status_code=HTTP_200_OK)


    @get("/{user_id:int}", return_dto=UserFullDTO)
    async def get_user(self, user_id: int, users_repo: UserRepository) -> User:
        try:
            return users_repo.get(user_id)
        except NotFoundError:
            raise HTTPException(detail="User not found", status_code=404)

    @patch("/{user_id:int}", dto=UserUpdateDTO)
    async def update_user(self, user_id: int, data: DTOData[User], users_repo: UserRepository) -> User:
        try:
            user, _ = users_repo.get_and_update(id=user_id, **data.as_builtins(), match_fields=["id"])
            return user
        except NotFoundError:
            raise HTTPException(detail="User not found", status_code=404)

    @delete("/{user_id:int}")
    async def delete_user(self, user_id: int, users_repo: UserRepository) -> None:
        try:
            users_repo.delete(user_id)
        except NotFoundError:
            raise HTTPException(detail="User not found", status_code=404)


class AuthController(Controller):
    """Controller for authentication (login and logout)."""

    path = "/auth"
    tags = ["accounts | auth"]

    @post(
        "/login",
        dto=LoginDTO,
        dependencies={"users_repo": Provide(provide_user_repository)},
    )
    async def login(
        self,
        data: Annotated[Login, Body(media_type=RequestEncodingType.URL_ENCODED)],
        users_repo: UserRepository,
    ) -> Response[Any]:
        user = users_repo.get_one_or_none(username=data.username)
        if not user or not password_hasher.verify(data.password, user.password):
            raise HTTPException(detail="Invalid username or password", status_code=401)

        user.last_login = datetime.utcnow()
        users_repo.update(user)
        
        return oauth2_auth.login(
            identifier=str(user.username),
            response_status_code=HTTP_200_OK,
            token_extras={"name": user.full_name, "email": user.email or ""},
        )

    @post("/logout")
    async def logout(self) -> Response[None]:
        response = Response(content=None, status_code=HTTP_200_OK)
        response.delete_cookie("token")

        return response


accounts_router = Router(
    route_handlers=[UserController, AuthController],
    path="/accounts",
)