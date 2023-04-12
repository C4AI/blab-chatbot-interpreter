# BLAB Chatbot Client: Interpreter

This repository contains an implementation of a bot that acts a
conversation manager and uses an interpreter to perform three tasks:

- **correction**: remove errors (grammar, punctuation, capitalization, etc.) and produce a self-contained sentence
  by replacing external references (implicit subjects, pronouns, etc.) considering the message history;
- **redirection**: choose the most appropriate bot to answer each question or detect that none of them can deal with the
  topic;
- **completion**: generate a complete sentence containing the answerer output.

This bot should be used with [BLAB Controller](../../../blab-controller).

### Installation

- Install a version of
  [Python](https://www.python.org/downloads/release/python-3100/) ≥ 3.10.

- Create the prompt template files for correction, redirection and completion.
  They should be [Jinja](https://palletsprojects.com/p/jinja/) templates that produce plain text files.
  Examples:
  - Correction and completion prompts:
    ```
    Consider the following message history:
    {% for message in history: -%}
        {% if message.sent_by_human -%}
            USER
        {%- else -%}
            BOT
        {%- endif -%}
        : «{{ message.text }}»
    {% endfor %}
  
    Rewrite the last message [...].
    ```

  - Redirection prompt:
    ```
    Consider the following question-answering bots:

    {% for description in bots.values(): -%}
        {{ loop.index }}: «{{ description -}}»
    {% endfor %}
  
    Which one should is best suited to answer the following question?
    «{{ user_message }}»
  
    If the topic is unrelated or the message is wrong, answer 0. Send ONLY the number, without text.
    ```

- Follow [these installation instructions](../../../blab-chatbot-bot-client/blob/main/INSTALL.md)
  using [*settings_interpreter_template.py*](settings_interpreter_template.py) as a template.

- Follow [these instructions](../../../blab-chatbot-bot-client/blob/main/RUN.md) to execute the
  program.

**IMPORTANT:** Make sure that the interpreter bots do not use the message history on their own, because the previous
messages are
included in the prompt. For example, if
[the interpreter bot is uses one of the OpenAI bots](../../../blab-chatbot-openai/), set `HISTORY_SIZE` to 1.
