"""Smart Rewrite Chatbot core logic.

The chatbot inherits from ChatbotBase, works offline using rule-based NLP,
and can optionally use a local Ollama Llama 3.2 model when it is installed.
"""

from __future__ import annotations

import random
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from chatbot_base import ChatbotBase


@dataclass
class RewriteResult:
    """Structured response returned by the chatbot."""

    mode: str
    original: str
    output: str
    warnings: List[str]


class SmartRewriteChatbot(ChatbotBase):
    """Local writing assistant for grammar correction, paraphrasing and rewriting."""

    MAX_CHARACTERS = 1500
    MAX_WORDS = 240
    MAX_SENTENCE_WORDS = 50

    TERMINAL_COMMAND_STARTS = (
        "python ",
        "py ",
        "pip ",
        "ollama ",
        "cd ",
        "dir",
        "cls",
        "clear",
        "where ",
        "set ",
        "echo ",
        "git ",
        "code ",
        "notepad ",
        "powershell",
        "cmd ",
    )

    def __init__(self, name: str = "Smart Rewrite Chatbot"):
        super().__init__(name=name)

        if not callable(getattr(self, "conversation_is_active", None)):
            try:
                delattr(self, "conversation_is_active")
            except AttributeError:
                pass

        self._conversation_active = True
        self.random = random.Random()
        self.spelling_and_phrase_rules = self._build_spelling_rules()
        self.formal_phrase_rules = self._build_formal_rules()
        self.synonym_groups = self._build_synonym_groups()
        self.structure_patterns = self._build_structure_patterns()

    # CLI interface required by the base class
    def stop_conversation(self) -> None:
        self._conversation_active = False

    def conversation_is_active(self) -> bool:
        return self._conversation_active

    def process_input(self, user_input):
        text = str(user_input).strip()

        if text.lower() in {"quit", "exit", "bye"}:
            self.stop_conversation()
            return {"mode": "quit", "text": text}

        if self.looks_like_terminal_command(text):
            return {"mode": "system", "text": text}

        if ":" in text:
            possible_mode, possible_text = text.split(":", 1)
            mode = self.normalise_mode(possible_mode)
            return {"mode": mode, "text": possible_text.strip()}

        return {"mode": "smart", "text": text}

    def generate_response(self, processed_input):
        mode = processed_input.get("mode", "smart")

        if mode == "quit":
            return "Goodbye."

        if mode == "system":
            return self.terminal_command_message(processed_input.get("text", ""))

        result = self.rewrite(processed_input.get("text", ""), mode)
        warning_text = "\n".join(f"Warning: {warning}" for warning in result.warnings)

        if warning_text:
            return f"{warning_text}\n\n{result.output}"

        return result.output

    def rewrite(self, text: str, mode: str = "smart") -> RewriteResult:
        """Main method used by GUI and CLI."""
        mode = self.normalise_mode(mode)
        original_text = text or ""

        if self.looks_like_terminal_command(original_text):
            return RewriteResult(
                "system",
                original_text,
                self.terminal_command_message(original_text),
                [],
            )

        warnings, clean_text = self.validate_and_prepare(original_text)

        if not clean_text:
            return RewriteResult(
                mode,
                original_text,
                "Please enter a sentence or short paragraph to rewrite.",
                warnings,
            )

        if mode == "grammar":
            output = self.correct_grammar(clean_text)

        elif mode == "paraphrase":
            output = self.paraphrase(clean_text)

        elif mode == "formal":
            output = self.formal_rewrite(clean_text)

        elif mode == "llm":
            output = self.local_llm_rewrite(clean_text)

        else:
            corrected = self.correct_grammar(clean_text)
            paraphrased = self.paraphrase(corrected)
            formal = self.formal_rewrite(corrected)

            output = (
                "Corrected version:\n"
                f"{corrected}\n\n"
                "Paraphrased version:\n"
                f"{paraphrased}\n\n"
                "Formal version:\n"
                f"{formal}"
            )

        return RewriteResult(mode, original_text, output, warnings)

    @staticmethod
    def normalise_mode(mode: str) -> str:
        value = (mode or "smart").strip().lower()

        if "llm" in value or "ollama" in value or "llama" in value or "model" in value:
            return "llm"
        if "formal" in value or "professional" in value or "academic" in value:
            return "formal"
        if "grammar" in value or "correct" in value or "fix" in value:
            return "grammar"
        if "smart" in value:
            return "smart"
        if "para" in value or "rewrite" in value or "reword" in value:
            return "paraphrase"

        return "smart"

    @classmethod
    def looks_like_terminal_command(cls, text: str) -> bool:
        value = (text or "").strip().lower()

        if not value:
            return False

        if value.startswith(cls.TERMINAL_COMMAND_STARTS):
            return True

        return bool(
            re.search(
                r"\b(run_chatbot|\.py|llama3\.2:3b)\b",
                value,
            )
        )

    @staticmethod
    def terminal_command_message(text: str) -> str:
        command = text.strip()

        if command.lower().startswith("ollama"):
            return (
                "That is a Windows Command Prompt or PowerShell command, not a sentence for rewriting.\n\n"
                "Please close or leave the chatbot first, open a fresh Command Prompt, then run:\n"
                "ollama --version\n"
                "ollama list\n\n"
                "If Ollama is not installed, install it first, then reopen Command Prompt."
            )

        return (
            "That looks like a terminal command, not a writing sentence.\n\n"
            "To run this command, type it in Command Prompt or PowerShell, not inside the chatbot:\n"
            f"{command}"
        )

    # Input validation
    def validate_and_prepare(self, text: str) -> Tuple[List[str], str]:
        warnings: List[str] = []
        clean_text = re.sub(r"\s+", " ", (text or "").strip())

        if not clean_text:
            return warnings, ""

        if len(clean_text) > self.MAX_CHARACTERS:
            warnings.append(
                f"Input was longer than {self.MAX_CHARACTERS} characters, so it was shortened for a stable demo."
            )
            clean_text = clean_text[: self.MAX_CHARACTERS].rsplit(" ", 1)[0]

        words = clean_text.split()

        if len(words) > self.MAX_WORDS:
            warnings.append(
                f"Input had more than {self.MAX_WORDS} words, so only the first {self.MAX_WORDS} words were processed."
            )
            clean_text = " ".join(words[: self.MAX_WORDS])

        if any(
            len(sentence.split()) > self.MAX_SENTENCE_WORDS
            for sentence in self.split_sentences(clean_text)
        ):
            warnings.append(
                "One or more sentences are very long; shorter sentences give clearer rewriting results."
            )

        if re.search(r"[^A-Za-z0-9\s.,!?;:'\"()\-]", clean_text):
            warnings.append("Some unusual symbols were removed to keep the rewrite readable.")
            clean_text = re.sub(r"[^A-Za-z0-9\s.,!?;:'\"()\-]", "", clean_text)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return warnings, clean_text

    # Grammar correction
    def correct_grammar(self, text: str) -> str:
        return " ".join(
            self._correct_sentence(sentence)
            for sentence in self.split_sentences(text)
        )

    def _correct_sentence(self, sentence: str) -> str:
        text = f" {sentence.strip()} "

        for pattern, replacement in self.spelling_and_phrase_rules:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        grammar_rules = [
            (r"\bI\s+is\b", "I am"),
            (r"\bI\s+are\b", "I am"),
            (r"\bI\s+has\b", "I have"),
            (r"\bhe\s+go\b", "he goes"),
            (r"\bshe\s+go\b", "she goes"),
            (r"\bit\s+go\b", "it goes"),
            (r"\bhe\s+have\b", "he has"),
            (r"\bshe\s+have\b", "she has"),
            (r"\bit\s+have\b", "it has"),
            (r"\bhe\s+do\s+not\b", "he does not"),
            (r"\bshe\s+do\s+not\b", "she does not"),
            (r"\bit\s+do\s+not\b", "it does not"),
            (r"\bthis\s+are\b", "this is"),
            (r"\bthese\s+is\b", "these are"),
            (r"\bmore\s+better\b", "better"),
            (r"\bvery\s+unique\b", "unique"),
            (r"\ba\s+apple\b", "an apple"),
            (r"\ba\s+idea\b", "an idea"),
            (r"\ban\s+university\b", "a university"),
            (r"\bshould\s+of\b", "should have"),
            (r"\bcould\s+of\b", "could have"),
            (r"\bwould\s+of\b", "would have"),
            (r"\bit\s+need\b", "it needs"),
            (r"\bit\s+sound\b", "it sounds"),
            (
                r"\bmy\s+english\s+sentence\s+is\s+not\s+good\b",
                "my English writing is not very good",
            ),
        ]

        for pattern, replacement in grammar_rules:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        text = self._normalise_spacing(text.strip())
        text = self._capitalise_special_words(text)
        text = self._ensure_sentence_punctuation(text)

        return text[0].upper() + text[1:] if text else text

    # Paraphrasing
    def paraphrase(self, text: str) -> str:
        return " ".join(
            self._paraphrase_sentence(sentence)
            for sentence in self.split_sentences(text)
        )

    def _paraphrase_sentence(self, sentence: str) -> str:
        rewritten = self._correct_sentence(sentence)

        for pattern, templates in self.structure_patterns:
            match = re.search(pattern, rewritten, flags=re.IGNORECASE)

            if match:
                template = self.random.choice(templates)
                groups = [part.strip().rstrip(".") for part in match.groups()]

                try:
                    rewritten = template.format(*groups)
                    break
                except IndexError:
                    pass

        replacements_done = 0
        keys = list(self.synonym_groups.keys())
        self.random.shuffle(keys)

        for target in keys:
            if replacements_done >= 3:
                break

            if re.search(rf"\b{re.escape(target)}\b", rewritten, flags=re.IGNORECASE):
                replacement = self.random.choice(self.synonym_groups[target])
                rewritten = re.sub(
                    rf"\b{re.escape(target)}\b",
                    replacement,
                    rewritten,
                    count=1,
                    flags=re.IGNORECASE,
                )
                replacements_done += 1

        rewritten = self._normalise_spacing(rewritten)
        rewritten = self._capitalise_special_words(rewritten)
        rewritten = self._ensure_sentence_punctuation(rewritten)

        return rewritten[0].upper() + rewritten[1:] if rewritten else rewritten

    # Formal rewriting
    def formal_rewrite(self, text: str) -> str:
        rewritten = self.correct_grammar(text)

        for pattern, replacement in self.formal_phrase_rules:
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

        formal_openers = [
            (r"^I think\b", "It can be argued that"),
            (r"^I believe\b", "It is reasonable to suggest that"),
            (r"^In my opinion\b", "From this perspective"),
            (r"^This is about\b", "This concerns"),
        ]

        for pattern, replacement in formal_openers:
            rewritten = re.sub(pattern, replacement, rewritten, flags=re.IGNORECASE)

        rewritten = self._normalise_spacing(rewritten)
        rewritten = self._capitalise_special_words(rewritten)
        rewritten = self._ensure_sentence_punctuation(rewritten)

        return rewritten[0].upper() + rewritten[1:] if rewritten else rewritten

    # Optional local LLM through Ollama
    def local_llm_rewrite(self, text: str) -> str:
        if self._looks_like_llm_instruction(text):
            return (
                "Please type only the sentence you want me to rewrite, not the internal LLM instruction prompt.\n\n"
                "Example sentence:\n"
                "i wanna submit this report becouse my english sentence is not good and it need to sound more professional"
            )

        if not shutil.which("ollama"):
            return (
                "Local LLM mode is optional and Ollama is not installed or not available in PATH.\n\n"
                "Install Ollama, reopen Command Prompt, then run:\n"
                "ollama pull llama3.2:3b\n\n"
                "Rule-based fallback:\n"
                + self.formal_rewrite(text)
            )

        prompt = (
            "Rewrite the sentence below into clear, natural and professional English.\n"
            "Keep the same meaning.\n"
            "Do not add new facts.\n"
            "Do not explain the answer.\n"
            "Do not include labels such as 'Rewritten sentence'.\n"
            "Do not include notes, markdown, quotation marks, or extra commentary.\n"
            "Return only the final rewritten sentence.\n\n"
            f"Sentence: {text}\n\n"
            "Final rewritten sentence:"
        )

        for model in ["llama3.2:3b", "llama3.2", "llama3.2:1b"]:
            try:
                completed = subprocess.run(
                    ["ollama", "run", model, prompt],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                    encoding="utf-8",
                    errors="replace",
                )

            except subprocess.TimeoutExpired:
                return (
                    "Local LLM mode timed out, so the rule-based fallback was used.\n\n"
                    + self.formal_rewrite(text)
                )

            if completed.returncode == 0 and completed.stdout.strip():
                cleaned_output = self._clean_llm_output(completed.stdout)

                if cleaned_output and not self._looks_like_bad_llm_output(cleaned_output):
                    return cleaned_output

        return (
            "Ollama is installed, but a clean Llama output could not be produced.\n\n"
            "Rule-based fallback:\n"
            + self.formal_rewrite(text)
        )

    @staticmethod
    def _clean_llm_output(text: str) -> str:
        cleaned = (text or "").strip()

        # Remove encoding artefacts, ANSI terminal codes and hidden symbols.
        cleaned = cleaned.replace("�", " ")
        cleaned = re.sub(r"\x1b\[[0-9;]*m", "", cleaned)
        cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

        # Normalise smart quotes.
        cleaned = cleaned.replace("“", '"').replace("”", '"')
        cleaned = cleaned.replace("‘", "'").replace("’", "'")

        # Extract a useful quoted answer if Ollama wraps it in quotation marks.
        quoted = re.search(r'"([^"]{10,500})"', cleaned)
        if quoted:
            possible = quoted.group(1).strip()
            if possible:
                cleaned = possible

        # Remove common model labels and introductions.
        cleaned = re.sub(
            r"^(here(?:'s| is)?\s*)?(a\s*)?(rewritten|revised|improved|professional|clearer)\s*"
            r"(version|sentence|rewrite|response)?\s*(of\s*(the|your)\s*(text|sentence))?\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r"^(final rewritten sentence|rewritten sentence|rewritten text|rewrite|output|answer|response|result)\s*:\s*",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(r"^sentence\s*:\s*", "", cleaned, flags=re.IGNORECASE)

        # Remove explanation/commentary sentences.
        explanation_markers = [
            "this revised version",
            "this rewritten version",
            "this version",
            "let me know",
            "i hope",
            "note:",
            "explanation:",
            "the sentence has been",
            "i corrected",
            "i changed",
        ]

        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        kept_parts = []

        for part in parts:
            part_clean = part.strip()
            part_lower = part_clean.lower()

            if not part_clean:
                continue

            if any(marker in part_lower for marker in explanation_markers):
                continue

            kept_parts.append(part_clean)

        if kept_parts:
            cleaned = " ".join(kept_parts)

        # Keep output short enough for the chat bubble.
        final_sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        if len(final_sentences) > 2:
            cleaned = " ".join(final_sentences[:2]).strip()

        cleaned = re.sub(r"[#*_`]+", "", cleaned)
        cleaned = re.sub(r"\b(?:[0-9A-F]{2,4}|K)\b", "", cleaned)
        cleaned = re.sub(r"[^A-Za-z0-9\s.,!?;:'\"()\-]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        cleaned = re.sub(r"\b(\w+)\s+\1\b", r"\1", cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.replace(" .", ".").replace(" ,", ",")
        cleaned = cleaned.strip(" \"'")

        if cleaned and not re.search(r"[.!?]$", cleaned):
            cleaned += "."

        return cleaned

    @staticmethod
    def _looks_like_llm_instruction(text: str) -> bool:
        value = (text or "").lower()

        instruction_phrases = [
            "you are a writing assistant",
            "rewrite the text",
            "rewrite the sentence",
            "return only one",
            "return only the final",
            "do not explain",
            "do not add new facts",
            "keep the original meaning",
            "keep the same meaning",
            "final rewritten sentence",
        ]

        matches = sum(1 for phrase in instruction_phrases if phrase in value)
        return matches >= 2

    @staticmethod
    def _looks_like_bad_llm_output(text: str) -> bool:
        """Detect unusable LLM output so the app can fall back safely."""
        value = (text or "").strip().lower()
        bad_starts = (
            "please rewrite",
            "rewrite the sentence",
            "rewrite the text",
            "you are a writing assistant",
            "keep the same meaning",
            "do not explain",
            "return only",
        )
        return value.startswith(bad_starts)

    # Helper methods and rule dictionaries
    @staticmethod
    def split_sentences(text: str) -> List[str]:
        text = text.strip()

        if not text:
            return []

        parts = re.split(r"(?<=[.!?])\s+", text)
        return [part.strip() for part in parts if part.strip()]

    @staticmethod
    def _normalise_spacing(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        text = re.sub(r"([.!?])([A-Za-z])", r"\1 \2", text)
        return text

    @staticmethod
    def _ensure_sentence_punctuation(text: str) -> str:
        return text if re.search(r"[.!?]$", text) else text + "."

    @staticmethod
    def _capitalise_special_words(text: str) -> str:
        replacements = {
            r"\bi\b": "I",
            r"\benglish\b": "English",
            r"\beurope\b": "Europe",
            r"\blondon\b": "London",
            r"\bpython\b": "Python",
            r"\bai\b": "AI",
            r"\bnlp\b": "NLP",
            r"\bchatgpt\b": "ChatGPT",
            r"\btkinter\b": "Tkinter",
            r"\bollama\b": "Ollama",
            r"\bllama\b": "Llama",
        }

        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def _build_spelling_rules() -> List[Tuple[str, str]]:
        pairs = {
            r"\bu\b": "you",
            r"\bur\b": "your",
            r"\br\b": "are",
            r"\bim\b": "I am",
            r"\bi'm\b": "I am",
            r"\bdont\b": "do not",
            r"\bdon't\b": "do not",
            r"\bcant\b": "cannot",
            r"\bcan't\b": "cannot",
            r"\bwont\b": "will not",
            r"\bwon't\b": "will not",
            r"\bdoesnt\b": "does not",
            r"\bdoesn't\b": "does not",
            r"\bdidnt\b": "did not",
            r"\bdidn't\b": "did not",
            r"\bisnt\b": "is not",
            r"\bisn't\b": "is not",
            r"\barent\b": "are not",
            r"\baren't\b": "are not",
            r"\bwanna\b": "want to",
            r"\bgonna\b": "going to",
            r"\bgotta\b": "have to",
            r"\balot\b": "a lot",
            r"\bteh\b": "the",
            r"\brecieve\b": "receive",
            r"\bdefinately\b": "definitely",
            r"\bseperate\b": "separate",
            r"\boccured\b": "occurred",
            r"\bwich\b": "which",
            r"\bbecouse\b": "because",
            r"\bthier\b": "their",
            r"\bfreind\b": "friend",
            r"\bgrammer\b": "grammar",
            r"\bsentance\b": "sentence",
        }

        return list(pairs.items())

    @staticmethod
    def _build_formal_rules() -> List[Tuple[str, str]]:
        pairs = {
            r"\bwant to\b": "would like to",
            r"\bget\b": "obtain",
            r"\bgot\b": "received",
            r"\bbig\b": "significant",
            r"\bsmall\b": "limited",
            r"\bstuff\b": "materials",
            r"\bthings\b": "factors",
            r"\bkids\b": "children",
            r"\bjob\b": "role",
            r"\bhelp\b": "support",
            r"\bshow\b": "demonstrate",
            r"\bmake\b": "produce",
            r"\buse\b": "utilise",
            r"\bvery good\b": "highly effective",
            r"\bnot very good\b": "limited",
            r"\bbad\b": "ineffective",
            r"\ba lot\b": "a considerable amount",
            r"\blots of\b": "a significant amount of",
            r"\bmany\b": "numerous",
            r"\bso\b": "therefore",
            r"\bbut\b": "however",
            r"\bsound more professional\b": "appear more professional",
        }

        return list(pairs.items())

    @staticmethod
    def _build_synonym_groups() -> Dict[str, List[str]]:
        return {
            "important": ["essential", "significant", "valuable", "meaningful"],
            "improve": ["enhance", "strengthen", "refine", "develop"],
            "good": ["effective", "useful", "strong", "suitable"],
            "hard": ["challenging", "difficult", "demanding"],
            "bad": ["weak", "ineffective", "poor", "limited"],
            "help": ["support", "assist", "guide", "enable"],
            "student": ["learner", "academic user"],
            "students": ["learners", "academic users"],
            "clear": ["understandable", "direct", "easy to follow", "well-structured"],
            "simple": ["straightforward", "accessible", "user-friendly", "lightweight"],
            "use": ["apply", "utilise", "work with", "employ"],
            "uses": ["applies", "utilises", "works with", "employs"],
            "write": ["compose", "produce text", "draft", "express ideas"],
            "writing": ["written communication", "text", "drafting", "composition"],
            "project": ["application", "system", "prototype", "tool"],
            "chatbot": ["chat assistant", "rewriting assistant", "interactive tool"],
            "fast": ["quick", "rapid", "efficient", "responsive"],
            "problem": ["issue", "challenge", "difficulty", "concern"],
            "professional": ["formal", "polished", "workplace-suitable", "academic"],
            "money": ["funds", "financial resources", "budget"],
            "answer": ["response", "solution", "explanation"],
            "visit": ["travel to", "go to", "experience"],
            "sentence": ["line of text", "written sentence", "statement"],
            "report": ["document", "assignment", "written report"],
        }

    @staticmethod
    def _build_structure_patterns() -> List[Tuple[str, List[str]]]:
        return [
            (
                r"^(.*?)\s+because\s+(.*?)\.?$",
                [
                    "{0} as {1}.",
                    "{0}. This is because {1}.",
                    "Since {1}, {0}.",
                ],
            ),
            (
                r"^I would like to\s+(.*?)\s+because\s+(.*?)\.?$",
                [
                    "My aim is to {0} because {1}.",
                    "I intend to {0} as {1}.",
                ],
            ),
            (
                r"^(.*?)\s+so\s+(.*?)\.?$",
                [
                    "{0}; therefore, {1}.",
                    "As a result, {1}.",
                    "{0}, which means that {1}.",
                ],
            ),
            (
                r"^(.*?)\s+but\s+(.*?)\.?$",
                [
                    "Although {0}, {1}.",
                    "{0}; however, {1}.",
                ],
            ),
        ]


def demo_examples() -> Iterable[Tuple[str, str]]:
    """Examples used in the presentation demo."""
    return [
        ("grammar", "i dont know teh answer becouse it is very hard"),
        (
            "paraphrase",
            "This project helps students improve English writing because it is simple.",
        ),
        ("formal", "i wanna ask about the meeting because i cant come today"),
        ("smart", "i want to visit europe because i have lots of money"),
        (
            "llm",
            "i wanna submit this report becouse my english sentence is not good and it need to sound more professional",
        ),
    ]
