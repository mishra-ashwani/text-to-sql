import re

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import settings


class LLMService:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.openai_api_key,
        )

    @staticmethod
    def _clean_response(text: str) -> str:
        """Strip markdown code fences if the LLM wraps the SQL."""
        text = text.strip()
        text = re.sub(r"^```(?:sql)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        return text.strip()

    async def generate_sql(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = await self.llm.ainvoke(messages)
        return self._clean_response(response.content)


llm_service = LLMService()
