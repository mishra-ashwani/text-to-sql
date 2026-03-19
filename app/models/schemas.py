from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ColumnDefinition(BaseModel):
    name: str
    data_type: str
    is_primary_key: bool = False
    is_nullable: bool = True
    default_value: Optional[str] = None
    foreign_key: Optional[str] = None


class TableDefinition(BaseModel):
    table_name: str
    columns: List[ColumnDefinition]


class SchemaInput(BaseModel):
    tables: List[TableDefinition]
    sql_dialect: Optional[str] = "postgresql"


class QueryRequest(BaseModel):
    schema_input: SchemaInput
    requirement: str


class QueryResponse(BaseModel):
    sql_query: str
    formatted_query: str
    is_valid: bool
    validation_errors: Optional[List[str]] = None
    explanation: Optional[str] = None


class SavedSchema(BaseModel):
    id: Optional[int] = None
    name: str
    schema_input: SchemaInput
    created_at: Optional[datetime] = None


class QueryHistoryEntry(BaseModel):
    id: Optional[int] = None
    requirement: str
    generated_sql: str
    schema_name: Optional[str] = None
    created_at: Optional[datetime] = None
