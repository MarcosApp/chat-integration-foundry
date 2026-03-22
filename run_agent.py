import os
from datetime import datetime

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ResponseStreamEventType
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT", "").strip()
AZURE_AGENT_ID = os.getenv("AZURE_EXISTING_AGENT_ID", "").strip()
AGENT_NAME, _, AGENT_VERSION = AZURE_AGENT_ID.partition(":")


def now_hhmm() -> str:
    return datetime.now().strftime("%H:%M")


def print_user_message(text: str) -> None:
    print(f"[{now_hhmm()}] You: {text}")


def print_agent_prefix() -> None:
    print(f"[{now_hhmm()}] Conviva:", end=" ", flush=True)


def run_whatsapp_mock_chat() -> None:
    if not AZURE_PROJECT_ENDPOINT:
        raise RuntimeError("AZURE_EXISTING_AIPROJECT_ENDPOINT nao configurado no .env")
    if not AGENT_NAME:
        raise RuntimeError("AZURE_EXISTING_AGENT_ID nao configurado no .env")

    project_client = AIProjectClient(
        endpoint=AZURE_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    workflow = {"name": AGENT_NAME, "version": AGENT_VERSION or "latest"}

    with project_client:
        openai_client = project_client.get_openai_client()
        conversation = openai_client.conversations.create()

        print("=" * 64)
        print("CONVIVA CHAT MOCK (WhatsApp-style no terminal)")
        print("Digite sua mensagem e pressione Enter.")
        print("Para sair: /exit")
        print("=" * 64)
        print(f"Conversation id: {conversation.id}")

        try:
            while True:
                user_text = input("\n> ").strip()
                if not user_text:
                    continue
                if user_text.lower() in {"/exit", "exit", "quit", "sair"}:
                    break

                print_user_message(user_text)

                stream = openai_client.responses.create(
                    conversation=conversation.id,
                    extra_body={
                        "agent_reference": {
                            "name": workflow["name"],
                            "type": "agent_reference",
                            **({"version": workflow["version"]} if workflow["version"] else {}),
                        }
                    },
                    input=user_text,
                    stream=True,
                    metadata={"x-ms-debug-mode-enabled": "1"},
                )

                printed_prefix = False
                saw_text_event = False

                for event in stream:
                    if event.type == ResponseStreamEventType.RESPONSE_OUTPUT_TEXT_DELTA:
                        if not printed_prefix:
                            print_agent_prefix()
                            printed_prefix = True
                        print(event.delta, end="", flush=True)
                        saw_text_event = True
                    elif event.type == ResponseStreamEventType.RESPONSE_OUTPUT_TEXT_DONE:
                        if not printed_prefix:
                            print_agent_prefix()
                            printed_prefix = True
                        if not saw_text_event and event.text:
                            print(event.text, end="", flush=True)
                            saw_text_event = True
                    elif (
                        event.type == ResponseStreamEventType.RESPONSE_OUTPUT_ITEM_DONE
                        and getattr(event.item, "type", None) == "workflow_action"
                    ):
                        # Keep workflow diagnostics concise without poluir a "bolha" de texto.
                        print(
                            f"\n  [workflow] {event.item.action_id}: {event.item.status}"
                        )

                if printed_prefix:
                    print()
                else:
                    print(f"[{now_hhmm()}] Conviva: (sem resposta textual)")
        finally:
            openai_client.conversations.delete(conversation_id=conversation.id)
            print("\nConversation deleted")


if __name__ == "__main__":
    run_whatsapp_mock_chat()
