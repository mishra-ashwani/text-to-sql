from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Text

from app.database.db import Base


class SavedSchemaModel(Base):
    __tablename__ = "saved_schemas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, nullable=False)
    schema_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryHistoryModel(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    schema_name = Column(Text, nullable=True)
    is_valid = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
