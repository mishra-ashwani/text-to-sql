from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_session
from app.database.models import QueryHistoryModel
from app.models.schemas import QueryHistoryEntry, QueryRequest, QueryResponse
from app.services.llm_service import llm_service
from app.services.prompt_builder import build_prompts
from app.services.sql_validator import check_schema_references, format_sql, validate_sql

router = APIRouter()


@router.post("/generate", response_model=QueryResponse)
async def generate_sql(
    request: QueryRequest, session: AsyncSession = Depends(get_session)
):
    if not request.schema_input.tables:
        raise HTTPException(status_code=400, detail="At least one table is required")
    if not request.requirement.strip():
        raise HTTPException(status_code=400, detail="Requirement cannot be empty")

    dialect = request.schema_input.sql_dialect or "postgresql"
    system_prompt, user_prompt = build_prompts(
        request.schema_input, request.requirement
    )

    try:
        raw_sql = await llm_service.generate_sql(system_prompt, user_prompt)
    except Exception:
        raise HTTPException(
            status_code=503, detail="AI service temporarily unavailable"
        )

    formatted = format_sql(raw_sql)
    is_valid, errors = validate_sql(raw_sql, dialect)
    warnings = check_schema_references(raw_sql, request.schema_input)
    all_errors = errors + warnings

    history = QueryHistoryModel(
        requirement=request.requirement,
        generated_sql=formatted,
        is_valid=is_valid,
    )
    session.add(history)
    await session.commit()

    return QueryResponse(
        sql_query=raw_sql,
        formatted_query=formatted,
        is_valid=is_valid and len(warnings) == 0,
        validation_errors=all_errors if all_errors else None,
    )


@router.get("/history", response_model=list[QueryHistoryEntry])
async def get_history(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(QueryHistoryModel).order_by(QueryHistoryModel.created_at.desc())
    )
    rows = result.scalars().all()
    return [
        QueryHistoryEntry(
            id=row.id,
            requirement=row.requirement,
            generated_sql=row.generated_sql,
            schema_name=row.schema_name,
            created_at=row.created_at,
        )
        for row in rows
    ]


@router.delete("/history/{history_id}")
async def delete_history(
    history_id: int, session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(QueryHistoryModel).where(QueryHistoryModel.id == history_id)
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="History entry not found")
    await session.delete(row)
    await session.commit()
    return {"detail": "History entry deleted"}
