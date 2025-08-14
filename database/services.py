from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Lot
from database.repository import LotRepository
from shared.schemas import LotSchema


class BaseService:
    def __init__(self, session: AsyncSession):
        self.session = session


class LotService(BaseService):
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.lot_repository = LotRepository(session)

    @staticmethod
    def _build_orm(lot: LotSchema) -> Lot:
        schema = lot.model_dump()
        return Lot(**schema)

    async def add_lot(self, lot: LotSchema) -> LotSchema:
        orm_obj = self._build_orm(lot)
        self.session.add(orm_obj)
        await self.session.commit()
        await self.session.refresh(orm_obj)
        return LotSchema.model_validate(orm_obj, from_attributes=True)

    async def get_lot_by_id(self, lot_id: int) -> LotSchema | None:
        lot = await self.lot_repository.get(lot_id)
        if lot is None:
            return None
        return LotSchema.model_validate(lot, from_attributes=True)

    async def get_lots(self) -> list[LotSchema] | None:
        lots = await self.lot_repository.list()
        if lots is None:
            return None
        return [LotSchema.model_validate(lot, from_attributes=True) for lot in lots]
