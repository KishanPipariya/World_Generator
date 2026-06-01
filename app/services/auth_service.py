from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.schemas.auth import UserCreate, UserRead
from app.sqlite_driver import SQLiteDriver

_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    username: str
    email: str
    created_at: datetime


class AuthService:
    def __init__(self, driver: SQLiteDriver) -> None:
        self._driver = driver

    def initialize_schema(self) -> None:
        self._driver.initialize_schema()

    def register(self, data: UserCreate) -> UserRead:
        username = data.username.strip()
        email = data.email.lower()
        if self.get_user_by_username_or_email(username, email):
            raise ValueError("Username or email already registered")

        user_id = uuid4()
        now = datetime.now(UTC)
        password_hash = _password_context.hash(data.password)
        first_user = self.user_count() == 0
        record = self._driver.create_user(
            {
                "id": str(user_id),
                "username": username,
                "email": email,
                "password_hash": password_hash,
                "created_at": now.isoformat(),
            }
        )
        if first_user:
            self.assign_legacy_worlds(user_id)
        return self._user_from_props(record)

    def authenticate(self, username: str, password: str) -> UserRead | None:
        user = self._get_user_record_by_username_or_email(username.strip(), username.strip().lower())
        if not user:
            return None
        if not _password_context.verify(password, str(user["password_hash"])):
            return None
        return self._user_from_props(user)

    def get_user_by_id(self, user_id: UUID) -> UserRead | None:
        record = self._driver.get_user_by_id(str(user_id))
        return self._user_from_props(record) if record else None

    def get_user_by_username_or_email(self, username: str, email: str) -> UserRead | None:
        props = self._get_user_record_by_username_or_email(username, email)
        return self._user_from_props(props) if props else None

    def _get_user_record_by_username_or_email(self, username: str, email: str) -> dict[str, object] | None:
        return self._driver.get_user_by_username_or_email(username, email)

    def user_count(self) -> int:
        return self._driver.user_count()

    def assign_legacy_worlds(self, user_id: UUID) -> int:
        return self._driver.assign_legacy_worlds(str(user_id))

    @staticmethod
    def _user_from_props(props: dict[str, object]) -> UserRead:
        return UserRead(
            id=UUID(str(props["id"])),
            username=str(props["username"]),
            email=str(props["email"]),
            created_at=datetime.fromisoformat(str(props["created_at"])),
        )
