import re
from logging import getLogger
from typing import Any

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from config import get_settings


logger = getLogger(__name__)


class AgentService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _create_client(self) -> AIProjectClient:
        return AIProjectClient(
            endpoint=self.settings.azure_endpoint,
            credential=DefaultAzureCredential(),
        )

    def create_conversation(self) -> str:
        with self._create_client() as project_client:
            openai_client = project_client.get_openai_client()
            conversation = openai_client.conversations.create()
            return conversation.id

    def delete_conversation(self, conversation_id: str) -> None:
        with self._create_client() as project_client:
            openai_client = project_client.get_openai_client()
            openai_client.conversations.delete(conversation_id=conversation_id)

    def _clean_reply(self, reply: str) -> str:
        reply = re.sub(r"^\s*(?:TRUE|FALSE)\s*", "", reply, flags=re.IGNORECASE)
        lines = [line.rstrip() for line in reply.splitlines()]
        filtered_lines: list[str] = []
        custom_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.settings.hidden_response_patterns
        ]
        default_validation_patterns = [
            re.compile(
                r"^\s*(validacao|validation|validator|status de validacao)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"^\s*(campos validados|regras aplicadas|template)\b",
                re.IGNORECASE,
            ),
        ]

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if filtered_lines and filtered_lines[-1] != "":
                    filtered_lines.append("")
                continue

            if self.settings.hide_validation_messages and any(
                pattern.search(stripped) for pattern in default_validation_patterns
            ):
                continue

            if custom_patterns and any(
                pattern.search(stripped) for pattern in custom_patterns
            ):
                continue

            filtered_lines.append(stripped)

        cleaned = "\n".join(filtered_lines).strip()
        return cleaned or reply.strip()

    def _is_hidden_agent(self, item: dict[str, Any]) -> bool:
        agent_reference = item.get("agent_reference") or {}
        agent_name = str(agent_reference.get("name") or "").casefold()
        return bool(agent_name) and agent_name in self.settings.hidden_output_agents

    def _extract_replies(self, response: Any) -> list[str]:
        payload = response.model_dump(mode="python")
        replies: list[str] = []

        for item in payload.get("output", []):
            if item.get("type") != "message":
                continue
            if item.get("role") != "assistant":
                continue
            if self._is_hidden_agent(item):
                continue

            content_items = item.get("content") or []
            text_parts: list[str] = []
            for content in content_items:
                if content.get("type") != "output_text":
                    continue
                text = self._clean_reply(str(content.get("text") or ""))
                if text:
                    text_parts.append(text)

            message_text = "\n".join(text_parts).strip()
            if message_text:
                replies.append(message_text)

        if replies:
            return replies

        fallback = self._clean_reply(response.output_text or "")
        return [fallback] if fallback else []

    def send_message(self, message: str, conversation_id: str) -> list[str]:
        with self._create_client() as project_client:
            openai_client = project_client.get_openai_client()
            response = openai_client.responses.create(
                conversation=conversation_id,
                extra_body={
                    "agent_reference": {
                        "name": self.settings.workflow_name,
                        "type": "agent_reference",
                    }
                },
                input=message,
                metadata={"x-ms-debug-mode-enabled": "1"},
            )
            if self.settings.log_agent_response_json:
                logger.info(
                    "agent_response_json conversation_id=%s payload=%s",
                    conversation_id,
                    response.model_dump_json(indent=2),
                )
            replies = self._extract_replies(response)
            if self.settings.log_agent_responses:
                logger.info(
                    "agent_response conversation_id=%s replies=%r",
                    conversation_id,
                    replies,
                )
            return replies
