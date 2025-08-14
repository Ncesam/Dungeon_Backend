from sqlalchemy import Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped


class BaseModel(DeclarativeBase):
    __abstract__ = True


class User(BaseModel):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)


class Lot(BaseModel):
    __tablename__ = 'lots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    price: Mapped[float] = mapped_column(Float)
