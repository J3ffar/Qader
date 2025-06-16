import json
import logging
from typing import List, Optional, Dict, Any, Tuple, Union

from django.conf import settings
from django.utils.translation import gettext_lazy as _  # Keep for defining lazy strings
from django.utils.functional import Promise  # For type checking __proxy__
from django.utils.encoding import force_str  # For converting lazy objects to strings
from openai import OpenAI, OpenAIError

from apps.study.models import ConversationMessage, ConversationSession

logger = logging.getLogger(__name__)

# --- Constants ---
DEFAULT_AI_MODEL = getattr(settings, "AI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = getattr(settings, "AI_DEFAULT_TEMPERATURE", 0.7)
DEFAULT_MAX_TOKENS = getattr(settings, "AI_DEFAULT_MAX_TOKENS", 1000)
MAX_HISTORY_MESSAGES_FOR_AI_CONTEXT = getattr(settings, "MAX_HISTORY_MESSAGES", 20)


# --- User-Facing Error Messages (ensure these are cast to str if used in JSON directly, though usually they are not) ---
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
BASE_PERSONA_PROMPT = force_str(
    getattr(
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
)

# CONTEXTUAL_INSTRUCTIONS values are templates. When they are .format()ted,
# the parameters passed to .format() must also be strings.
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
    "generate_understanding_test_preface": """
You are Qader AI. The user has just indicated they understand a concept related to a question about '{topic_context}'.
You have selected a new, related question to test their understanding.
Generate a short, encouraging message (in the previously defined {tone} tone) to introduce this new test question.
Keep it brief (1-2 sentences).
DO NOT include the question text itself in your message.
Example ({cheerful_example_tone} tone): "Awesome, glad to hear it! Let's see that knowledge in action with this question. Good luck! ✨"
Example ({serious_example_tone} tone): "Understood. To confirm your comprehension, please attempt the following related question."
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
- Summary of Some Answers (primarily incorrect ones):
{user_answers_details_str}

Task:
Generate a brief (target 2-4 sentences, max 5) analysis in Arabic.
1. Acknowledge the effort and mention the overall score. Example: "عمل رائع في إكمال {test_type_display}! نتيجتك الإجمالية هي {overall_score}%."
2. If applicable, briefly comment on verbal/quantitative performance if scores are available. Example: "أداؤك في القسم اللفظي كان {verbal_score_str} وفي القسم الكمي {quantitative_score_str}." (Only if scores are not "N/A").
3. Using the "Summary of Some Answers" and "Performance by Topic/Subsection", identify one or two topics/subsections where the user struggled most.
   If the "Summary of Some Answers" provides clues (e.g., specific skills missed within a low-scoring subsection, or common error patterns if visible from the summary), try to mention this.
   Example: "لتحسين أدائك أكثر، نقترح التركيز على [اسم الموضوع الضعيف الأول] حيث كانت نتيجتك [النتيجة]%. استنادًا إلى إجاباتك، يبدو أن الأسئلة المتعلقة بـ [مهارة معينة أو نوع سؤال معين من ملخص الإجابات] في هذا الموضوع كانت تمثل تحديًا."
4. If there are clear strengths (high scores in some topics, e.g., above 85-90%), mention one briefly as encouragement. If "Summary of Some Answers" shows correct handling of certain types, you can allude to it.
   Example: "لقد أظهرت فهمًا جيدًا في [اسم الموضوع القوي]."
5. Maintain an encouraging and constructive tone. Avoid overly negative language.
6. If scores are generally high (e.g., overall > 85%), congratulate the user. If scores are low, focus on improvement steps.
7. If the results_summary or answer details are sparse or not very informative, provide a general encouraging message about completing the test and suggest reviewing the material broadly.

Output ONLY the generated text analysis as a single string. Do not use markdown or JSON.
    """,
}


def get_tone_instruction_text(ai_tone_value: str) -> str:
    """Returns specific tone instructions for the system prompt based on ConversationSession.AiTone value."""
    tone_map = {
        ConversationSession.AiTone.CHEERFUL: "Use a cheerful, friendly, and slightly informal tone. Use emojis appropriately to convey encouragement (e.g., 😎, ✨, 👍).",  # Assuming ConversationSession.AiTone.CHEERFUL.value
        ConversationSession.AiTone.SERIOUS: "Maintain a professional, encouraging, but more formal and direct tone.",  # Assuming ConversationSession.AiTone.SERIOUS.value
        "encouraging_analytic": "Maintain an encouraging, supportive, yet analytical tone suitable for providing feedback on test performance. Focus on actionable advice.",
    }
    # Ensure the returned value is a plain string
    return force_str(tone_map.get(ai_tone_value, tone_map["encouraging_analytic"]))


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
        return force_str(f"{AI_UNAVAILABLE_ERROR_MSG}{reason}")

    def _construct_system_prompt(
        self,
        ai_tone_value: str,
        context_key: Optional[str] = None,
        context_params: Optional[Dict[str, Any]] = None,
        additional_instructions: Optional[List[str]] = None,
    ) -> str:
        prompt_parts = [BASE_PERSONA_PROMPT]
        prompt_parts.append(get_tone_instruction_text(ai_tone_value))

        if context_key and context_key in CONTEXTUAL_INSTRUCTIONS:
            instruction_template = CONTEXTUAL_INSTRUCTIONS[context_key]

            # Ensure all context_params values are strings before formatting
            safe_context_params = {}
            if context_params:
                for key, value in context_params.items():
                    safe_context_params[key] = (
                        force_str(value) if isinstance(value, Promise) else value
                    )

            full_context_params = {"tone": ai_tone_value, **safe_context_params}
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

        if additional_instructions:
            prompt_parts.extend([force_str(instr) for instr in additional_instructions])

        return "\n\n".join(filter(None, prompt_parts))

    def _format_conversation_history(
        self, history: List[ConversationMessage]
    ) -> List[Dict[str, str]]:
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
        messages_for_api: List[Dict[str, str]],
        model: str = DEFAULT_AI_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        response_format: Optional[Dict[str, str]] = None,
        user_id_for_tracking: Optional[str] = None,
    ) -> Tuple[Optional[Union[str, Dict]], Optional[str]]:
        if not self.is_available():
            return (
                None,
                self.get_error_message_if_unavailable(),
            )  # Returns forced string

        # Ensure all content in messages_for_api is string
        safe_messages_for_api = [
            {"role": msg["role"], "content": force_str(msg["content"])}
            for msg in messages_for_api
        ]

        api_payload_messages = [
            {"role": "system", "content": system_prompt_content},  # Already a string
            *safe_messages_for_api,
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
            # The api_payload_messages should now be safe for json.dumps
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
                return None, force_str(AI_SPEECHLESS_MSG)

            if response_format and response_format.get("type") == "json_object":
                try:
                    if content.strip().startswith("```json"):
                        content_cleaned = content.strip()[7:]
                        if content_cleaned.endswith("```"):
                            content_cleaned = content_cleaned[:-3]
                        content = content_cleaned.strip()
                    elif content.strip().startswith("```"):
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
                    return None, force_str(AI_JSON_PARSE_ERROR_MSG)

            logger.info(
                f"AI text response received. User: {user_id_for_tracking or 'N/A'}"
            )
            return content.strip(), None

        except OpenAIError as e:
            logger.error(
                f"OpenAI API error: {e}. User: {user_id_for_tracking or 'N/A'}",
                exc_info=True,
            )
            user_facing_error = AI_RESPONSE_ERROR_MSG
            if hasattr(e, "status_code"):
                if e.status_code == 429:
                    user_facing_error = _(
                        "The AI service is currently busy. Please try again in a moment."
                    )
                elif e.status_code == 401:
                    user_facing_error = _(
                        "There's an issue with AI service authentication. Please contact support."
                    )
            return None, force_str(user_facing_error)
        except Exception as e:  # This will catch the TypeError if it still occurs
            logger.exception(
                f"Unexpected error calling AI: {e}. User: {user_id_for_tracking or 'N/A'}"
            )
            return None, force_str(AI_RESPONSE_ERROR_MSG)


_ai_manager_instance = None


def get_ai_manager() -> AIInteractionManager:
    global _ai_manager_instance
    if _ai_manager_instance is None:
        _ai_manager_instance = AIInteractionManager()
    return _ai_manager_instance
