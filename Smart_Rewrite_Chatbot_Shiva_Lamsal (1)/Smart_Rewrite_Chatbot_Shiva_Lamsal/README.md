# Introduction to Artificial Intelligence (25/26)

## Student name: Shiva Lamsal
## Student number: 2413800
## Project title: Smart Rewrite Chatbot
## Link to project video recording:

## Project summary

Smart Rewrite Chatbot is a local Python NLP application that improves short English text. It supports:

- grammar correction
- paraphrasing with expanded synonym and rewrite patterns
- formal rewriting for academic or professional tone
- input validation for empty, very long or symbol-heavy text
- a lightweight Tkinter GUI
- optional offline local LLM extension using Ollama and Llama 3.2

The default version is fully local and uses no API. The optional LLM mode only works when Ollama and a local model are installed on the user's computer.

## Files

- `chatbot_base.py` - template base class, corrected so the conversation loop works
- `smart_rewrite_chatbot.py` - main chatbot class that inherits from `ChatbotBase`
- `gui_app.py` - Tkinter graphical interface
- `run_chatbot.py` - run file for GUI or CLI
- `requirements.txt` - notes about dependencies


## How to run the GUI

```bash
python run_chatbot.py
```

Or directly:

```bash
python gui_app.py
```

## How to run the terminal version

```bash
python run_chatbot.py --cli
```

Example CLI inputs:

```text
grammar: i dont know teh answer becouse it is very hard
paraphrase: This project helps students improve English writing because it is simple.
formal: i wanna ask about the meeting because i cant come today
smart: i want to visit europe because i have lots of money
llm: rewrite this sentence in a formal style
quit
```

## How to run tests

```bash
python test_smart_rewrite.py
```

## Optional local LLM extension

1. Install Ollama from https://ollama.com/
2. Pull a small local model:

```bash
ollama pull llama3.2:3b
```

3. Run the app and select `Local LLM - Ollama Llama 3.2` in the GUI.

If Ollama is not installed, the app does not crash. It shows a message and uses the rule-based fallback.
