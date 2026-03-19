from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ColumnDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    data_type: str = Field(..., min_length=1, max_length=64)
    is_primary_key: bool = False
    is_nullable: bool = True
    default_value: Optional[str] = Field(None, max_length=256)
    foreign_key: Optional[str] = Field(None, max_length=256)


class TableDefinition(BaseModel):
    table_name: str = Field(..., min_length=1, max_length=128)
    columns: List[ColumnDefinition] = Field(..., min_length=1, max_length=100)


class SchemaInput(BaseModel):
    tables: List[TableDefinition] = Field(..., min_length=1, max_length=50)
    sql_dialect: Optional[str] = Field("postgresql", max_length=20)


class QueryRequest(BaseModel):
    schema_input: SchemaInput
    requirement: str = Field(..., min_length=1, max_length=2000)


class QueryResponse(BaseModel):
    sql_query: str
    formatted_query: str
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    explanation: Optional[str] = None


class SavedSchema(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=128)
    schema_input: SchemaInput
    created_at: Optional[datetime] = None


class QueryHistoryEntry(BaseModel):
    id: Optional[int] = None
    requirement: str
    generated_sql: str
    schema_name: Optional[str] = None
    created_at: Optional[datetime] = None
