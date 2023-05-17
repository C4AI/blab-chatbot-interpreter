<!--
NOTE:
- On GitHub, the diagram should render automatically.
- On PyCharm, this diagram is rendered in the preview if you enable Mermaid support
  ("Settings" > "Languages and Frameworks" > "Markdown" > check "Mermaid").
-->

```mermaid
sequenceDiagram

  actor user as user
  participant ui as UI client
  participant controller as BLAB Controller
  participant interpreter as Interpreter client
  participant llm_client as Client for LLM
  participant llm as LLM 
  participant answerer_client as Client for the<br/>chosen answerer
  participant answerer as Chosen answerer
  
  activate ui
  activate controller
  
  user-)ui:       (asks question)
  ui-)controller: user's question
  
  controller-)+interpreter: user's question

  interpreter-)controller: request to send correction prompt to LLM
  controller-)+llm_client: correction prompt
  llm_client->>+llm: correction prompt
  llm-->>-llm_client: corrected question
  llm_client--)-controller: corrected question 
  controller-)interpreter: corrected question 
  
  interpreter-)controller: request to send redirection prompt to LLM
  controller-)+llm_client: redirection prompt
  llm_client->>+llm: redirection prompt
  llm-->>-llm_client: chosen answerer number
  llm_client--)-controller: chosen answerer number
  controller-)interpreter: chosen answerer number
  
  interpreter-)controller: request to send corrected question to chosen answerer
  controller-)+answerer_client: corrected question
  answerer_client->>+answerer: corrected question
  answerer-->>-answerer_client: raw answer
  answerer_client--)-controller: raw answer
  controller-)interpreter: raw answer
  
  interpreter-)controller: request to send completion prompt to LLM
  controller-)+llm_client: completion prompt
  llm_client->>+llm: completion prompt
  llm-->>-llm_client: completed answer
  llm_client--)-controller: completed answer
  controller-)interpreter: completed answer
  
  interpreter-)-controller: request to send completed answer to user
  controller-)ui: completed answer
  ui--)user: (displays answer) 
  
  deactivate ui
  deactivate controller
  
```

The controller delivers all messages back to the corresponding senders
(which clients can use to confirm that the controller received their messages),
but this has been omitted from the diagram to save space.
