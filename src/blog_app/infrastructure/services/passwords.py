from argon2 import PasswordHasher as Argon
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from blog_app.domain.services.passwords import (
    PasswordComplexityValidator,
    PasswordHasher,
)


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


class PWComplexityValidator(PasswordComplexityValidator):
    def __init__(
        self, min_length: int = 8, max_length: int = 100, uniq_symbols: int = 5
    ) -> None:
        self.min_length = min_length
        self.max_length = max_length
        self.uniq_symbols = uniq_symbols

    def get_violations(self, password: str) -> list[str]:
        errors: list[str] = []

        if len(password) < self.min_length or len(password) > self.max_length:
            errors.append(
                f"Password must be between {self.min_length} and "
                f"{self.max_length} characters."
            )

        if len(set(password)) < self.uniq_symbols:
            errors.append(
                f"Password must contain at least {self.uniq_symbols} unique characters."
            )

        if password.isdigit():
            errors.append("Password must not contain only digits.")

        from string import ascii_letters

        easy_combinations = (
            ascii_letters,
            "qwertyuiop",
            "QWERTYUIOP",
            "asdfghjkl",
            "ASDFGHJKL",
        )
        if any(password in combination for combination in easy_combinations):
            errors.append("Password is too easy.")

        return errors
