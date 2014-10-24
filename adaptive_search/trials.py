import json
from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import (TypeDecorator, Text, Float, Integer, Enum,
                              DateTime, String, Interval)
from sqlalchemy.orm import Session
Base = declarative_base()

__all__ = ['Trial']


class JSONEncoded(TypeDecorator):
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class Trial(Base):
    __tablename__ = 'experiments'

    id = Column(Integer, primary_key=True)
    status = Column(Enum('PENDING', 'SUCCEEDED', 'FAILED'))
    parameters = Column(JSONEncoded())
    mean_cv_score = Column(Float)
    cv_scores = Column(JSONEncoded())

    started = Column(DateTime())
    completed = Column(DateTime())
    elapsed = Column(Interval())
    host = Column(String(512))
    user = Column(String(512))
    traceback = Column(Text())


def make_session(uri, echo=False):
    engine = create_engine(uri, echo=echo)
    Base.metadata.create_all(engine)
    session = Session(engine)
    return session
