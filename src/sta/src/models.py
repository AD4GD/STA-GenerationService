from sqlalchemy import ARRAY, Column, Integer, String

from src.database import Base


class Pilot(Base):
    __tablename__ = "pilots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String, default=None)
    custom_endpoint = Column(String, default=None)
    graphs = Column(ARRAY(String))
    cached_properties = Column(Integer, default=None)
