from typing import Protocol, TypedDict, runtime_checkable

from blab_chatbot_bot_client.settings_format import BlabBotClientSettings


class InterpreterTemplatePathSettings(TypedDict):
    CORRECTION: str
    REDIRECTION: str
    COMPLETION: str


class InterpreterSettings(TypedDict):
    INTERPRETER_BOT_NAME: str
    TEMPLATE_FILE_NAMES: InterpreterTemplatePathSettings
    HISTORY_SIZE: int
    ANSWERERS: dict[str, str]
    DEBUG: bool


@runtime_checkable
class BlabInterpreterClientSettings(BlabBotClientSettings, Protocol):
    INTERPRETER_SETTINGS: InterpreterSettings
