"""Run file for Smart Rewrite Chatbot.

Default mode launches the Tkinter GUI.
Use --cli for terminal mode.
"""

import sys

from smart_rewrite_chatbot import SmartRewriteChatbot


def run_cli() -> None:
    chatbot = SmartRewriteChatbot()
    chatbot.greeting()

    print("Type a command such as 'grammar: i dont know teh answer' or 'quit'.")
    print("Modes: grammar, paraphrase, formal, smart, llm")

    response = "How can I help you rewrite your text?"

    while chatbot.conversation_is_active():
        try:
            print(response)
            user_input = input("> ")
            processed = chatbot.process_input(user_input)
            response = chatbot.generate_response(processed)

        except KeyboardInterrupt:
            print("\nChatbot stopped safely.")
            break

    chatbot.farewell()


def run_gui() -> None:
    try:
        from gui_app import launch_gui

        launch_gui()

    except KeyboardInterrupt:
        print("\nGUI closed safely.")

    except Exception as error:
        print("The GUI could not be launched.")
        print(f"Reason: {error}")
        print("\nTry terminal mode instead:")
        print("python run_chatbot.py --cli")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()
