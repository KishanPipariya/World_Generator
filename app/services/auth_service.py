from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID, uuid4

from passlib.context import CryptContext

from app.schemas.auth import UserCreate, UserRead


class Neo4jDriverLike(Protocol):
    def session(self) -> Any: ...


_password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    username: str
    email: str
    created_at: datetime


class AuthService:
    def __init__(self, driver: Neo4jDriverLike) -> None:
        self._driver = driver

    def initialize_schema(self) -> None:
        queries = [
            "CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
            "CREATE CONSTRAINT user_username_unique IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
            "CREATE CONSTRAINT user_email_unique IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE",
        ]
        with self._driver.session() as session:
            for query in queries:
                session.run(query)

    def register(self, data: UserCreate) -> UserRead:
        username = data.username.strip()
        email = data.email.lower()
        if self.get_user_by_username_or_email(username, email):
            raise ValueError("Username or email already registered")

        user_id = uuid4()
        now = datetime.now(UTC)
        password_hash = _password_context.hash(data.password)
        query = """
        CREATE (u:User {
            id: $id, username: $username, email: $email,
            password_hash: $password_hash, created_at: $created_at
        })
        RETURN properties(u) AS props
        """
        first_user = self.user_count() == 0
        with self._driver.session() as session:
            result = session.run(
                query,
                id=str(user_id),
                username=username,
                email=email,
                password_hash=password_hash,
                created_at=now.isoformat(),
            )
            record = result.single()
            if not record:
                raise ValueError("Unable to register user")
        if first_user:
            self.assign_legacy_worlds(user_id)
        return self._user_from_record(record)

    def authenticate(self, username: str, password: str) -> UserRead | None:
        user = self._get_user_record_by_username_or_email(username.strip(), username.strip().lower())
        if not user:
            return None
        if not _password_context.verify(password, str(user["password_hash"])):
            return None
        return self._user_from_props(user)

    def get_user_by_id(self, user_id: UUID) -> UserRead | None:
        query = """
        MATCH (u:User {id: $id})
        RETURN properties(u) AS props
        """
        with self._driver.session() as session:
            record = session.run(query, id=str(user_id)).single()
            return self._user_from_record(record) if record else None

    def get_user_by_username_or_email(self, username: str, email: str) -> UserRead | None:
        props = self._get_user_record_by_username_or_email(username, email)
        return self._user_from_props(props) if props else None

    def _get_user_record_by_username_or_email(self, username: str, email: str) -> dict[str, object] | None:
        query = """
        MATCH (u:User)
        WHERE u.username = $username OR u.email = $email
        RETURN properties(u) AS props
        """
        with self._driver.session() as session:
            record = session.run(query, username=username, email=email).single()
            if not record:
                return None
            return record.get("props", record)

    def user_count(self) -> int:
        query = """
        MATCH (u:User)
        RETURN count(u) AS count
        """
        with self._driver.session() as session:
            record = session.run(query).single()
            return int(record["count"]) if record else 0

    def assign_legacy_worlds(self, user_id: UUID) -> int:
        query = """
        MATCH (w:World)
        WHERE w.owner_id IS NULL
        SET w.owner_id = $owner_id
        RETURN count(w) AS assigned
        """
        with self._driver.session() as session:
            record = session.run(query, owner_id=str(user_id)).single()
            return int(record["assigned"]) if record else 0

    @staticmethod
    def _user_from_record(record: dict[str, object]) -> UserRead:
        return AuthService._user_from_props(record.get("props", record))

    @staticmethod
    def _user_from_props(props: dict[str, object]) -> UserRead:
        return UserRead(
            id=UUID(str(props["id"])),
            username=str(props["username"]),
            email=str(props["email"]),
            created_at=datetime.fromisoformat(str(props["created_at"])),
        )
