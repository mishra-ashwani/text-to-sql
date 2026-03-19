import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_session
from app.database.models import SavedSchemaModel
from app.models.schemas import SavedSchema, SchemaInput

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/schemas", response_model=SavedSchema)
async def save_schema(
    saved_schema: SavedSchema, session: AsyncSession = Depends(get_session)
):
    db_schema = SavedSchemaModel(
        name=saved_schema.name,
        schema_json=saved_schema.schema_input.model_dump_json(),
    )
    session.add(db_schema)
    await session.commit()
    await session.refresh(db_schema)
    logger.info("Schema saved: %s (id=%s)", saved_schema.name, db_schema.id)
    return SavedSchema(
        id=db_schema.id,
        name=db_schema.name,
        schema_input=SchemaInput.model_validate_json(db_schema.schema_json),
        created_at=db_schema.created_at,
    )


@router.get("/schemas", response_model=list[SavedSchema])
async def list_schemas(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(SavedSchemaModel).order_by(SavedSchemaModel.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        SavedSchema(
            id=row.id,
            name=row.name,
            schema_input=SchemaInput.model_validate_json(row.schema_json),
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.get("/schemas/{schema_id}", response_model=SavedSchema)
async def get_schema(schema_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(SavedSchemaModel).where(SavedSchemaModel.id == schema_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Schema not found")
    return SavedSchema(
        id=row.id,
        name=row.name,
        schema_input=SchemaInput.model_validate_json(row.schema_json),
        created_at=row.created_at,
    )


@router.delete("/schemas/{schema_id}")
async def delete_schema(schema_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(SavedSchemaModel).where(SavedSchemaModel.id == schema_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Schema not found")
    await session.delete(row)
    await session.commit()
    logger.info("Schema deleted: id=%s", schema_id)
    return {"detail": "Schema deleted"}
