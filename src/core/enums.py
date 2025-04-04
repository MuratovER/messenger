from enum import Enum


class ChatTypeEnum(str, Enum):
    public = "Групповой"
    private = "Личный"
