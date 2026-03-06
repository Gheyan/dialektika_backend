from pydantic import BaseModel, ConfigDict


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    email: str
    role: str