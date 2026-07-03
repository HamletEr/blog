from dataclasses import dataclass
from uuid import UUID


@dataclass
class User:
    id: UUID
    username: str
    email: str
    hashed_password: str
    is_active: bool
    role: str
