from enum import IntEnum, auto, Enum


class UserMessageState(IntEnum):
    NEW = auto()
    AWAITING_CORRECTION = auto()
    AWAITING_REDIRECTION = auto()
    AWAITING_ANSWER = auto()
    AWAITING_COMPLETION = auto()
    DONE = auto()


class Task(Enum):
    CORRECTION = "correction"
    REDIRECTION = "redirection"
    ANSWER = "answer"
    COMPLETION = "completion"
