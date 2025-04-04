from factory.fuzzy import FuzzyChoice

from db.models.message import Message
from tests.factories.base import BaseFactory
from tests.factories.fakers import UniqueFaker, UniqueStringFaker


class MessageFactory(BaseFactory):
    class Meta:
        model = Message

    chat_id = UniqueFaker("pyint")
    sender_id = UniqueFaker("pyint")
    text = UniqueStringFaker("text")
    app_type = FuzzyChoice([True, False])
