from advanced_alchemy.repository import SQLAlchemySyncRepository
from argon2 import PasswordHasher  # Usa argon2-cffi para el hashing y la verificación
from sqlalchemy.orm import Session

from .models import User

# Crea un hasher usando argon2-cffi
password_hasher = PasswordHasher()

class UserRepository(SQLAlchemySyncRepository[User]):
    model_type = User

    def add_with_password_hash(self, user: User) -> User:
        """Crea un nuevo usuario con una contraseña hasheada."""
        # Genera el hash de la contraseña
        user.password = password_hasher.hash(user.password)
        print(f"Generated hash: {user.password}")  # Línea de depuración para ver el hash generado
        return self.add(user)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verifica si la contraseña ingresada coincide con el hash almacenado."""
        try:
            # Verifica la contraseña utilizando argon2-cffi
            return password_hasher.verify(hashed_password, plain_password)
        except Exception:
            return False

async def provide_user_repository(db_session: Session) -> UserRepository:
    return UserRepository(session=db_session)