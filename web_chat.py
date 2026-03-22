import os

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import ResponseStreamEventType
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request

load_dotenv()

APP_TITLE = "Conviva Web Chat"
AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_EXISTING_AIPROJECT_ENDPOINT", "").strip()
AZURE_AGENT_ID = os.getenv("AZURE_EXISTING_AGENT_ID", "").strip()
AGENT_NAME, _, AGENT_VERSION = AZURE_AGENT_ID.partition(":")

app = Flask(__name__)


def create_project_client() -> AIProjectClient:
    if not AZURE_PROJECT_ENDPOINT:
        raise RuntimeError("AZURE_EXISTING_AIPROJECT_ENDPOINT nao configurado no .env")

    return AIProjectClient(
        endpoint=AZURE_PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )


def build_agent_reference() -> dict:
    if not AGENT_NAME:
        raise RuntimeError("AZURE_EXISTING_AGENT_ID nao configurado no .env")

    agent_reference = {"name": AGENT_NAME, "type": "agent_reference"}
    if AGENT_VERSION:
        agent_reference["version"] = AGENT_VERSION
    return agent_reference


@app.get("/")
def index():
    return render_template("index.html", app_title=APP_TITLE)


@app.post("/api/conversations")
def create_conversation():
    project_client = create_project_client()

    with project_client:
        openai_client = project_client.get_openai_client()
        conversation = openai_client.conversations.create()
        return jsonify(
            {"conversation_id": conversation.id, "agent_version": AGENT_VERSION or None}
        )


@app.post("/api/messages")
def stream_message():
    data = request.get_json(silent=True) or {}
    conversation_id = data.get("conversation_id", "").strip()
    text = data.get("message", "").strip()

    if not conversation_id:
        return jsonify({"error": "conversation_id is required"}), 400
    if not text:
        return jsonify({"error": "message is required"}), 400

    def generate():
        project_client = create_project_client()

        with project_client:
            openai_client = project_client.get_openai_client()
            stream = openai_client.responses.create(
                conversation=conversation_id,
                extra_body={"agent_reference": build_agent_reference()},
                input=text,
                stream=True,
                metadata={"x-ms-debug-mode-enabled": "1"},
            )

            saw_delta = False
            full_text = ""
            last_text_done = ""
            for event in stream:
                if (
                    event.type == ResponseStreamEventType.RESPONSE_OUTPUT_TEXT_DELTA
                    and event.delta
                ):
                    saw_delta = True
                    full_text += event.delta
                elif (
                    event.type == ResponseStreamEventType.RESPONSE_OUTPUT_TEXT_DONE
                    and event.text
                ):
                    last_text_done = event.text
                    if not saw_delta:
                        full_text += event.text

            final_text = last_text_done.strip() if last_text_done else full_text.strip()
            yield final_text

            print(
                (
                    f"[agent-response] conversation_id={conversation_id} "
                    f"input={text!r} output={final_text!r}"
                ),
                flush=True,
            )

    return Response(generate(), mimetype="text/plain; charset=utf-8")


@app.delete("/api/conversations/<conversation_id>")
def delete_conversation(conversation_id: str):
    project_client = create_project_client()

    with project_client:
        openai_client = project_client.get_openai_client()
        openai_client.conversations.delete(conversation_id=conversation_id)

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
