# -*- coding: utf-8 -*-

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 创建对象的基类:
Base = declarative_base()
# 初始化数据库连接:
engine = create_engine('mysql+pymysql://root:123456@localhost:3306/stock?charset=utf8')

#返回数据库会话

Session = sessionmaker(bind=engine)
session = Session()



class IndexDaily(Base):
    __tablename__ = 'index_daily'

    id = Column(Integer, primary_key=True)
    code = Column(String(16))
    datetime = Column(String(20))
    open = Column(Float)
    close = Column(Float)
    low = Column(Float)
    high = Column(Float)
    volume = Column(Float)
    amount = Column(Float)

    def __init__(self, **items):
        for key in items:
            if hasattr(self, key):
                setattr(self, key, items[key])


class StockDataDaily(Base):
    __tablename__ = 'daily_stock'

    id = Column(Integer, primary_key=True)
    code = Column(String(16))
    datetime = Column(String(16))
    open = Column(Float)
    close = Column(Float)
    low = Column(Float)
    high = Column(Float)
    pre_close = Column(Float)
    volume = Column(Float)
    money = Column(Float)
    turnover = Column(Float)

    def __init__(self, **items):
        for key in items:
            if hasattr(self, key):
                setattr(self, key, items[key])