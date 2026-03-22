import os
import re
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "sim"}


def _env_list(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _agent_env_name(prefix: str, workflow_name: str) -> str:
    safe_name = re.sub(r"[^A-Z0-9]+", "_", workflow_name.upper()).strip("_")
    return f"{prefix}_{safe_name}" if safe_name else prefix


def _workflow_parts() -> tuple[str, str]:
    agent_id = os.getenv("AZURE_EXISTING_AGENT_ID", "")
    name = os.getenv("AZURE_WORKFLOW_NAME", "")
    version = os.getenv("AZURE_WORKFLOW_VERSION", "")

    if (not name or not version) and ":" in agent_id:
        parsed_name, parsed_version = agent_id.split(":", 1)
        name = name or parsed_name
        version = version or parsed_version

    if not name or not version:
        raise RuntimeError(
            "Set AZURE_WORKFLOW_NAME and AZURE_WORKFLOW_VERSION or provide AZURE_EXISTING_AGENT_ID in name:version format."
        )

    return name, version


@dataclass(frozen=True)
class Settings:
    azure_endpoint: str
    workflow_name: str
    workflow_version: str
    app_host: str
    app_port: int
    app_secret_key: str
    chat_title: str
    chat_badge: str
    chat_subtitle: str
    chat_welcome: str
    chat_input_placeholder: str
    show_welcome_message: bool
    chat_panel_label: str
    chat_panel_title: str
    assistant_label: str
    user_label: str
    pending_message: str
    hide_validation_messages: bool
    hidden_response_patterns: list[str]
    hidden_output_agents: list[str]
    log_agent_responses: bool
    log_agent_response_json: bool


def get_settings() -> Settings:
    workflow_name, workflow_version = _workflow_parts()

    hidden_response_patterns = _env_list(
        _agent_env_name("AGENT_HIDE_PATTERNS", workflow_name),
        os.getenv("AGENT_HIDE_PATTERNS", ""),
    )
    hidden_output_agents = [
        item.casefold()
        for item in _env_list(
            _agent_env_name("AGENT_HIDE_OUTPUT_AGENTS", workflow_name),
            os.getenv("AGENT_HIDE_OUTPUT_AGENTS", ""),
        )
    ]
    hide_validation_messages = _env_bool(
        _agent_env_name("AGENT_HIDE_VALIDATION_MESSAGES", workflow_name),
        _env_bool("AGENT_HIDE_VALIDATION_MESSAGES", False),
    )

    return Settings(
        azure_endpoint=_required("AZURE_AI_PROJECT_ENDPOINT"),
        workflow_name=workflow_name,
        workflow_version=workflow_version,
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=int(os.getenv("APP_PORT", "8000")),
        app_secret_key=os.getenv("APP_SECRET_KEY", "change-me"),
        chat_title=os.getenv("CHAT_TITLE", "Workshop Agent"),
        chat_badge=os.getenv("CHAT_BADGE", "Template Generico"),
        chat_subtitle=os.getenv(
            "CHAT_SUBTITLE",
            "Template introdutorio para experimentar conversas, fluxos e integracoes com Azure AI Foundry.",
        ),
        chat_welcome=os.getenv(
            "CHAT_WELCOME", "Bem-vindo. Envie uma mensagem para iniciar a conversa."
        ),
        chat_input_placeholder=os.getenv(
            "CHAT_INPUT_PLACEHOLDER", "Digite sua mensagem..."
        ),
        show_welcome_message=_env_bool("CHAT_SHOW_WELCOME", True),
        chat_panel_label=os.getenv("CHAT_PANEL_LABEL", "Assistente"),
        chat_panel_title=os.getenv("CHAT_PANEL_TITLE", "Agent Console"),
        assistant_label=os.getenv("CHAT_ASSISTANT_LABEL", "Assistente"),
        user_label=os.getenv("CHAT_USER_LABEL", "Voce"),
        pending_message=os.getenv("CHAT_PENDING_MESSAGE", "Analisando..."),
        hide_validation_messages=hide_validation_messages,
        hidden_response_patterns=hidden_response_patterns,
        hidden_output_agents=hidden_output_agents,
        log_agent_responses=_env_bool("AGENT_LOG_RESPONSES", True),
        log_agent_response_json=_env_bool("AGENT_LOG_RESPONSE_JSON", True),
    )
