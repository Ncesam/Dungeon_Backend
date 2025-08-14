from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    ConfigDict(use_enum_values=True, extra='ignore', from_attributes=True)


class UserSchema(BaseSchema):
    id: int


class LotSchema(BaseSchema):
    id: int
    name: str
    price: int


class StartBotSchema(BaseSchema):
    item_id: int
    max_price: int
    user_id: int
    auth_key: str
    delay: int
    name: str
    vk_token: str
