"""
Multi-language prompt templates for HomeAI
==========================================

This module contains prompt templates for different languages
to support internationalization in the chat interface.
"""

from typing import Dict
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class PromptTemplates:
    """Multi-language prompt templates for HomeAI"""

    @staticmethod
    def get_system_prompts() -> Dict[str, str]:
        """Get system prompts for different languages"""
        return {
            "ja": (
                "あなたは親切で優秀な日本語アシスタントです。"
                "質問には正確かつ簡潔に答えてください。"
            ),
            "en": (
                "You are a kind and helpful English-speaking assistant. "
                "Please answer questions accurately and concisely."
            ),
            "zh": ("你是一位友善且优秀的中文助手。请准确简洁地回答问题。"),
            "es": (
                "Eres un asistente amable y servicial que habla español. "
                "Por favor responde a las preguntas de manera precisa y concisa."
            ),
            "fr": (
                "Vous êtes un assistant serviable et parlant français. "
                "Veuillez répondre aux questions de manière précise et concise."
            ),
        }

    @staticmethod
    def get_input_labels() -> Dict[str, str]:
        """Get input labels for different languages"""
        return {
            "ja": "human",
            "en": "human",
            "zh": "human",
            "es": "human",
            "fr": "human",
        }

    @staticmethod
    def create_prompt_template(language: str = "en") -> ChatPromptTemplate:
        """Create a prompt template for the specified language"""
        prompts = PromptTemplates.get_system_prompts()
        labels = PromptTemplates.get_input_labels()

        if language not in prompts:
            language = "en"  # Fallback to English

        return ChatPromptTemplate.from_messages(
            [
                ("system", prompts[language]),
                MessagesPlaceholder(variable_name="history"),
                (labels[language], "{input}"),
            ]
        )

    @staticmethod
    def get_available_languages() -> Dict[str, str]:
        """Get available languages with their display names"""
        return {
            "ja": "日本語",
            "en": "English",
            "zh": "中文",
            "es": "Español",
            "fr": "Français",
        }


# Default templates for backward compatibility
DEFAULT_JAPANESE_PROMPT = PromptTemplates.create_prompt_template("ja")
DEFAULT_ENGLISH_PROMPT = PromptTemplates.create_prompt_template("en")
