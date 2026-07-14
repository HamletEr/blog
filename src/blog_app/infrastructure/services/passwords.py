from argon2 import PasswordHasher as Argon
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from blog_app.domain.services.passwords import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    def __init__(self) -> None:
        self.pw_hasher = Argon(
            time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16
        )

    async def hash(self, password: str) -> str:
        hashed = self.pw_hasher.hash(password)
        return hashed

    async def verify(self, password: str, hashed_password: str) -> bool:
        try:
            self.pw_hasher.verify(hash=hashed_password, password=password)
            return True
        except VerifyMismatchError:
            return False
        except (VerificationError, InvalidHashError):
            raise  # given string is not a valid hash
