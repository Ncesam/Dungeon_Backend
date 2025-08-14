from typing import Generic, TypeVar, Type, Sequence, Any

from sqlalchemy import Row, RowMapping, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession, AsyncEngine

from database.models import BaseModel, Lot
from shared.config import Configuration

configuration = Configuration()
async_engine: AsyncEngine = create_async_engine(url=f"sqlite+aiosqlite:///{configuration.DATABASE_PATH}", echo=True)
session_maker = async_sessionmaker(bind=async_engine, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with session_maker() as session:
        yield session


ModelT = TypeVar('ModelT', bound=BaseModel)


class BaseRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: Type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def _execute(self, stmt):
        return await self.session.execute(stmt)

    async def get(self, obj_id: Any, *, options: Sequence = ()) -> ModelT | None:
        stmt = (
            select(self.model)
            .options(*options)
            .where(self.model.id == obj_id)
        )
        result = await self._execute(stmt)
        return result.scalar_one_or_none()

    async def list(
            self,
            *,
            filters: dict | None = None,
            options: Sequence = (),
    ) -> Sequence[Row[Any] | RowMapping | Any]:
        stmt = select(self.model).options(*options)
        if filters:
            for attr, value in filters.items():
                stmt = stmt.where(getattr(self.model, attr) == value)
        result = await self._execute(stmt)
        return result.scalars().all()

    async def create(self, obj_in: dict) -> None:
        obj = self.model(**obj_in)
        self.session.add(obj)

    async def update(self, db_obj: ModelT, obj_in: dict) -> None:
        for k, v in obj_in.items():
            setattr(db_obj, k, v)
        self.session.add(db_obj)

    async def delete(self, db_obj: ModelT) -> None:
        await self.session.delete(db_obj)


class LotRepository(BaseRepository[Lot]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Lot)
