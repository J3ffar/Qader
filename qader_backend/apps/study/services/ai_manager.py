import json
import logging
from typing import List, Optional, Dict, Any, Tuple, Union

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from openai import OpenAI, OpenAIError

# Assuming ConversationSession is in apps.study.models for AiTone definitions
# If not, we'll pass tone strings directly.
from apps.study.models import (
    ConversationMessage,
    ConversationSession,
)

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_AI_MODEL = getattr(settings, "AI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = getattr(settings, "AI_DEFAULT_TEMPERATURE", 0.7)
DEFAULT_MAX_TOKENS = getattr(settings, "AI_DEFAULT_MAX_TOKENS", 1000)
MAX_HISTORY_MESSAGES_FOR_AI_CONTEXT = getattr(settings, "MAX_HISTORY_MESSAGES", 20)


# --- User-Facing Error Messages ---
AI_UNAVAILABLE_ERROR_MSG = _(
    "Sorry, the AI assistant is currently unavailable. Please try again later."
)
AI_RESPONSE_ERROR_MSG = _(
    "An unexpected error occurred while generating my response. Please try again."
)
AI_SPEECHLESS_MSG = _("I seem to be speechless! Could you try rephrasing?")
AI_JSON_PARSE_ERROR_MSG = _(
    "I had a little trouble formatting my thoughts. Could you try again?"
)


# --- System Prompt Configuration ---
BASE_PERSONA_PROMPT = getattr(
    settings,
    "AI_BASE_PERSONA_PROMPT",
    """
You are Qader AI, a helpful and encouraging AI assistant for students preparing for the Qudurat test (Saudi Arabia's aptitude test).
Your goal is to help students understand concepts, practice questions, and build confidence.
Focus on the Verbal (اللفظي) and Quantitative (الكمي) sections.
Keep your explanations clear, concise, and step-by-step.
If asked about a specific question, use the provided database information if possible.
When the user indicates understanding ('Got it'), prepare to test them on a related concept.
Do not reveal answers or detailed solutions unless explicitly asked or when explaining a concept the user struggled with.
When asked to provide a question, give a motivational message first, then clearly state the question.
Ensure your responses are culturally appropriate for Saudi Arabia. And your output language must be in Arabic.
""",
)

# Context-specific instruction templates. These are added to the base persona.
# Keys correspond to use cases. Placeholders like {tone} or {user_message_text} will be formatted.
CONTEXTUAL_INSTRUCTIONS = {
    "general_conversation": "",
    "generate_cheer_message": """
The user wants you to ask them a practice question.
The question is about the topic: '{topic_context}'.
Its text starts with: "{question_text_snippet}..."
Generate a short, encouraging message (in the previously defined {tone} tone) to preface this question.
Keep the message brief (1-2 sentences maximum).
DO NOT include the question text itself or the options in your generated message, only the preface.
Example ({cheerful_example_tone} tone): "Alright! Let's test your skills with this one... ✨ (Something like this message but let be different to not be the same every time)"
Example ({serious_example_tone} tone): "Okay, let's try a question on this topic. (Something like this message but let be different to not be the same every time)"
    """,
    "process_user_answer_intent": """
Analyze the latest user message: '{user_message_text}'
Determine the user's intent based on the message and the current context (if any).
Your response MUST be a valid JSON object with the following keys:
    - `processed_as_answer`: boolean (true if the message is primarily an answer choice like 'A', 'b.', 'answer is C', etc. for the current question; false otherwise).
    - `user_choice`: string (The detected answer choice 'A', 'B', 'C', or 'D' if processed_as_answer is true, otherwise null). Valid choices are 'A', 'B', 'C', 'D'.
    - `feedback_text`: string (Your generated response message, adhering to the previously defined {tone} tone).
{question_context_block}
Specific Instructions for intent determination and feedback_text generation:
{intent_instructions_block}
Ensure the output is ONLY the JSON object. And without markdown JSON like ```json ``` just pure JSON output.
    """,
    "generate_answer_feedback": """
Analyze the user's attempt and generate feedback in JSON format.
Context:
    - Question ID: {question_id}
    - Question Text Snippet: "{question_text_snippet}..."
    - User's Answer: '{user_answer}'
    - Correct Answer: '{correct_answer}'
    - Was User Correct?: {is_correct}
    - Explanation Snippet: "{explanation_snippet}..."

Your response MUST be a valid JSON object containing EXACTLY ONE key, Example JSON Output, And remember do not include markdown:
{{
    `feedback_text`: string (The detailed feedback message for the user, in the previously defined {tone} tone).
}}

Instructions for `feedback_text`:
- If the user was correct (Was User Correct? is True):
    - Provide an encouraging confirmation (in the defined {tone} tone).
    - Briefly reinforce *why* the answer '{correct_answer}' is correct, using the Explanation Snippet.
- If the user was incorrect (Was User Correct? is False):
    - Provide constructive feedback (in the defined {tone} tone).
    - State the correct answer was '{correct_answer}'.
    - Explain *why* '{correct_answer}' is correct, using the Explanation Snippet. Keep it helpful.
Example Correct ({cheerful_example_tone} tone):
{{"feedback_text": "Excellent! 😎 '{correct_answer}' is exactly right because [brief reason from explanation]..."}}
Example Incorrect ({serious_example_tone} tone):
{{"feedback_text": "Not quite. The correct answer was '{correct_answer}'. This is because [explanation based on snippet]..."}}
Output ONLY the JSON object.
    """,
    "generate_emergency_tips": """
You are an encouraging AI assistant helping a student in 'Emergency Mode' prepare for the Qudurat test.
The user needs quick, actionable tips for an emergency study session.
Context:
- Focus Areas: {focus_areas_str}
- Identified Weak Skills/Areas for Improvement:
    {weak_skills_summary_str}
- Available Time: {time_context}

Task: Generate 2-3 concise, positive, and actionable tips tailored to this context.
Focus on:
- Stress management / staying calm.
- Quick strategies relevant to identified weak areas (if any).
- General test-taking advice for time pressure.

Your response MUST be a valid JSON object containing EXACTLY ONE key:
    `tips`: List[str] (A list containing 2 or 3 string tips).
Example JSON Output:
{{
    "tips": [
    "Take a moment to breathe deeply before you begin. You've got this!",
    "For '{{weak_skill_example}}', focus on [quick strategy, e.g., keyword spotting/formula recall].",
    "Read each question carefully, but trust your first instinct if short on time."
    ]
}}
Output ONLY the JSON object. And without markdown JSON like ```json ``` just pure JSON output.
    """,
    "generate_test_performance_analysis": """
You are Qader AI, an encouraging assistant analyzing a student's test performance for the Qudurat test.
The user has just completed a test. Your goal is to provide a concise, insightful, and actionable summary.
Your output language MUST be in Arabic.

Test Details Provided:
- Overall Score: {overall_score}%
- Verbal Score: {verbal_score_str}
- Quantitative Score: {quantitative_score_str}
- Performance by Topic/Subsection (Name: Score%):
{results_summary_str}
- Test Type: {test_type_display}

Task:
Generate a brief (target 2-4 sentences, max 5) analysis in Arabic.
1. Acknowledge the effort and mention the overall score. Example: "عمل رائع في إكمال {test_type_display}! نتيجتك الإجمالية هي {overall_score}%."
2. If applicable, briefly comment on verbal/quantitative performance if scores are available. Example: "أداؤك في القسم اللفظي كان {verbal_score_str} وفي القسم الكمي {quantitative_score_str}." (Only if scores are not "N/A").
3. Identify one or two topics/subsections where the user performed weakest (lowest scores from the summary, e.g., below 60-70%). Suggest focusing on these. Example: "لتحسين أدائك أكثر، نقترح التركيز على [اسم الموضوع الضعيف الأول] حيث كانت نتيجتك [النتيجة]%." (Mention specific score).
4. If there are clear strengths (high scores in some topics, e.g., above 85-90%), mention one briefly as encouragement. Example: "لقد أظهرت فهمًا جيدًا في [اسم الموضوع القوي]."
5. Maintain an encouraging and constructive tone. Avoid overly negative language.
6. If scores are generally high (e.g., overall > 85%), congratulate the user. If scores are low, focus on improvement steps.
7. If the results_summary is empty or lacks scorable data, provide a general encouraging message about completing the test and suggest reviewing the material.

Example (conceptual, ensure final output is purely Arabic text):
"عمل رائع في إكمال اختبار {test_type_display}! نتيجتك الإجمالية هي {overall_score}%.
أظهرت فهمًا جيدًا في [اسم الموضوع القوي].
لتحسين أدائك أكثر، نقترح التركيز على [اسم الموضوع الضعيف الأول] حيث كانت نتيجتك [النتيجة]%."

Output ONLY the generated text analysis as a single string. Do not use markdown or JSON.
    """,
}


def get_tone_instruction_text(ai_tone_value: str) -> str:
    """Returns specific tone instructions for the system prompt based on ConversationSession.AiTone value."""
    # Ensure ConversationSession.AiTone is available or provide a fallback mechanism
    # For this specific use case, we might pre-define the tone or make it configurable.
    # Let's assume a default "encouraging" tone for performance analysis.
    tone_map = {
        ConversationSession.AiTone.CHEERFUL: "Use a cheerful, friendly, and slightly informal tone. Use emojis appropriately to convey encouragement (e.g., 😎, ✨, 👍).",  # Assuming ConversationSession.AiTone.CHEERFUL.value
        ConversationSession.AiTone.SERIOUS: "Maintain a professional, encouraging, but more formal and direct tone.",  # Assuming ConversationSession.AiTone.SERIOUS.value
        "encouraging_analytic": "Maintain an encouraging, supportive, yet analytical tone suitable for providing feedback on test performance. Focus on actionable advice.",
    }
    return tone_map.get(ai_tone_value, tone_map["encouraging_analytic"])


class AIInteractionManager:
    def __init__(self):
        self.client, self.init_error = self._initialize_openai_client()
        if self.init_error:
            logger.error(
                f"AIInteractionManager initialization failed: {self.init_error}"
            )

    def _initialize_openai_client(self) -> Tuple[Optional[OpenAI], Optional[str]]:
        client_instance = None
        error_message = None
        try:
            if settings.OPENAI_API_KEY:
                kwargs = {"api_key": settings.OPENAI_API_KEY}
                if base_url := getattr(settings, "OPENAI_API_BASE_URL", None):
                    kwargs["base_url"] = base_url
                client_instance = OpenAI(**kwargs)
                logger.info(
                    "OpenAI client initialized successfully for AIInteractionManager."
                )
            else:
                error_message = (
                    "OPENAI_API_KEY not configured. AI features will be disabled."
                )
        except Exception as e:
            error_message = f"Failed to initialize OpenAI client: {e}"
            logger.exception(error_message)
        return client_instance, error_message

    def is_available(self) -> bool:
        return self.client is not None

    def get_error_message_if_unavailable(self) -> str:
        reason = f" (Reason: {self.init_error})" if self.init_error else ""
        return f"{AI_UNAVAILABLE_ERROR_MSG}{reason}"

    def _construct_system_prompt(
        self,
        ai_tone_value: str,  # This will now accept a string like "encouraging_analytic"
        context_key: Optional[str] = None,
        context_params: Optional[Dict[str, Any]] = None,
        additional_instructions: Optional[List[str]] = None,
    ) -> str:
        prompt_parts = [BASE_PERSONA_PROMPT]
        prompt_parts.append(get_tone_instruction_text(ai_tone_value))

        if context_key and context_key in CONTEXTUAL_INSTRUCTIONS:
            instruction_template = CONTEXTUAL_INSTRUCTIONS[context_key]
            # Add tone to context_params so templates can also reference it if needed for examples
            full_context_params = {"tone": ai_tone_value, **(context_params or {})}
            # Add example tones for templates that use them
            full_context_params["cheerful_example_tone"] = (
                ConversationSession.AiTone.CHEERFUL.value
            )
            full_context_params["serious_example_tone"] = (
                ConversationSession.AiTone.SERIOUS.value
            )

            try:
                prompt_parts.append(instruction_template.format(**full_context_params))
            except KeyError as e:
                logger.error(
                    f"Missing key {e} for formatting contextual instruction '{context_key}'. Params: {full_context_params}"
                )
                # Fallback: append raw template or a generic error message within prompt?
                # For now, we'll just miss this part of the instruction.

        if additional_instructions:
            prompt_parts.extend(additional_instructions)

        return "\n\n".join(filter(None, prompt_parts))

    def _format_conversation_history(
        self, history: List[ConversationMessage]
    ) -> List[Dict[str, str]]:
        """Formats ConversationMessage history for the AI API."""
        formatted_messages = []
        for msg in history[-MAX_HISTORY_MESSAGES_FOR_AI_CONTEXT:]:
            role = (
                "user"
                if msg.sender_type == ConversationMessage.SenderType.USER
                else "assistant"
            )
            formatted_messages.append({"role": role, "content": msg.message_text})
        return formatted_messages

    def get_chat_completion(
        self,
        system_prompt_content: str,
        messages_for_api: List[
            Dict[str, str]
        ],  # Already includes history + current user message or task trigger
        model: str = DEFAULT_AI_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, str]] = None,
        user_id_for_tracking: Optional[str] = None,
    ) -> Tuple[Optional[Union[str, Dict]], Optional[str]]:
        """
        Core method to interact with OpenAI ChatCompletion.
        Returns (response_content, user_facing_error_message).
        response_content is str or dict (if JSON parsed successfully).
        """
        if not self.is_available():
            return None, self.get_error_message_if_unavailable()

        api_payload_messages = [
            {"role": "system", "content": system_prompt_content},
            *messages_for_api,
        ]

        api_kwargs = {
            "model": model,
            "messages": api_payload_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if user_id_for_tracking:
            api_kwargs["user"] = user_id_for_tracking

        try:
            # Truncate log message if too long
            log_payload_str = json.dumps(
                api_payload_messages, ensure_ascii=False, indent=2
            )
            log_snippet = log_payload_str[:1000] + (
                "..." if len(log_payload_str) > 1000 else ""
            )

            logger.info(
                f"Calling OpenAI ({model}) with {len(api_payload_messages)} messages. "
                f"User: {user_id_for_tracking or 'N/A'}. Response Format: {response_format}. Snippet: {log_snippet}"
            )

            completion = self.client.chat.completions.create(**api_kwargs)
            content = completion.choices[0].message.content

            if not content:
                logger.warning(
                    f"Received empty AI response. User: {user_id_for_tracking or 'N/A'}"
                )
                return None, AI_SPEECHLESS_MSG

            # If expecting JSON, try to parse it
            if response_format and response_format.get("type") == "json_object":
                try:
                    # Remove markdown backticks if present before parsing JSON
                    # This is a common issue with models outputting JSON in markdown
                    if content.strip().startswith("```json"):
                        content_cleaned = content.strip()[7:]  # Remove ```json\n
                        if content_cleaned.endswith("```"):
                            content_cleaned = content_cleaned[:-3]  # Remove ```
                        content = content_cleaned.strip()
                    elif content.strip().startswith(
                        "```"
                    ):  # Less specific, but might catch other markdown variations
                        content_cleaned = content.strip()[3:]
                        if content_cleaned.endswith("```"):
                            content_cleaned = content_cleaned[:-3]
                        content = content_cleaned.strip()

                    parsed_json = json.loads(content)
                    logger.info(
                        f"AI JSON response parsed successfully. User: {user_id_for_tracking or 'N/A'}"
                    )
                    return parsed_json, None
                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse AI JSON response. Error: {e}. Raw Response: '{content}'. User: {user_id_for_tracking or 'N/A'}",
                        exc_info=True,
                    )
                    return None, AI_JSON_PARSE_ERROR_MSG

            # If not expecting JSON, or if parsing wasn't required/attempted, return as string
            logger.info(
                f"AI text response received. User: {user_id_for_tracking or 'N/A'}"
            )
            return content.strip(), None

        except OpenAIError as e:
            logger.error(
                f"OpenAI API error: {e}. User: {user_id_for_tracking or 'N/A'}",
                exc_info=True,
            )
            # Provide a more specific error if possible, e.g., based on e.status_code
            user_facing_error = AI_RESPONSE_ERROR_MSG
            if hasattr(e, "status_code"):
                if e.status_code == 429:  # Rate limit
                    user_facing_error = _(
                        "The AI service is currently busy. Please try again in a moment."
                    )
                elif e.status_code == 401:  # Auth error
                    user_facing_error = _(
                        "There's an issue with AI service authentication. Please contact support."
                    )
            return None, user_facing_error
        except Exception as e:
            logger.exception(
                f"Unexpected error calling AI: {e}. User: {user_id_for_tracking or 'N/A'}"
            )
            return None, AI_RESPONSE_ERROR_MSG


_ai_manager_instance = None


def get_ai_manager() -> AIInteractionManager:
    global _ai_manager_instance
    if _ai_manager_instance is None:
        _ai_manager_instance = AIInteractionManager()
    return _ai_manager_instance
