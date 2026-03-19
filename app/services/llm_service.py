import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

SQL_KEYWORDS = re.compile(
    r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP|WITH)\b", re.IGNORECASE
)


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key,
            request_timeout=settings.llm_timeout,
        )

    @staticmethod
    def _clean_response(text: str) -> str:
        """Strip markdown code fences if the LLM wraps the SQL."""
        text = text.strip()
        text = re.sub(r"^```(?:sql)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip()

    @staticmethod
    def _looks_like_sql(text: str) -> bool:
        """Check if the response looks like a SQL query."""
        return bool(SQL_KEYWORDS.search(text))

    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        cleaned = self._clean_response(response.content)

        if self._looks_like_sql(cleaned):
            logger.info("SQL generated successfully on first attempt")
            return cleaned

        # Retry once if response doesn't look like SQL
        logger.warning("LLM returned non-SQL response, retrying once")
        response = await self.llm.ainvoke(messages)
        cleaned = self._clean_response(response.content)

        if not self._looks_like_sql(cleaned):
            logger.error("LLM returned non-SQL response on retry")
            raise ValueError("LLM failed to generate a valid SQL query")

        return cleaned


llm_service = LLMService()
