from flask import Flask, jsonify, render_template, request, session
import logging

from agent_service import AgentService
from config import get_settings


settings = get_settings()
agent_service = AgentService()

app = Flask(__name__)
app.config["SECRET_KEY"] = settings.app_secret_key
logging.basicConfig(level=logging.INFO)


def _conversation_id() -> str:
    conversation_id = session.get("conversation_id")
    if conversation_id:
        return conversation_id

    conversation_id = agent_service.create_conversation()
    session["conversation_id"] = conversation_id
    return conversation_id


@app.get("/")
def index():
    conversation_id = session.pop("conversation_id", None)
    if conversation_id:
        agent_service.delete_conversation(conversation_id)
    return render_template("index.html", settings=settings)


@app.post("/api/chat")
def chat():
    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()

    if not message:
        return jsonify({"error": "A mensagem nao pode ficar vazia."}), 400

    replies = agent_service.send_message(message, _conversation_id())
    return jsonify({"reply": replies[0] if replies else "", "replies": replies})


@app.post("/api/reset")
def reset_chat():
    conversation_id = session.pop("conversation_id", None)
    if conversation_id:
        agent_service.delete_conversation(conversation_id)

    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host=settings.app_host, port=settings.app_port, debug=True)
