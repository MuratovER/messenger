from db.models.chat_participant import ChatParticipant
from tests.factories.base import BaseFactory
from tests.factories.fakers import UniqueFaker


class ChatParticipantFactory(BaseFactory):
    class Meta:
        model = ChatParticipant

    chat_id = UniqueFaker("pyint")
    participant_id = UniqueFaker("pyint")
