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

    @staticmethod
    def get_ui_labels() -> Dict[str, Dict[str, str]]:
        """Get UI labels for different languages"""
        return {
            "ja": {
                "title": "Home AI",
                "caption": "LangChain + Streamlitで構築されたホームAIアシスタント",
                "settings": "⚙️ 設定",
                "language": "言語",
                "language_help": "AIの応答言語を選択します。",
                "session_id": "セッションID",
                "session_id_help": "会話を識別するID。変更すると新しい会話が開始されます。",
                "clear_history": "🗑️ 会話履歴をクリア",
                "model_info": "📊 モデル情報",
                "language_info": "言語",
                "input_placeholder": "メッセージを入力...",
                "thinking": "考え中...",
            },
            "en": {
                "title": "Home AI",
                "caption": "Home AI assistant built with LangChain + Streamlit",
                "settings": "⚙️ Settings",
                "language": "Language",
                "language_help": "Select the language for AI responses.",
                "session_id": "Session ID",
                "session_id_help": "ID to identify conversations. Changing this starts a new conversation.",
                "clear_history": "🗑️ Clear Conversation History",
                "model_info": "📊 Model Information",
                "language_info": "Language",
                "input_placeholder": "Enter your message...",
                "thinking": "Thinking...",
            },
            "zh": {
                "title": "Home AI",
                "caption": "使用LangChain + Streamlit构建的家庭AI助手",
                "settings": "⚙️ 设置",
                "language": "语言",
                "language_help": "选择AI回复的语言。",
                "session_id": "会话ID",
                "session_id_help": "用于标识对话的ID。更改此ID将开始新对话。",
                "clear_history": "🗑️ 清除对话历史",
                "model_info": "📊 模型信息",
                "language_info": "语言",
                "input_placeholder": "输入您的消息...",
                "thinking": "思考中...",
            },
            "es": {
                "title": "Home AI",
                "caption": "Asistente de IA del hogar construido con LangChain + Streamlit",
                "settings": "⚙️ Configuración",
                "language": "Idioma",
                "language_help": "Seleccione el idioma para las respuestas de la IA.",
                "session_id": "ID de Sesión",
                "session_id_help": "ID para identificar conversaciones. Cambiar esto inicia una nueva conversación.",
                "clear_history": "🗑️ Borrar Historial de Conversación",
                "model_info": "📊 Información del Modelo",
                "language_info": "Idioma",
                "input_placeholder": "Ingrese su mensaje...",
                "thinking": "Pensando...",
            },
            "fr": {
                "title": "Home AI",
                "caption": "Assistant IA domestique construit avec LangChain + Streamlit",
                "settings": "⚙️ Paramètres",
                "language": "Langue",
                "language_help": "Sélectionnez la langue pour les réponses de l'IA.",
                "session_id": "ID de Session",
                "session_id_help": "ID pour identifier les conversations. Changer cela lance une nouvelle conversation.",
                "clear_history": "🗑️ Effacer l'Historique des Conversations",
                "model_info": "📊 Informations sur le Modèle",
                "language_info": "Langue",
                "input_placeholder": "Entrez votre message...",
                "thinking": "Réflexion...",
            },
        }


# Default templates for backward compatibility
DEFAULT_JAPANESE_PROMPT = PromptTemplates.create_prompt_template("ja")
DEFAULT_ENGLISH_PROMPT = PromptTemplates.create_prompt_template("en")
