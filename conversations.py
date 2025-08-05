from typing import Optional, Dict, List, Any


class ConversationContext:
    def __init__(self, context_id: str):
        self.context_id = context_id
        self.messages: List[Dict[str, str | Any]] = []

    def add_message(self, message: Dict[str, str | Any]):
        self.messages.append(message)

    def get_messages(self) -> List[Dict[str, Any]]:
        return self.messages

    def clear_messages(self):
        self.messages.clear()


class Conversations:
    def __init__(self):
        self.contexts: Dict[str, ConversationContext] = {}
        self.current: Optional[str] = None  # Current context ID

    def create_context(self, context_id: str):
        if context_id in self.contexts:
            raise ValueError(f"Context '{context_id}' already exists")

        context = ConversationContext(context_id)
        self.contexts[context_id] = context

        if not self.current:
            self.current = context_id

        return context

    def switch_context(self, context_id: str):
        if context_id not in self.contexts:
            raise ValueError(f"Context '{context_id}' does not exist")
        self.current = context_id
        return self.contexts[context_id]

    def get_current_context(self) -> Optional[ConversationContext]:
        return self.contexts.get(self.current, None)
