import logging
from sqlalchemy import create_engine, Column, Integer, Time, String, func
from sqlalchemy.orm import sessionmaker, declarative_base

from app.logger import Logger


class DataBase:
    def __init__(self, db_file):
        self.logger = Logger().get_logger()  # Получаем логгер
        self.engine = create_engine('sqlite:///' + db_file)
        self.session_maker = sessionmaker(bind=self.engine)
        self.logger.info("Инициализирована база данных: %s", db_file)
        self.migration()

    def migration(self):
        Base.metadata.create_all(self.engine)
        self.logger.info("Миграция базы данных выполнена.")


class ServiceDatabase:
    def __init__(self):
        self.logger = Logger().get_logger()  # Получаем логгер
        self.database = DataBase('lot.db')
        self.session = self.database.session_maker()
        self.logger.info("Сервис базы данных инициализирован.")

    def add_lot(self, lot_id, name, price):
        try:
            self.session.add(LotsModel(lot_id=lot_id, name=name, price=price))
            self.session.commit()
            self.logger.info("Добавлен лот: ID=%s, Name=%s, Price=%s", lot_id, name, price)
        except Exception as e:
            self.logger.error("Ошибка при добавлении лота: %s", e)

    def get_lots(self):
        try:
            lots = self.session.query(LotsModel).all()
            self.logger.info("Получены все лоты: %d записей.", len(lots))
            return lots
        except Exception as e:
            self.logger.error("Ошибка при получении лотов: %s", e)
            return []

    def delete_lot(self, lot_id):
        try:
            deleted = self.session.query(LotsModel).filter_by(lot_id=lot_id).delete()
            self.session.commit()
            if deleted:
                self.logger.info("Удалён лот с ID=%s", lot_id)
            else:
                self.logger.warning("Лот с ID=%s не найден для удаления.", lot_id)
        except Exception as e:
            self.logger.error("Ошибка при удалении лота: %s", e)


Base = declarative_base()


class LotsModel(Base):
    __tablename__ = 'lots'

    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer)
    name = Column(String)
    price = Column(Integer)
    time = Column(Time, default=func.now())
    logging.info("Создана модель лота.")
