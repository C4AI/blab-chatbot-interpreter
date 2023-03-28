from logging import getLogger
from sys import argv

from blab_chatbot_bot_client.cli import BlabBotClientArgParser

from blab_chatbot_interpreter.conversation_interpreter import (
    InterpreterWebSocketBotClientConversation,
)

BlabBotClientArgParser(InterpreterWebSocketBotClientConversation).parse_and_run(
    argv[1:]
)
