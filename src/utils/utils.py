from typing import Annotated

from passlib.context import CryptContext
from pydantic import AfterValidator

from core.constants import MAX_PASS_LENGTH, MIN_PASS_LENGTH, SPECIAL_CHARS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def validate_password(v: str) -> str:
    includes_special_chars: bool = True
    includes_numbers: bool = True
    includes_lowercase: bool = True
    includes_uppercase: bool = True

    min_length: int = MIN_PASS_LENGTH
    max_length: int = MAX_PASS_LENGTH
    special_chars = SPECIAL_CHARS

    if len(v) < min_length or len(v) > max_length:
        raise ValueError(f"length should be at least {min_length} but not more than 20")

    if includes_numbers and not any(char.isdigit() for char in v):
        raise ValueError("Password should have at least one numeral")

    if includes_uppercase and not any(char.isupper() for char in v):
        raise ValueError("Password should have at least one uppercase letter")

    if includes_lowercase and not any(char.islower() for char in v):
        raise ValueError("Password should have at least one lowercase letter")

    if includes_special_chars and not any(char in special_chars for char in v):
        raise ValueError(
            f"Password should have at least one of the symbols {special_chars}"
        )

    return v


ValidatePassword = Annotated[str, AfterValidator(validate_password)]
