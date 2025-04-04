from factory.fuzzy import FuzzyChoice

from core.enums import ChatTypeEnum
from db.models.chat import Chat
from tests.factories.base import BaseFactory
from tests.factories.fakers import UniqueStringFaker


class ChatFactory(BaseFactory):
    class Meta:
        model = Chat

    name = UniqueStringFaker("name")
    chat_type = FuzzyChoice(list(ChatTypeEnum))
