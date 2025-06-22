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

MIN_PASS_LENGTH: int = 8
MAX_PASS_LENGTH: int = 128

ACCESS_TOKEN_EXPIRATION_TIME_IN_MIN: int = 15
REFRESH_TOKEN_EXPIRATION_TIME_IN_MIN: int = 1440
JWT_ALGORITHM: str = "HS256"

MAX_MESSAGES_PER_MINUTE: int = 30
MAX_CONNECTIONS_PER_USER: int = 3
WEBSOCKET_PING_INTERVAL: int = 30
WEBSOCKET_PING_TIMEOUT: int = 10
