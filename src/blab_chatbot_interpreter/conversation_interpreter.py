import json
import re
from collections import deque
from dataclasses import dataclass
from itertools import islice
from operator import itemgetter
from pathlib import Path
from typing import Any, Literal, cast

from blab_chatbot_bot_client.conversation_websocket import (
    WebSocketBotClientConversation,
)
from blab_chatbot_bot_client.data_structures import (
    OutgoingMessage,
    MessageType,
    Message,
)
from jinja2 import Environment, FileSystemLoader, Template
from overrides import overrides

from blab_chatbot_interpreter.data_structures import UserMessageState, Task
from blab_chatbot_interpreter.interpreter_settings_format import (
    BlabInterpreterClientSettings,
)

_quotes = '«»“”"'


@dataclass
class UserMessage:
    def __init__(self, user_message: Message):
        self.user_message = user_message
        self.state: UserMessageState = UserMessageState.NEW
        self.correction_message: Message | None = None
        self.redirection_message: Message | None = None
        self.answer_message: Message | None = None
        self.completion_message: Message | None = None

    @property
    def id(self) -> str:
        return self.user_message.id

    @property
    def corrected_message(self) -> str | None:
        if not self.correction_message:
            return None
        return self.correction_message.text.strip().strip(_quotes)

    @property
    def chosen_bot_number(self) -> int | None:
        if not self.redirection_message:
            return None
        result = re.findall(r"\d+", self.redirection_message.text) or [0]
        return int(result[0])

    @property
    def answer(self) -> str | None:
        if not self.answer_message:
            return None
        return self.answer_message.text.strip().strip(_quotes)

    @property
    def complete_message(self) -> str | None:
        if not self.completion_message:
            return None
        return self.completion_message.text.strip().strip(_quotes)


class InterpreterWebSocketBotClientConversation(WebSocketBotClientConversation):
    settings: BlabInterpreterClientSettings

    def __init__(self, *args: Any, **kwargs: Any):
        """Create an instance. The history deque is initialized as empty."""
        super().__init__(*args, **kwargs)

        self.interpreter_ids: dict[Task, str | None] = {}

        self.debug: bool = bool(self.settings.INTERPRETER_SETTINGS.get("DEBUG", False))

        self.jinja_environments: dict[str, Environment] = {}
        self.templates: dict[Task, Template] = {}
        for t in Task.__members__.values():
            if t != Task.ANSWER:
                self._process_template_path(t)

        self.current_participants: dict[str, str] = {}
        # participant name -> participant id

        history_size = self.settings.INTERPRETER_SETTINGS["HISTORY_SIZE"]
        self.last_messages = deque(maxlen=max(1, history_size))

        self.user_messages: dict[str, UserMessage] = {}

        # the inner dicts map the requests message ids to the user message ids
        self.request_ids = {t: {} for t in Task.__members__.values()}

        # when our own messages are delivered: local id -> lambda
        self.on_delivery = {}

    def _process_template_path(self, task: Task):
        p = Path(
            self.settings.INTERPRETER_SETTINGS["TEMPLATE_FILE_NAMES"][
                cast(Literal["CORRECTION", "REDIRECTION", "COMPLETION"], task.name)
            ]
        )
        directory, name = str(p.parent), p.name
        if directory not in self.jinja_environments:
            self.jinja_environments[directory] = Environment(
                loader=FileSystemLoader(directory)
            )
        environment = self.jinja_environments[directory]
        self.templates[task] = environment.get_template(name)

    def send_debug_message(self, text: str):
        self.enqueue_message(
            OutgoingMessage(
                type=MessageType.TEXT,
                text=text,
                local_id=self.generate_local_id(),
                command=json.dumps({"self_approve": True}),
            )
        )

    def handle_new_message(self, message: Message):
        if message.id in self.user_messages:
            return
        if self.debug:
            self.send_debug_message(f"#DEBUG\nmessage from user:\n«{message.text}»")
        user_message = UserMessage(message)
        self.user_messages[message.id] = user_message
        self.last_messages.append(message)
        h = self.last_messages
        correction_prompt = self.templates[Task.CORRECTION].render(history=h)
        user_message.state = UserMessageState.AWAITING_CORRECTION
        local_id = self.generate_local_id()
        self.on_delivery[local_id] = (
            self.request_ids[Task.CORRECTION],
            message,
        )
        self.enqueue_message(
            OutgoingMessage(
                type=MessageType.TEXT,
                text=correction_prompt,
                local_id=local_id,
                command=json.dumps(
                    {
                        "self_redirect": True,
                        "bots": [self.interpreter_ids[Task.CORRECTION]],
                        "overrides": {"sent_by_human": True},
                    }
                ),
            )
        )

    def handle_correction(self, correction_message: Message, user_message: UserMessage):
        if user_message.state != UserMessageState.AWAITING_CORRECTION:
            return  # should not happen
        user_message.correction_message = correction_message
        if self.debug:
            self.send_debug_message(
                f"#DEBUG\ncorrection from interpreter:\n«{correction_message.text}»"
            )
        redirection_prompt = self.templates[Task.REDIRECTION].render(
            user_message=user_message.corrected_message,
            bots=self.settings.INTERPRETER_SETTINGS["ANSWERERS"],
        )
        user_message.state = UserMessageState.AWAITING_REDIRECTION
        local_id = self.generate_local_id()
        self.on_delivery[local_id] = (
            self.request_ids[Task.REDIRECTION],
            user_message,
        )
        self.enqueue_message(
            OutgoingMessage(
                type=MessageType.TEXT,
                text=redirection_prompt,
                local_id=local_id,
                command=json.dumps(
                    {
                        "self_redirect": True,
                        "bots": [self.interpreter_ids[Task.REDIRECTION]],
                        "overrides": {"sent_by_human": True},
                    }
                ),
            )
        )

    def handle_redirection(
        self, redirection_message: Message, user_message: UserMessage
    ):
        if user_message.state != UserMessageState.AWAITING_REDIRECTION:
            return  # should not happen
        user_message.redirection_message = redirection_message
        chosen_number = user_message.chosen_bot_number
        answerers = self.settings.INTERPRETER_SETTINGS["ANSWERERS"]
        if chosen_number == 0:
            return  # TO DO: warning
        elif not (1 <= chosen_number <= len(answerers)):
            return  # should not happen
        chosen_bot_name = next(
            islice(answerers.keys(), chosen_number - 1, chosen_number)
        )
        if self.debug:
            self.send_debug_message(
                f"#DEBUG\nredirection from interpreter:\n«{redirection_message.text}»\n"
                f"→ {chosen_bot_name}"
            )
        chosen_bot_id = self.current_participants[chosen_bot_name]
        user_message.state = UserMessageState.AWAITING_ANSWER
        local_id = self.generate_local_id()
        self.on_delivery[local_id] = (
            self.request_ids[Task.ANSWER],
            user_message,
        )
        self.enqueue_message(
            OutgoingMessage(
                text=user_message.corrected_message,
                type=MessageType.TEXT,
                command=json.dumps(
                    {
                        "self_redirect": True,
                        "bots": [chosen_bot_id],
                        "overrides": {"sent_by_human": True},
                    }
                ),
                local_id=local_id,
            )
        )

    def handle_answer(self, answer_message: Message, user_message: UserMessage):
        if user_message.state != UserMessageState.AWAITING_ANSWER:
            return  # should not happen
        if self.debug:
            self.send_debug_message(
                f"#DEBUG\nanswer from answerer:\n«{answer_message.text}»"
            )
        user_message.answer_message = answer_message
        h = [*self.last_messages, answer_message]
        completion_prompt = self.templates[Task.COMPLETION].render(history=h)
        user_message.state = UserMessageState.AWAITING_COMPLETION
        local_id = self.generate_local_id()
        self.on_delivery[local_id] = (
            self.request_ids[Task.COMPLETION],
            user_message,
        )
        user_message.state = UserMessageState.AWAITING_COMPLETION
        self.enqueue_message(
            OutgoingMessage(
                type=MessageType.TEXT,
                text=completion_prompt,
                local_id=local_id,
                command=json.dumps(
                    {
                        "self_redirect": True,
                        "bots": [self.interpreter_ids[Task.COMPLETION]],
                        "overrides": {"sent_by_human": True},
                    }
                ),
            )
        )

    def handle_completion(self, completion_message: Message, user_message: UserMessage):
        if user_message.state != UserMessageState.AWAITING_COMPLETION:
            return  # should not happen
        if self.debug:
            self.send_debug_message(
                f"#DEBUG\ncompletion from interpreter:\n«{completion_message.text}»"
            )
        user_message.completion_message = completion_message
        local_id = self.generate_local_id()
        self.enqueue_message(
            OutgoingMessage(
                type=MessageType.TEXT,
                text=user_message.complete_message,
                command=json.dumps(
                    {
                        "on_behalf_of": user_message.answer_message.sender_id,
                        "self_approve": True,
                        "overrides": {"sent_by_human": True},
                    }
                ),
                local_id=local_id,
            )
        )
        self.last_messages.append(user_message.complete_message)

    def _handle_interpreter_answer(self, message: Message) -> None:
        q = message.quoted_message_id
        if m_id := self.request_ids[Task.CORRECTION].get(q, ""):
            self.handle_correction(message, self.user_messages[m_id])
        elif m_id := self.request_ids[Task.REDIRECTION].get(q, ""):
            self.handle_redirection(message, self.user_messages[m_id])
        elif m_id := self.request_ids[Task.COMPLETION].get(q, ""):
            self.handle_completion(message, self.user_messages[m_id])
        else:
            return  # should not happen

    @overrides
    def on_receive_message(self, message: Message) -> None:
        if message.type != MessageType.TEXT:
            # only text messages are supported
            return
        if message.sender_id == self.bot_participant_id:
            # our own message - store the id
            if cb := self.on_delivery.get(message.local_id):
                d, m = cb
                d[message.id] = m.id
        elif message.sent_by_human:
            # new message from the user
            self.handle_new_message(message)
        elif message.sender_id in self.interpreter_ids.values():
            # answer from the interpreter - deal with the different types
            self._handle_interpreter_answer(message)
        elif m_id := self.request_ids[Task.ANSWER].get(message.quoted_message_id, ""):
            # answer from the answerer - handle it accordingly
            self.handle_answer(message, self.user_messages[m_id])

    @overrides
    def on_receive_state(self, event: dict[str, Any]) -> None:
        super().on_receive_state(event)
        if "participants" in event:
            self.current_participants = dict(
                map(itemgetter("name", "id"), event["participants"])
            )
            self.interpreter_ids = {
                t: self.current_participants[
                    self.settings.INTERPRETER_SETTINGS["INTERPRETER_BOT_NAMES"][
                        cast(Literal["CORRECTION", "REDIRECTION", "COMPLETION"], t.name)
                    ]
                ]
                for t in Task.__members__.values()
                if t != Task.ANSWER
            }
