from pydantic import BaseModel


class CallRequest(BaseModel):
    message: str
    to_phone_number: str