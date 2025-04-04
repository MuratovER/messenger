SPECIAL_CHARS = (
    "$",
    "@",
    "#",
    "%",
    "!",
    "^",
    "&",
    "*",
    "(",
    ")",
    "-",
    "_",
    "+",
    "=",
    "{",
    "}",
    "[",
    "]",
)

MIN_PASS_LENGTH: int = 5
MAX_PASS_LENGTH: int = 20

ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN: int = 15
REFRES_TOKEN_EXPIRATION_TIME_IN_MIN: int = 150
JWT_ALGORITHM: str = "HS256"
