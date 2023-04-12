"""This module contains settings for the Interpreter bot client."""

# fmt: off

from __future__ import annotations

from blab_chatbot_bot_client.settings_format import BlabWebSocketConnectionSettings

from blab_chatbot_interpreter.interpreter_settings_format import InterpreterSettings

BLAB_CONNECTION_SETTINGS: BlabWebSocketConnectionSettings = {

    # address of the local HTTP server that the controller will connect to
    # (it should be "127.0.0.1" to accept only local connections from the controller):
    "BOT_HTTP_SERVER_HOSTNAME": "127.0.0.1",

    # port of the aforementioned server (any valid port):
    "BOT_HTTP_SERVER_PORT": 25229,

    # BLAB Controller address for WebSocket connections (it starts with ws:// or wss://):
    "BLAB_CONTROLLER_WS_URL": "ws://localhost:8000",

}

INTERPRETER_SETTINGS: InterpreterSettings = {

    # name of the interpreter bots (exactly as defined in the controller settings;
    # the same bot may perform multiple interpretation tasks):
    "INTERPRETER_BOT_NAMES": {
        "CORRECTION": "Interpreter bot 1",
        "REDIRECTION": "Interpreter bot 2",
        "COMPLETION": "Interpreter bot 3",
    },

    # answerer bots
    # (the keys must be the bot names exactly as defined in the controller settings;
    #  the values must be a short description of what each bot does)
    "ANSWERERS": {
        "First bot": "A bot that answers questions about subjects A, B and C.",
        "Second bot": "An answerer system that produces answers to questions about the topics X and Y, but not Z.",
    },

    # paths to template files (see README.md for instructions)
    # (the paths can be either absolute or relative to the root directory of this repository)
    "TEMPLATE_FILE_NAMES": {
        "CORRECTION": "path/to/the/correction-prompt.txt",
        "REDIRECTION": "path/to/the/redirection-prompt.txt",
        "COMPLETION": "path/to/the/completion-prompt.txt",
    },

    # number of messages that the interpreter will receive as context
    "HISTORY_SIZE": 10,

    # whether the internal communication with the interpreter bot and the answerers should be sent as messages
    "DEBUG": False,
}
