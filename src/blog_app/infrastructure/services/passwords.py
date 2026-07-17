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

        self.violations: list[str] = []

    def _validate_length(self, password: str) -> None:
        if len(password) < self.min_length or len(password) > self.max_length:
            self.violations.append(
                f"Password must be between {self.min_length} and {self.max_length} characters."
            )

    def _validate_uniq_symbols(self, password: str) -> None:
        if len(set(password)) < self.uniq_symbols:
            self.violations.append(
                f"Password must contain at least {self.uniq_symbols} unique characters."
            )

    def _validate_digits_only(self, password: str) -> None:
        if password.isdigit():
            self.violations.append("Password must contain NOT only digits.")

    def _validate_easy_combinations(self, password: str) -> None:
        from string import ascii_letters

        easy_combinations = [
            ascii_letters,
            "qwertyuiop",
            "QWERTYUIOP",
            "asdfghjkl",
            "ASDFGHJKL",
        ]
        for combination in easy_combinations:
            if password in combination:
                self.violations.append("Password is too easy.")
                break

    def is_complexity_password(self, password: str) -> tuple[bool, list[str] | None]:
        self._validate_length(password)
        self._validate_uniq_symbols(password)
        self._validate_digits_only(password)
        self._validate_easy_combinations(password)

        return (True, None) if not self.violations else (False, self.violations)
