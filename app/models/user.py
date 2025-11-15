from datetime import datetime
from app.db.base_class import Base
from sqlalchemy import Column, Integer, String, DateTime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    signup_date = Column(DateTime, default=datetime.now)
