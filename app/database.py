import logging
import os

from sqlalchemy import create_engine, Column, Integer, Time, String, func
from sqlalchemy.orm import sessionmaker, declarative_base


class DataBase:
    def __init__(self, db_file):
        if not os.path.exists(db_file):
            with open('example.db', 'w') as file:
                pass
        self.engine = create_engine('sqlite:///' + db_file)
        self.session_maker = sessionmaker(bind=self.engine)
        logging.info("Инициализирована база данных: %s", db_file)

    def migration(self):
        Base.metadata.create_all(self.engine)
        logging.info("Миграция базы данных выполнена.")


class ServiceDatabase:
    def __init__(self):
        self.database = DataBase('lot.db')
        self.session = self.database.session_maker()
        logging.info("Сервис базы данных инициализирован.")

    def add_lot(self, lot_id, name, price):
        try:
            self.session.add(LotsModel(lot_id=lot_id, name=name, price=price))
            self.session.commit()
            logging.info("Добавлен лот: ID=%s, Name=%s, Price=%s", lot_id, name, price)
        except Exception as e:
            logging.error("Ошибка при добавлении лота: %s", e)

    def get_lots(self):
        try:
            lots = self.session.query(LotsModel).all()
            logging.info("Получены все лоты: %d записей.", len(lots))
            return lots
        except Exception as e:
            logging.error("Ошибка при получении лотов: %s", e)
            return []

    def delete_lot(self, lot_id):
        try:
            deleted = self.session.query(LotsModel).filter_by(lot_id=lot_id).delete()
            self.session.commit()
            if deleted:
                logging.info("Удалён лот с ID=%s", lot_id)
            else:
                logging.warning("Лот с ID=%s не найден для удаления.", lot_id)
        except Exception as e:
            logging.error("Ошибка при удалении лота: %s", e)


Base = declarative_base()


class LotsModel(Base):
    __tablename__ = 'lots'

    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer)
    name = Column(String)
    price = Column(Integer)
    time = Column(Time, default=func.now())
    logging.info("Создана модель лота.")
