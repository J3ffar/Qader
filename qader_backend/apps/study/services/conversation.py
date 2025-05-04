import json
import logging
from typing import List, Optional, Dict, Any, Tuple

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openai import OpenAI, OpenAIError
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers  # For raising validation errors

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill
from apps.users.models import UserProfile
from django.contrib.auth import get_user_model

# Assuming get_filtered_questions is in apps.study.services
from .study import get_filtered_questions, update_user_skill_proficiency

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Constants ---
AI_MODEL = getattr(settings, "AI_MODEL", "gpt-3.5-turbo")  # Default model
MAX_HISTORY_MESSAGES = getattr(settings, "MAX_HISTORY_MESSAGES", 20)  # Sensible default
DEFAULT_AI_ERROR_MSG = _(
    "Sorry, the AI assistant is currently unavailable. Please try again later."
)
DEFAULT_AI_RESPONSE_ERROR_MSG = _(
    "An unexpected error occurred while generating my response. Please try again."
)
DEFAULT_AI_SPEECHLESS_MSG = _("I seem to be speechless! Could you try rephrasing?")


# --- AI Client Initialization ---
# Encapsulate initialization logic for clarity and potential reuse/testing
def _initialize_openai_client() -> Tuple[Optional[OpenAI], Optional[str]]:
    """Initializes and returns the OpenAI client and any initialization error message."""
    client_instance = None
    error_message = None
    try:
        if settings.OPENAI_API_KEY:
            kwargs = {"api_key": settings.OPENAI_API_KEY}
            if base_url := getattr(settings, "OPENAI_API_BASE_URL", None):
                kwargs["base_url"] = base_url
                logger.info(
                    f"Initializing OpenAI client with custom base URL: {base_url}"
                )
            else:
                logger.info("Initializing OpenAI client with default base URL.")

            client_instance = OpenAI(**kwargs)
            # Optional: Perform a quick check like listing models
            # client_instance.models.list()
            logger.info(
                f"OpenAI client initialized successfully using model: {AI_MODEL}"
            )
        else:
            error_message = (
                "OPENAI_API_KEY not configured. AI features will be disabled."
            )
            logger.warning(error_message)
    except Exception as e:
        error_message = f"Failed to initialize OpenAI client: {e}"
        logger.exception(error_message)  # Log the full traceback

    return client_instance, error_message


client, openai_init_error = _initialize_openai_client()

# --- System Prompt Generation ---
SYSTEM_PROMPT_BASE = """
You are Qader AI, a helpful and encouraging AI assistant for students preparing for the Qudurat test (Saudi Arabia's aptitude test).
Your goal is to help students understand concepts, practice questions, and build confidence.
Focus on the Verbal (اللفظي) and Quantitative (الكمي) sections.
Keep your explanations clear, concise, and step-by-step.
Maintain a positive and motivating tone appropriate for the user's selected preference.
If asked about a specific question, use the provided database information if possible.
When the user indicates understanding ('Got it'), prepare to test them on a related concept.
Do not reveal answers or detailed solutions unless explicitly asked or when explaining a concept the user struggled with.
When asked to provide a question, give a motivational message first, then clearly state the question.
Ensure your responses are culturally appropriate for Saudi Arabia.
"""


def _get_tone_instruction(tone: str) -> str:
    """Returns specific tone instructions for the system prompt."""
    tone_map = {
        ConversationSession.AiTone.CHEERFUL: "Use a cheerful, friendly, and slightly informal tone. Use emojis appropriately to convey encouragement (e.g., 😎, ✨, 👍).",
        ConversationSession.AiTone.SERIOUS: "Maintain a professional, encouraging, but more formal and direct tone.",
        # Add other tones here if needed
    }
    # Default to serious if tone is unrecognized
    return tone_map.get(tone, tone_map[ConversationSession.AiTone.SERIOUS])


def _get_system_prompt(session: ConversationSession) -> str:
    """Constructs the full system prompt including tone instructions."""
    return SYSTEM_PROMPT_BASE + "\n" + _get_tone_instruction(session.ai_tone)


# --- History Formatting ---
def _format_history_for_ai(messages: List[ConversationMessage]) -> List[Dict[str, str]]:
    """Formats message history for the AI API, respecting MAX_HISTORY_MESSAGES."""
    formatted_messages = []
    # Take the most recent messages, excluding the system prompt if it were stored here
    for msg in messages[-MAX_HISTORY_MESSAGES:]:
        role = (
            "user"
            if msg.sender_type == ConversationMessage.SenderType.USER
            else "assistant"
        )
        formatted_messages.append({"role": role, "content": msg.message_text})
    return formatted_messages


# --- Core AI Interaction Functions ---


def get_ai_response(
    session: ConversationSession,
    user_message_text: str,
    current_topic_question: Optional[Question] = None,
) -> str:
    """
    Gets a conversational response from the AI based on session history and user message.

    Args:
        session: The current ConversationSession.
        user_message_text: The latest message text from the user.
        current_topic_question: Optional Question context.

    Returns:
        The AI's generated text response, or an error message.
    """
    if not client:
        logger.error(
            f"AI Client not available for get_ai_response (Session {session.id}). Init error: {openai_init_error}"
        )
        return f"{DEFAULT_AI_ERROR_MSG}{f' (Reason: {openai_init_error})' if openai_init_error else ''}"

    try:
        system_prompt = _get_system_prompt(session)
        # Fetch history efficiently within the try block
        history = list(session.messages.order_by("timestamp").all())
        formatted_history = _format_history_for_ai(history)

        context_message = ""
        if current_topic_question:
            # Provide concise context
            q_text = current_topic_question.question_text[:150]
            context_message = f'\n\n[AI Context: We are currently discussing Question ID {current_topic_question.id}: "{q_text}..."]'

        messages_for_api = [
            {"role": "system", "content": system_prompt},
            *formatted_history,
            {"role": "user", "content": user_message_text + context_message},
        ]

        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for conversation response (Session {session.id}, Context QID: {current_topic_question.id if current_topic_question else 'None'})."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=1000,
            # Consider adding user=str(session.user.id) for monitoring/abuse prevention
            # user=str(session.user.id)
        )
        ai_response_text = response.choices[0].message.content.strip()

        if not ai_response_text:
            logger.warning(f"Received empty AI response for session {session.id}.")
            return DEFAULT_AI_SPEECHLESS_MSG

        logger.info(f"AI conversational response received for session {session.id}")
        return ai_response_text

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error during conversation response (Session {session.id}, QID: {current_topic_question.id if current_topic_question else 'None'}): {e}",
            exc_info=True,
        )
        return _(
            "I encountered an issue communicating with my brain (the AI service). Please try again shortly."
        )
    except Exception as e:
        # Log the full traceback for unexpected errors
        logger.exception(
            f"Unexpected error calling AI for conversation response (Session {session.id}, QID: {current_topic_question.id if current_topic_question else 'None'}): {e}"
        )
        return DEFAULT_AI_RESPONSE_ERROR_MSG


def select_test_question_for_concept(
    original_question: Question, user: User
) -> Optional[Question]:
    """
    Selects a different, related question to test understanding.

    Prioritizes the same skill, then the same subsection, excluding the original
    question and those recently answered correctly by the user in conversation mode.

    Args:
        original_question: The question the user just confirmed understanding of.
        user: The user interacting with the session.

    Returns:
        A suitable Question object or None if no suitable question is found.
    """
    if not original_question:
        logger.warning(
            f"select_test_question_for_concept called with no original_question for user {user.id}"
        )
        return None

    target_skill = original_question.skill
    target_subsection = original_question.subsection

    if not target_skill and not target_subsection:
        logger.warning(
            f"Original question {original_question.id} lacks both skill and subsection. Cannot select related test question."
        )
        return None

    # Get IDs of questions recently answered correctly in CONVERSATION mode
    # Limit the timeframe and number checked for performance
    recent_correct_conv_ids = (
        UserQuestionAttempt.objects.filter(
            user=user,
            is_correct=True,
            mode=UserQuestionAttempt.Mode.CONVERSATION,
            attempted_at__gte=timezone.now()
            - timezone.timedelta(days=7),  # Configurable?
        )
        .order_by("-attempted_at")
        .values_list("question_id", flat=True)[:20]
    )  # Limit check

    exclude_ids = set(recent_correct_conv_ids) | {
        original_question.id
    }  # Use set for efficiency

    test_question = None
    # Prioritize finding a question with the same skill
    if target_skill:
        test_question = (
            Question.objects.filter(skill=target_skill, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")
            .first()
        )  # Random selection

    # Fallback to the same subsection if no skill-match found
    if not test_question and target_subsection:
        logger.info(
            f"No suitable test question found for Skill ID {target_skill.id if target_skill else 'N/A'}. Falling back to Subsection ID {target_subsection.id}."
        )
        test_question = (
            Question.objects.filter(subsection=target_subsection, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")
            .first()
        )

    if test_question:
        logger.info(
            f"Selected test question {test_question.id} (Skill: {test_question.skill_id}, SubSec: {test_question.subsection_id}) related to original Q:{original_question.id} for user {user.id}."
        )
    else:
        logger.warning(
            f"No suitable *different* test question found related to original Q:{original_question.id} (Skill: {target_skill.id if target_skill else 'N/A'}, SubSec: {target_subsection.id if target_subsection else 'N/A'}) for user {user.id}."
        )

    return test_question


@transaction.atomic
def record_conversation_test_attempt(
    user: User,
    session: ConversationSession,
    test_question: Question,
    selected_answer: str,
) -> UserQuestionAttempt:
    """
    Records a user's answer to a test question presented within a conversation session.
    Uses update_or_create to handle potential re-attempts within the same session.
    Updates user skill proficiency based on the attempt outcome.

    Args:
        user: The user making the attempt.
        session: The conversation session where the test occurred.
        test_question: The Question object attempted.
        selected_answer: The user's chosen answer choice ('A', 'B', 'C', or 'D').

    Returns:
        The created or updated UserQuestionAttempt instance.

    Raises:
        ValueError: If selected_answer is invalid (although usually caught by serializer).
    """
    if selected_answer not in UserQuestionAttempt.AnswerChoice.values:
        # Should be validated upstream, but good to have a safeguard
        raise ValueError(f"Invalid answer choice '{selected_answer}' provided.")

    defaults = {
        "selected_answer": selected_answer,
        "mode": UserQuestionAttempt.Mode.CONVERSATION,
        "attempted_at": timezone.now(),
        "is_correct": None,  # Let the model's save method calculate this
    }

    # Using session in uniqueness constraint allows retrying the same question in different sessions
    attempt, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        question=test_question,
        conversation_session=session,
        defaults=defaults,
    )

    # The model's save() method should calculate is_correct based on selected_answer
    # refresh_from_db might be needed if the model's save logic doesn't update the instance in memory
    attempt.refresh_from_db(fields=["is_correct"])

    log_prefix = "Recorded" if created else "Updated"
    logger.info(
        f"{log_prefix} conversation test attempt {attempt.id} for user {user.username} (ID: {user.id}), Q:{test_question.id}, Session:{session.id}. Correct: {attempt.is_correct}"
    )

    # Update Skill Proficiency
    update_user_skill_proficiency(
        user=user, skill=test_question.skill, is_correct=attempt.is_correct
    )

    # Placeholder for gamification logic (e.g., call a gamification service or signal)
    # award_points_for_conversation_attempt(attempt)

    return attempt


@transaction.atomic
def generate_ai_question_and_message(
    session: ConversationSession, user: User
) -> Dict[str, Any]:
    """
    Selects a suitable question for the AI to ask the user, generates an
    encouraging preface message using the AI, saves the AI message, and returns
    the preface and question details.

    Args:
        session: The current ConversationSession.
        user: The user the question is for.

    Returns:
        A dictionary containing:
            - "ai_message": str (The AI-generated preface/cheer message)
            - "question": Question (The selected Question object)

    Raises:
        ObjectDoesNotExist: If no suitable question can be found.
        ValueError: If the AI client is not available.
    """
    if not client:
        logger.error(
            f"AI Client not available for generate_ai_question (Session {session.id}). Init error: {openai_init_error}"
        )
        raise ValueError(
            f"{DEFAULT_AI_ERROR_MSG}{f' (Reason: {openai_init_error})' if openai_init_error else ''}"
        )

    # 1. Select a Question
    # Get IDs of questions already asked or tested in this specific session to avoid repetition
    session_q_ids = set(
        session.messages.filter(related_question__isnull=False).values_list(
            "related_question_id", flat=True
        )
    )
    session_attempt_q_ids = set(
        UserQuestionAttempt.objects.filter(conversation_session=session).values_list(
            "question_id", flat=True
        )
    )
    exclude_ids = list(session_q_ids | session_attempt_q_ids)

    # Prioritize questions where the user is not proficient
    selected_question = get_filtered_questions(
        user=user, limit=1, not_mastered=True, exclude_ids=exclude_ids
    ).first()

    if not selected_question:
        logger.info(
            f"No 'not_mastered' question found for ask-question (Session {session.id}, User {user.id}). Trying random suitable question."
        )
        # Fallback: Get any suitable question not already used in this session
        selected_question = get_filtered_questions(
            user=user, limit=1, exclude_ids=exclude_ids
        ).first()

    if not selected_question:
        logger.error(
            f"Could not find any suitable question for ask-question (Session {session.id}, User {user.id}). Excluded IDs: {exclude_ids}"
        )
        raise ObjectDoesNotExist(
            _("Could not find a suitable question to ask at this time.")
        )

    logger.info(
        f"Selected Q:{selected_question.id} for AI to ask in session {session.id} for user {user.id}."
    )

    # 2. Generate AI Cheer Message
    skill_name = (
        selected_question.skill.name if selected_question.skill else "a relevant topic"
    )
    subsection_name = (
        selected_question.subsection.name
        if selected_question.subsection
        else "a key area"
    )
    topic_context = skill_name if selected_question.skill else subsection_name

    prompt_for_cheer = f"""
    The user wants you to ask them a practice question.
    The question is about the topic: '{topic_context}'.
    Its text starts with: "{selected_question.question_text[:100]}..."
    Generate a short, encouraging message ({session.ai_tone} tone) to preface this question.
    Keep the message brief (1-2 sentences maximum).
    DO NOT include the question text itself or the options in your generated message, only the preface.
    Example ({ConversationSession.AiTone.CHEERFUL} tone): "Alright! Let's test your skills with this one... ✨"
    Example ({ConversationSession.AiTone.SERIOUS} tone): "Okay, let's try a question on this topic."
    """

    ai_cheer_message_text = _(
        "Okay, let's try this practice question:"
    )  # Default fallback

    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for cheer message (Session {session.id}, Q:{selected_question.id})"
        )
        system_prompt = _get_system_prompt(session)
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_for_cheer},
            ],
            temperature=0.8,  # Slightly more creative for cheer
            max_tokens=100,
            # user=str(user.id)
        )
        generated_text = response.choices[0].message.content.strip()
        if generated_text:
            ai_cheer_message_text = generated_text
        else:
            logger.warning(
                f"Received empty AI cheer message for session {session.id}, Q:{selected_question.id}. Using fallback."
            )

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error generating cheer message for session {session.id}, Q:{selected_question.id}: {e}",
            exc_info=True,
        )
        # Use fallback message
    except Exception as e:
        logger.exception(
            f"Unexpected error generating AI cheer message for session {session.id}, Q:{selected_question.id}: {e}"
        )
        # Use fallback message

    # 3. Save AI Message (preface only) linked to the Question
    ai_msg = ConversationMessage.objects.create(
        session=session,
        sender_type=ConversationMessage.SenderType.AI,
        message_text=ai_cheer_message_text,
        related_question=selected_question,  # Link the question AI intends to present
    )
    logger.info(
        f"AI 'ask-question' preface message saved (ID: {ai_msg.id}) for session {session.id}, linking Q:{selected_question.id}"
    )

    # 4. Update session context
    # This indicates the question the *user* is expected to be looking at or answering next
    session.current_topic_question = selected_question
    session.save(update_fields=["current_topic_question", "updated_at"])

    # 5. Prepare data for the API response (Serializer will handle Question object)
    return {
        "ai_message": ai_cheer_message_text,
        "question": selected_question,
    }


# --- AI-Powered Message Processing and Feedback ---


def process_user_message_with_ai(
    session: ConversationSession,
    user_message_text: str,
    current_topic_question: Optional[Question] = None,
) -> Dict[str, Any]:
    """
    Uses AI to analyze user message intent (answer vs. conversation) and generates a response.

    If a `current_topic_question` is provided, the AI determines if the user's
    message is likely an answer choice (A, B, C, D).
    - If it IS an answer: Returns structured data with `processed_as_answer=True`,
      the detected choice, and AI-generated feedback (hint or confirmation).
    - If it is NOT an answer (or no question context): Returns structured data
      with `processed_as_answer=False` and a standard AI conversational response.

    Relies on the AI's ability to follow instructions and return valid JSON.

    Args:
        session: The current ConversationSession.
        user_message_text: The user's latest message text.
        current_topic_question: The question the user might be answering.

    Returns:
        Dict: {
            "processed_as_answer": bool,
            "user_choice": Optional[str], # 'A', 'B', 'C', 'D' or None
            "feedback_text": str # AI response/hint/confirmation
        }
    """
    fallback_error_response = {
        "processed_as_answer": False,
        "user_choice": None,
        "feedback_text": _(
            "Sorry, I encountered an issue processing that. Could you try again?"
        ),
    }

    if not client:
        logger.error(
            f"AI Client not available for process_user_message (Session {session.id}). Init error: {openai_init_error}"
        )
        return {
            **fallback_error_response,
            "feedback_text": f"{DEFAULT_AI_ERROR_MSG}{f' (Reason: {openai_init_error})' if openai_init_error else ''}",
        }

    # 1. Prepare Context & Prompt Engineering for JSON Output
    system_prompt = _get_system_prompt(session)
    history = list(session.messages.order_by("timestamp").all())
    formatted_history = _format_history_for_ai(history)

    # --- Build the instruction prompt ---
    instruction_parts = [
        f"Analyze the latest user message: '{user_message_text}'",
        "Determine the user's intent based on the message and the current context (if any).",
        "Your response MUST be a valid JSON object with the following keys:",
        "  - `processed_as_answer`: boolean (true if the message is primarily an answer choice like 'A', 'b.', 'answer is C', etc. for the current question; false otherwise).",
        "  - `user_choice`: string (The detected answer choice 'A', 'B', 'C', or 'D' if processed_as_answer is true, otherwise null).",
        "  - `feedback_text`: string (Your generated response message).",
    ]

    if current_topic_question:
        correct_letter = current_topic_question.correct_answer
        explanation_snippet = (
            current_topic_question.explanation or "No explanation available."
        )[:200]
        q_text_snippet = current_topic_question.question_text[:200]
        options_snippet = f"A) {current_topic_question.option_a[:50]}... B) {current_topic_question.option_b[:50]}... C) {current_topic_question.option_c[:50]}... D) {current_topic_question.option_d[:50]}..."

        current_q_context = f"""
[Current Question Context (ID {current_topic_question.id}):
Text Snippet: "{q_text_snippet}..."
Options Snippet: {options_snippet}
Correct Answer Letter: '{correct_letter}']
"""
        instruction_parts.append(current_q_context)
        instruction_parts.append(f"Instructions:")
        instruction_parts.append(
            f"1. Check if the user message is likely an answer choice (A, B, C, D) for THIS question."
        )
        instruction_parts.append(f"2. If YES (it's an answer choice):")
        instruction_parts.append(f"   - Set `processed_as_answer` to true.")
        instruction_parts.append(
            f"   - Set `user_choice` to the detected letter (A, B, C, or D)."
        )
        instruction_parts.append(f"   - Compare detected choice to '{correct_letter}'.")
        instruction_parts.append(f"   - Generate `feedback_text`:")
        instruction_parts.append(
            f"     - If correct: Brief, positive confirmation ({session.ai_tone} tone)."
        )
        instruction_parts.append(
            f"     - If incorrect: A guiding hint ({session.ai_tone} tone) based on the concept or explanation ('{explanation_snippet}...'). DO NOT reveal the correct answer letter ('{correct_letter}') in the hint."
        )
        instruction_parts.append(
            f"3. If NO (it's conversational, a question, unrelated, etc.):"
        )
        instruction_parts.append(f"   - Set `processed_as_answer` to false.")
        instruction_parts.append(f"   - Set `user_choice` to null.")
        instruction_parts.append(
            f"   - Generate `feedback_text`: A helpful conversational response ({session.ai_tone} tone) addressing the user's message, considering the history and question context."
        )
    else:
        # No current question context - treat as purely conversational
        instruction_parts.append("[No specific question context active.]")
        instruction_parts.append(f"Instructions:")
        instruction_parts.append(
            f"1. The message is NOT an answer choice to a specific question."
        )
        instruction_parts.append(f"2. Set `processed_as_answer` to false.")
        instruction_parts.append(f"3. Set `user_choice` to null.")
        instruction_parts.append(
            f"4. Generate `feedback_text`: A helpful conversational response ({session.ai_tone} tone) to the user's message, considering the history."
        )

    instruction_parts.append("\nEnsure the output is ONLY the JSON object.")
    final_instruction = "\n".join(instruction_parts)

    messages_for_api = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {
            "role": "user",
            "content": final_instruction,
        },  # Use the detailed instruction prompt
    ]

    # 2. Call AI API - Request JSON output if model supports it reliably
    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for intent analysis/response (Session {session.id}, QID: {current_topic_question.id if current_topic_question else 'None'}). Requesting JSON."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.5,  # Lower temp for better instruction following
            max_tokens=500,  # Adjust as needed for feedback length
            response_format={
                "type": "json_object"
            },  # Explicitly request JSON object output
            # user=str(session.user.id)
        )
        ai_response_content = response.choices[0].message.content

        # 3. Parse and Validate JSON response
        try:
            parsed_json = json.loads(ai_response_content)

            # Validate structure and types
            processed_as_answer = parsed_json.get("processed_as_answer")
            user_choice = parsed_json.get("user_choice")
            feedback_text = parsed_json.get("feedback_text")

            if not isinstance(processed_as_answer, bool) or not isinstance(
                feedback_text, str
            ):
                raise ValueError("Invalid types in JSON response.")
            if (
                processed_as_answer
                and user_choice not in UserQuestionAttempt.AnswerChoice.values
            ):
                logger.warning(
                    f"AI returned processed_as_answer=true but invalid user_choice '{user_choice}' (Session {session.id}). Treating as non-answer. JSON: {ai_response_content}"
                )
                # Fallback: Treat as conversational if choice is invalid
                processed_as_answer = False
                user_choice = None
                # TODO: Optionally, make another AI call here for a purely conversational response?
                # For simplicity now, we might return the potentially confusing feedback text or a generic message.
                feedback_text = _(
                    "Thanks for your input! Let's continue our discussion."
                )  # Generic fallback
            elif not processed_as_answer:
                user_choice = None  # Ensure choice is null if not processed as answer

            logger.info(
                f"AI JSON response parsed successfully for session {session.id}. Processed as answer: {processed_as_answer}, Choice: {user_choice}"
            )
            return {
                "processed_as_answer": processed_as_answer,
                "user_choice": user_choice,
                "feedback_text": feedback_text,
            }

        except (json.JSONDecodeError, ValueError, KeyError) as json_err:
            logger.error(
                f"Failed to parse or validate AI JSON response (Session {session.id}). Error: {json_err}. Response: '{ai_response_content}'",
                exc_info=True,
            )
            # Attempt a standard conversational response as a fallback
            logger.info(
                f"Falling back to standard conversational AI response for session {session.id}."
            )
            fallback_text = get_ai_response(
                session, user_message_text, current_topic_question
            )
            return {
                **fallback_error_response,
                "feedback_text": fallback_text,
            }  # Return standard response

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error processing message (Session {session.id}): {e}",
            exc_info=True,
        )
        return {
            **fallback_error_response,
            "feedback_text": _(
                "Sorry, I couldn't connect to my core AI service right now."
            ),
        }
    except Exception as e:
        logger.exception(
            f"Unexpected error processing message with AI (Session {session.id}): {e}"
        )
        return fallback_error_response


def get_ai_feedback_on_answer(
    session: ConversationSession,
    attempt: UserQuestionAttempt,
) -> str:
    """
    Generates detailed feedback from the AI for an explicitly submitted answer,
    using JSON mode for reliable output structure.

    Args:
        session: The ConversationSession context.
        attempt: The UserQuestionAttempt containing the question, user's answer, and correctness.

    Returns:
        A string containing the AI-generated feedback message.
    """
    default_feedback = _("Answer recorded.")
    if not client:
        logger.error(
            f"AI Client not available for get_ai_feedback_on_answer (Session {session.id}, Attempt {attempt.id}). Init error: {openai_init_error}"
        )
        return f"{default_feedback} {DEFAULT_AI_ERROR_MSG}{f' (Reason: {openai_init_error})' if openai_init_error else ''}"

    question = attempt.question
    is_correct = (
        attempt.is_correct
    )  # Assumes is_correct is already determined and saved
    user_answer = attempt.selected_answer
    correct_answer = question.correct_answer
    explanation = question.explanation or _("No detailed explanation available.")

    # This should not happen if called after recording, but check anyway
    if is_correct is None:
        logger.error(
            f"Cannot generate AI feedback for attempt {attempt.id}: is_correct is None."
        )
        return _(
            "Answer recorded, but correctness could not be determined for feedback."
        )

    # Define the desired JSON structure and instructions for the AI
    json_instruction_prompt = f"""
    Analyze the user's attempt and generate feedback in JSON format.
    Context:
      - Question ID: {question.id}
      - Question Text Snippet: "{question.question_text[:150]}..."
      - User's Answer: '{user_answer}'
      - Correct Answer: '{correct_answer}'
      - Was User Correct?: {is_correct}
      - Explanation Snippet: "{explanation[:300]}..."
      - Required Tone: {session.ai_tone}

    Your response MUST be a valid JSON object containing EXACTLY ONE key:
      `feedback_text`: string (The detailed feedback message for the user).

    Instructions for `feedback_text`:
    - If the user was correct (Was User Correct? is True):
        - Provide an encouraging confirmation ({session.ai_tone} tone).
        - Briefly reinforce *why* the answer '{correct_answer}' is correct, using the Explanation Snippet.
    - If the user was incorrect (Was User Correct? is False):
        - Provide constructive feedback ({session.ai_tone} tone).
        - State the correct answer was '{correct_answer}'.
        - Explain *why* '{correct_answer}' is correct, using the Explanation Snippet. Keep it helpful.

    Example Correct ({ConversationSession.AiTone.CHEERFUL}): {{"feedback_text": "Excellent! 😎 '{correct_answer}' is exactly right because [brief reason from explanation]..."}}
    Example Incorrect ({ConversationSession.AiTone.SERIOUS}): {{"feedback_text": "Not quite. The correct answer was '{correct_answer}'. This is because [explanation based on snippet]..."}}

    Output ONLY the JSON object.
    """

    messages_for_api = [
        {"role": "system", "content": _get_system_prompt(session)},
        {"role": "user", "content": json_instruction_prompt},
    ]

    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for JSON answer feedback (Session {session.id}, Attempt {attempt.id})."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.6,
            max_tokens=350,  # Allow enough for good feedback
            response_format={"type": "json_object"},  # Use JSON mode
            # user=str(session.user.id)
        )
        ai_response_content = response.choices[0].message.content

        # Parse JSON response
        try:
            parsed_json = json.loads(ai_response_content)
            ai_feedback_text = parsed_json.get("feedback_text")

            if not ai_feedback_text or not isinstance(ai_feedback_text, str):
                logger.error(
                    f"AI returned valid JSON but 'feedback_text' missing or invalid type for attempt {attempt.id}. JSON: {ai_response_content}"
                )
                # Provide a simple fallback confirming correctness
                ai_feedback_text = _("Answer recorded. Correct: {is_correct}.").format(
                    is_correct=is_correct
                )
            else:
                logger.info(
                    f"AI JSON feedback parsed successfully for attempt {attempt.id}"
                )

            return ai_feedback_text

        except (json.JSONDecodeError, KeyError, ValueError) as json_err:
            logger.error(
                f"Failed to parse or validate AI JSON feedback response for attempt {attempt.id}. Error: {json_err}. Response: '{ai_response_content}'",
                exc_info=True,
            )
            # Fallback indicating technical difficulty
            return _(
                "Answer recorded. I had a little trouble formatting my detailed feedback!"
            )

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error getting JSON feedback for attempt {attempt.id}: {e}",
            exc_info=True,
        )
        return _(
            "Answer recorded. I had trouble generating detailed feedback this time."
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error getting AI JSON feedback for attempt {attempt.id}: {e}"
        )
        # Generic fallback if something else went wrong
        return (
            default_feedback
            + " "
            + _("Could not generate detailed feedback due to an unexpected issue.")
        )
