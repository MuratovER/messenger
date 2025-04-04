from fastapi import HTTPException, status

not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Not found.",
)

chat_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Chat not found.",
)

message_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Message not found.",
)

incorrect_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password provided.",
)

incorrect_token_provided_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect token provided.",
)

user_not_found_exception = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="User not found.",
)

chat_uniquness_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Chat with exact name arleady exist.",
)

user_uniquness_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User with exact email arleady exist.",
)

user_not_participant_exception = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="You cannot create chat if you are not participant in it.",
)
