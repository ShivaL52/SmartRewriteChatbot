"""Tkinter GUI for Smart Rewrite Chatbot.

The interface is designed to look like a modern chat application while staying
lightweight enough for demo. It uses only Python's standard library, so it will
run without external API keys.
"""

from __future__ import annotations

import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

from smart_rewrite_chatbot import SmartRewriteChatbot


class SmartRewriteGUI:

    DARK = {
        "root": "#0b1224",
        "main": "#0f172a",
        "sidebar": "#111b33",
        "sidebar2": "#1c2947",
        "chat": "#0a1020",
        "entry": "#17233d",
        "border": "#2d3b59",
        "text": "#f8fafc",
        "muted": "#cbd5e1",
        "soft": "#94a3b8",
        "accent": "#a78bfa",
        "accent_dark": "#7c3aed",
        "user": "#3b82f6",
        "bot": "#263650",
        "success": "#86efac",
        "danger": "#7f1d1d",
    }

    LIGHT = {
        "root": "#eef2ff",
        "main": "#f8fafc",
        "sidebar": "#edf2ff",
        "sidebar2": "#dbeafe",
        "chat": "#ffffff",
        "entry": "#ffffff",
        "border": "#c7d2fe",
        "text": "#0f172a",
        "muted": "#334155",
        "soft": "#64748b",
        "accent": "#8b5cf6",
        "accent_dark": "#6d28d9",
        "user": "#2563eb",
        "bot": "#f1f5f9",
        "success": "#15803d",
        "danger": "#fee2e2",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Smart Rewrite Chatbot")
        self.root.geometry("1180x720")
        self.root.minsize(980, 620)
        self.root.configure(bg=self.DARK["root"])

        self.chatbot = SmartRewriteChatbot()
        self.dark_mode = tk.BooleanVar(value=True)
        self.awaiting_mode: str | None = None
        self.selected_nav = "Chat"
        self.messages: list[dict[str, str]] = []
        self.nav_buttons: dict[str, tk.Button] = {}
        self.last_bot_output = ""

        self._build_widgets()
        self._bind_events()
        self.root.after(150, self._welcome)

    @property
    def c(self) -> dict[str, str]:
        return self.DARK if self.dark_mode.get() else self.LIGHT

    def _build_widgets(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

        self.root.configure(bg=self.c["root"])

        shell = tk.Frame(self.root, bg=self.c["root"])
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            shell,
            bg=self.c["sidebar"],
            width=250,
            highlightthickness=1,
            highlightbackground=self.c["border"],
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(
            shell,
            bg=self.c["main"],
            highlightthickness=1,
            highlightbackground=self.c["border"],
        )
        self.main.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_main()
        self._repaint_messages()

    def _build_sidebar(self) -> None:
        tk.Label(
            self.sidebar,
            text="🤖",
            font=("Segoe UI Emoji", 42),
            bg=self.c["sidebar2"],
            fg=self.c["text"],
            width=4,
            height=2,
        ).pack(pady=(24, 14))

        tk.Label(
            self.sidebar,
            text="Smart Rewrite\nChatbot",
            font=("Segoe UI", 20, "bold"),
            bg=self.c["sidebar"],
            fg=self.c["text"],
            justify="center",
        ).pack()

        tk.Label(
            self.sidebar,
            text="Your intelligent writing assistant",
            font=("Segoe UI", 9, "bold"),
            bg=self.c["sidebar"],
            fg=self.c["muted"],
        ).pack(pady=(8, 20))

        nav_items = [
            ("Chat", "💬", self.activate_chat),
            ("Grammar Check", "☑", lambda: self.activate_mode("grammar")),
            ("Paraphrase", "✍", lambda: self.activate_mode("paraphrase")),
            ("Formal Rewrite", "📝", lambda: self.activate_mode("formal")),
            ("Smart Rewrite", "✨", lambda: self.activate_mode("smart")),
            ("LLM Rewrite", "🧠", lambda: self.activate_mode("llm")),
            ("Help", "?", self.show_help),
            ("About", "i", self.show_about),
        ]

        self.nav_buttons = {}
        for title, icon, command in nav_items:
            button = tk.Button(
                self.sidebar,
                text=f"  {icon}   {title}",
                anchor="w",
                font=("Segoe UI", 10, "bold"),
                bd=0,
                relief="flat",
                cursor="hand2",
                padx=18,
                pady=10,
                command=command,
            )
            button.pack(fill="x", padx=16, pady=3)
            self.nav_buttons[title] = button

        self._refresh_nav_buttons()

        feature_card = tk.Frame(self.sidebar, bg=self.c["sidebar2"], padx=16, pady=12)
        feature_card.pack(fill="x", padx=16, pady=(20, 10))

        tk.Label(
            feature_card,
            text="Features",
            font=("Segoe UI", 11, "bold"),
            bg=self.c["sidebar2"],
            fg=self.c["accent"],
        ).pack(anchor="w", pady=(0, 4))

        for text in [
            "Grammar Correction",
            "Sentence Paraphrasing",
            "Formal Rewriting",
            "Optional Llama 3.2",
            "Input Validation",
            "Copy and Paste Output",
        ]:
            tk.Label(
                feature_card,
                text=f"✓  {text}",
                font=("Segoe UI", 8, "bold"),
                bg=self.c["sidebar2"],
                fg=self.c["text"],
            ).pack(anchor="w", pady=2)

        toggle_frame = tk.Frame(self.sidebar, bg=self.c["sidebar2"], padx=12, pady=8)
        toggle_frame.pack(fill="x", padx=16, pady=(0, 14), side="bottom")

        tk.Label(
            toggle_frame,
            text="☾  Dark Mode",
            font=("Segoe UI", 9, "bold"),
            bg=self.c["sidebar2"],
            fg=self.c["text"],
        ).pack(side="left")

        tk.Checkbutton(
            toggle_frame,
            variable=self.dark_mode,
            command=self._build_widgets,
            bg=self.c["sidebar2"],
            activebackground=self.c["sidebar2"],
            selectcolor=self.c["accent"],
        ).pack(side="right")

    def _build_main(self) -> None:
        header = tk.Frame(self.main, bg=self.c["main"], padx=28, pady=20)
        header.pack(fill="x")

        title_block = tk.Frame(header, bg=self.c["main"])
        title_block.pack(side="left", fill="x", expand=True)

        tk.Label(
            title_block,
            text="Smart Rewrite Chatbot",
            font=("Segoe UI", 24, "bold"),
            bg=self.c["main"],
            fg=self.c["text"],
        ).pack(anchor="w")

        tk.Label(
            title_block,
            text="I can help you with grammar checking, paraphrasing and formal rewriting.",
            font=("Segoe UI", 10, "bold"),
            bg=self.c["main"],
            fg=self.c["muted"],
        ).pack(anchor="w", pady=(6, 0))

        tk.Button(
            header,
            text="🗑  Clear Chat",
            font=("Segoe UI", 9, "bold"),
            bg=self.c["danger"],
            fg=("#fecaca" if self.dark_mode.get() else "#991b1b"),
            activebackground="#991b1b",
            activeforeground="white",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
            command=self.clear_chat,
        ).pack(side="right")

        chat_holder = tk.Frame(self.main, bg=self.c["main"], padx=28)
        chat_holder.pack(fill="both", expand=True)

        self.chat_text = tk.Text(
            chat_holder,
            bg=self.c["chat"],
            fg=self.c["text"],
            wrap="word",
            state="disabled",
            bd=0,
            relief="flat",
            padx=18,
            pady=18,
            font=("Segoe UI", 11),
            insertbackground=self.c["text"],
            highlightthickness=1,
            highlightbackground=self.c["border"],
        )

        self.scrollbar = tk.Scrollbar(chat_holder, command=self.chat_text.yview)
        self.chat_text.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.chat_text.pack(side="left", fill="both", expand=True)
        self._configure_text_tags()

        input_area = tk.Frame(self.main, bg=self.c["main"], padx=28, pady=14)
        input_area.pack(fill="x")

        self.entry = tk.Entry(
            input_area,
            font=("Segoe UI", 11),
            bg=self.c["entry"],
            fg=self.c["text"],
            insertbackground=self.c["text"],
            relief="flat",
            bd=0,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=14, padx=(0, 8))
        self.entry.insert(0, "Type your message here...")
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)
        self.entry.bind("<Control-v>", self.paste_from_clipboard)
        self.entry.bind("<Control-V>", self.paste_from_clipboard)

        tk.Button(
            input_area,
            text="📋  Paste",
            font=("Segoe UI", 10, "bold"),
            bg=self.c["sidebar2"],
            fg=self.c["text"],
            activebackground=self.c["border"],
            activeforeground=self.c["text"],
            bd=0,
            padx=16,
            pady=13,
            cursor="hand2",
            command=self.paste_from_clipboard,
        ).pack(side="right", padx=(0, 8))

        tk.Button(
            input_area,
            text="⧉  Copy Output",
            font=("Segoe UI", 10, "bold"),
            bg=self.c["sidebar2"],
            fg=self.c["text"],
            activebackground=self.c["border"],
            activeforeground=self.c["text"],
            bd=0,
            padx=16,
            pady=13,
            cursor="hand2",
            command=self.copy_last_output,
        ).pack(side="right", padx=(0, 8))

        tk.Button(
            input_area,
            text="➤  Send",
            font=("Segoe UI", 10, "bold"),
            bg=self.c["accent"],
            fg="white",
            activebackground=self.c["accent_dark"],
            activeforeground="white",
            bd=0,
            padx=26,
            pady=13,
            cursor="hand2",
            command=self.send_message,
        ).pack(side="right")

        footer = tk.Frame(self.main, bg=self.c["main"], pady=8)
        footer.pack(fill="x")

        ollama_status = "Ollama Ready" if shutil.which("ollama") else "Ollama Optional"
        tk.Label(
            footer,
            text=f"🧠  Built with NLP and Python   |   Offline   |   No API Used   |   {ollama_status}",
            font=("Segoe UI", 8, "bold"),
            bg=self.c["main"],
            fg=self.c["muted"],
        ).pack()

    def _configure_text_tags(self) -> None:
        self.chat_text.tag_configure(
            "bot_name",
            foreground=self.c["muted"],
            font=("Segoe UI", 8, "bold"),
            lmargin1=8,
            lmargin2=8,
            spacing1=8,
        )
        self.chat_text.tag_configure(
            "bot_bubble",
            foreground=self.c["text"],
            background=self.c["bot"],
            lmargin1=8,
            lmargin2=8,
            rmargin=220,
            spacing3=12,
            font=("Segoe UI", 11),
        )
        self.chat_text.tag_configure(
            "bot_title",
            foreground=self.c["success"],
            background=self.c["bot"],
            lmargin1=8,
            lmargin2=8,
            rmargin=220,
            font=("Segoe UI", 11, "bold"),
        )
        self.chat_text.tag_configure(
            "user_name",
            foreground=self.c["muted"],
            justify="right",
            font=("Segoe UI", 8, "bold"),
            lmargin1=220,
            lmargin2=220,
            rmargin=8,
            spacing1=8,
        )
        self.chat_text.tag_configure(
            "user_bubble",
            foreground="white",
            background=self.c["user"],
            justify="right",
            lmargin1=220,
            lmargin2=220,
            rmargin=8,
            spacing3=12,
            font=("Segoe UI", 11, "bold"),
        )

    def _bind_events(self) -> None:
        self.root.bind("<Return>", lambda event: self.send_message())
        self.root.bind("<Control-l>", lambda event: self.clear_chat())
        self.root.bind("<Control-L>", lambda event: self.clear_chat())
        self.root.bind("<Control-Shift-c>", self.copy_last_output)
        self.root.bind("<Control-Shift-C>", self.copy_last_output)

    def _welcome(self) -> None:
        if not self.messages:
            self.add_message("bot", "Hello! 👋 How can I help you today?")
            self.add_message("bot", "Try: Grammar correction: i dont know teh answer becouse it is very hard")

    def _refresh_nav_buttons(self) -> None:
        for title, button in self.nav_buttons.items():
            active = title == self.selected_nav
            button.configure(
                bg=(self.c["accent"] if active else self.c["sidebar"]),
                fg=("white" if active else self.c["text"]),
                activebackground=self.c["sidebar2"],
                activeforeground=self.c["text"],
            )

    def _repaint_messages(self) -> None:
        if not hasattr(self, "chat_text"):
            return

        saved = list(self.messages)
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self.messages = []

        for message in saved:
            self.add_message(message["sender"], message["text"], message.get("title", ""))

    def add_message(self, sender: str, text: str, title: str = "") -> None:
        self.messages.append({"sender": sender, "text": text, "title": title})
        time_text = datetime.now().strftime("%I:%M %p").lstrip("0")

        self.chat_text.configure(state="normal")

        if sender == "user":
            self.chat_text.insert("end", f"You   {time_text}\n", "user_name")
            self.chat_text.insert("end", f"  {text}  \n\n", "user_bubble")
        else:
            self.chat_text.insert("end", f"🤖  Bot   {time_text}\n", "bot_name")
            if title:
                self.chat_text.insert("end", f"  {title}\n", "bot_title")
            self.chat_text.insert("end", f"  {text}  \n\n", "bot_bubble")

        self.chat_text.configure(state="disabled")
        self.chat_text.see("end")

    def send_message(self) -> None:
        text = self.entry.get().strip()

        if not text or text == "Type your message here...":
            return

        self.entry.delete(0, "end")
        self.add_message("user", text)

        lower = text.lower().strip()

        if lower in {"clear", "clear chat", "reset"}:
            self.clear_chat()
            return

        if lower in {"help", "what can you do", "commands"}:
            self.show_help()
            return

        if lower in {"about", "about app"}:
            self.show_about()
            return

        if self.chatbot.looks_like_terminal_command(text):
            output = self.chatbot.terminal_command_message(text)
            self.last_bot_output = output
            self.add_message("bot", output, "Command detected:")
            return

        if self.awaiting_mode:
            mode = self.awaiting_mode
            self.awaiting_mode = None
            self.selected_nav = "Chat"
            self._refresh_nav_buttons()
            self._process_rewrite(text, mode)
            return

        detected = self._detect_request(lower)
        if detected:
            self.activate_mode(detected)
            return

        self._process_rewrite(text, "smart")

    def _process_rewrite(self, text: str, mode: str) -> None:
        result = self.chatbot.rewrite(text, mode)
        output = result.output

        if result.warnings:
            output = "\n".join(f"⚠ {warning}" for warning in result.warnings) + "\n\n" + output

        self.last_bot_output = output

        title_map = {
            "grammar": "Corrected Sentence:",
            "paraphrase": "Paraphrased Sentence:",
            "formal": "Formal Rewrite:",
            "llm": "Local LLM Rewrite:",
            "smart": "Smart Rewrite Output:",
            "system": "Command Detected:",
        }

        self.add_message("bot", output, title_map.get(result.mode, "Output:"))

    def copy_last_output(self, event=None):
        if not self.last_bot_output.strip():
            messagebox.showinfo("Copy Output", "There is no chatbot output to copy yet.")
            return "break"

        self.root.clipboard_clear()
        self.root.clipboard_append(self.last_bot_output)
        self.root.update()
        messagebox.showinfo("Copy Output", "Latest chatbot output copied to clipboard.")
        return "break"

    def paste_from_clipboard(self, event=None):
        try:
            clipboard_text = self.root.clipboard_get()
        except tk.TclError:
            messagebox.showinfo("Paste", "Clipboard is empty or does not contain text.")
            return "break"

        clipboard_text = clipboard_text.strip()

        if not clipboard_text:
            messagebox.showinfo("Paste", "Clipboard is empty.")
            return "break"

        if self.entry.get() == "Type your message here...":
            self.entry.delete(0, "end")

        current_text = self.entry.get().strip()

        if current_text:
            self.entry.insert("end", " " + clipboard_text)
        else:
            self.entry.insert(0, clipboard_text)

        self.entry.focus_set()
        return "break"

    @staticmethod
    def _detect_request(text: str) -> str | None:
        if any(
            word in text
            for word in [
                "grammar",
                "check grammar",
                "correct",
                "fix my sentence",
                "sentence mistake",
            ]
        ):
            return "grammar"

        if any(word in text for word in ["formal", "professional", "academic tone"]):
            return "formal"

        if any(word in text for word in ["llm", "llama", "use model", "local model"]):
            return "llm"

        if any(word in text for word in ["paraphrase", "rewrite", "reword", "change my sentence"]):
            return "paraphrase"

        return None

    def activate_chat(self) -> None:
        self.selected_nav = "Chat"
        self.awaiting_mode = None
        self._refresh_nav_buttons()
        self.add_message(
            "bot",
            "Chat mode is active. Type any sentence and I will return corrected, paraphrased and formal versions.",
        )

    def activate_mode(self, mode: str) -> None:
        self.awaiting_mode = mode
        nav_name = {
            "grammar": "Grammar Check",
            "paraphrase": "Paraphrase",
            "formal": "Formal Rewrite",
            "smart": "Smart Rewrite",
            "llm": "LLM Rewrite",
        }.get(mode, "Chat")

        self.selected_nav = nav_name
        self._refresh_nav_buttons()

        prompts = {
            "grammar": "Sure! Please type the sentence you want me to correct.",
            "paraphrase": "Sure! Please type the sentence you want me to paraphrase.",
            "formal": "Sure! Please type the casual sentence you want me to make formal.",
            "smart": "Sure! Please type the sentence and I will return grammar, paraphrase and formal versions.",
            "llm": (
                "Sure! Please type. "
                "If Ollama + Llama 3.2 is installed, "
                "I will use it; otherwise I will use the offline fallback."
            ),
        }

        self.add_message("bot", prompts.get(mode, "Please type your sentence."))

    def show_help(self) -> None:
        self.selected_nav = "Help"
        self.awaiting_mode = None
        self._refresh_nav_buttons()
        self.add_message(
            "bot",
            "Use the left menu or type normally.\n\n"
            "Examples:\n"
            "Grammar correction: i dont know teh answer becouse it is very hard\n"
            "Paraphrase: This project helps students improve English writing because it is simple.\n"
            "Formal rewrite: i wanna ask about the meeting because i cant come today\n"
            "Smart rewrite: i want to visit europe because i have lots of money\n"
            "LLM rewrite: i wanna submit this report becouse my english sentence is not good and it need to sound more professional\n\n"
            "Important: run commands such as python run_chatbot.py, ollama --version and ollama list in Command Prompt, not inside this chatbot input box.\n\n"
            "Buttons: Paste inserts clipboard text into the input box. Copy Output copies the latest chatbot answer.",
            "Help:",
        )

    def show_about(self) -> None:
        self.selected_nav = "About"
        self.awaiting_mode = None
        self._refresh_nav_buttons()
        self.add_message(
            "bot",
            "Smart Rewrite Chatbot is a local Python NLP application. It uses rule-based grammar correction, pattern-based paraphrasing, formal rewriting and optional local Llama 3.2 support through Ollama. No external API key is required.",
            "About:",
        )

    def clear_chat(self) -> None:
        self.messages.clear()
        self.last_bot_output = ""
        self.chat_text.configure(state="normal")
        self.chat_text.delete("1.0", "end")
        self.chat_text.configure(state="disabled")
        self.awaiting_mode = None
        self.selected_nav = "Chat"
        self._refresh_nav_buttons()
        self.add_message("bot", "Chat cleared. How can I help you now?")

    def _clear_placeholder(self, event=None) -> None:
        if self.entry.get() == "Type your message here...":
            self.entry.delete(0, "end")

    def _restore_placeholder(self, event=None) -> None:
        if not self.entry.get().strip():
            self.entry.insert(0, "Type your message here...")


def launch_gui() -> None:
    root = tk.Tk()
    try:
        root.iconbitmap(default="")
    except tk.TclError:
        pass
    SmartRewriteGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
