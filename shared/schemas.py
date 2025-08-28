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


auth_key: "3a548454f70391405932bf4769761acc"
delay: 50
item_id: 534534
max_price: 10000
name: "Книга Дебила"
user_id: 214163323
