from agent_service import AgentService


def main() -> None:
    service = AgentService()
    conversation_id = service.create_conversation()

    print(f"Created conversation (id: {conversation_id})")
    try:
        reply = service.send_message("Hello Agent", conversation_id)
        print(reply)
    finally:
        service.delete_conversation(conversation_id)
        print("Conversation deleted")


if __name__ == "__main__":
    main()
