import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.db import transaction
from django.utils import timezone

# --- Placeholder for Actual AI Client ---
# from openai import OpenAI # Example
# client = OpenAI(api_key=settings.OPENAI_API_KEY)
# ---

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill
from apps.users.models import (
    UserProfile,
)  # Assuming User model is settings.AUTH_USER_MODEL
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Constants ---
AI_MODEL = "gpt-3.5-turbo"  # Or your preferred model
MAX_HISTORY_MESSAGES = 10  # Limit context window

SYSTEM_PROMPT_BASE = """
You are Qader AI, a helpful and encouraging AI assistant for students preparing for the Qudurat test (Saudi Arabia's aptitude test).
Your goal is to help students understand concepts, practice questions, and build confidence.
Focus on the Verbal (اللفظي) and Quantitative (الكمي) sections.
Keep your explanations clear, concise, and step-by-step.
Maintain a positive and motivating tone appropriate for the user's selected preference.
If asked about a specific question, use the provided database information if possible.
When the user indicates understanding ('Got it'), prepare to test them on a related concept.
"""


def _get_tone_instruction(tone: str) -> str:
    """Returns specific tone instructions for the system prompt."""
    if tone == ConversationSession.AiTone.CHEERFUL:
        return "Use a cheerful, friendly, and slightly informal tone. Use emojis appropriately to convey encouragement (e.g., 😎, ✨, 👍)."
    else:  # Default to serious
        return "Maintain a professional, encouraging, but more formal and direct tone."


def _format_history_for_ai(messages: List[ConversationMessage]) -> List[Dict[str, str]]:
    """Formats message history for the AI API."""
    formatted_messages = []
    for msg in messages[-MAX_HISTORY_MESSAGES:]:  # Get recent history
        role = (
            "user"
            if msg.sender_type == ConversationMessage.SenderType.USER
            else "assistant"
        )
        formatted_messages.append({"role": role, "content": msg.message_text})
    return formatted_messages


def get_ai_response(session: ConversationSession, user_message_text: str) -> str:
    """
    Gets a response from the AI based on the session history and new user message.
    Handles interaction with the external AI service.
    """
    # 1. Prepare context
    system_prompt = SYSTEM_PROMPT_BASE + "\n" + _get_tone_instruction(session.ai_tone)
    history = list(
        session.messages.order_by("timestamp").all()
    )  # Fetch ordered history
    formatted_history = _format_history_for_ai(history)

    messages_for_api = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {"role": "user", "content": user_message_text},
    ]

    # 2. Call AI API (Replace with your actual client call)
    try:
        logger.info(
            f"Calling AI for session {session.id} with {len(messages_for_api)} messages."
        )
        # --- Placeholder Call ---
        # response = client.chat.completions.create(
        #     model=AI_MODEL,
        #     messages=messages_for_api
        # )
        # ai_response_text = response.choices[0].message.content.strip()
        # --- Mock Response ---
        ai_response_text = f"Mock AI Response ({session.ai_tone}): Got it! You said '{user_message_text}'. Let's explore that further."
        if "error" in user_message_text.lower():
            raise ValueError("Simulated AI Error")
        # --- End Placeholder ---

        logger.info(f"AI response received for session {session.id}")
        return ai_response_text

    except Exception as e:
        logger.error(f"Error calling AI for session {session.id}: {e}", exc_info=True)
        # Fallback response
        return _(
            "I encountered an issue processing your request. Please try again shortly."
        )


def select_test_question_for_concept(
    original_question: Question, user: User
) -> Optional[Question]:
    """
    Selects a *different* question related to the same skill/subsection
    to test the user's understanding after they say "Got it".
    Avoids questions the user recently answered correctly.
    """
    if not original_question or not original_question.skill:
        logger.warning(
            f"Cannot select test question: Original question {original_question.id if original_question else 'None'} or its skill is missing."
        )
        return None

    target_skill = original_question.skill
    target_subsection = original_question.subsection

    # Get IDs of questions user recently answered correctly (e.g., last 20 attempts)
    recently_correct_ids = list(
        UserQuestionAttempt.objects.filter(
            user=user,
            is_correct=True,
            mode=UserQuestionAttempt.Mode.CONVERSATION,  # Or consider other modes?
        )
        .order_by("-attempted_at")
        .values_list("question_id", flat=True)[:20]
    )

    # Find a suitable question: same skill, different ID, not recently correct
    test_question = (
        Question.objects.filter(
            skill=target_skill, subsection=target_subsection, is_active=True
        )
        .exclude(id=original_question.id)
        .exclude(id__in=recently_correct_ids)
        .order_by("?")
        .first()
    )  # Random suitable question

    if not test_question:
        logger.warning(
            f"No suitable *different* test question found for skill {target_skill.name} (original Q: {original_question.id})."
        )
        # Fallback: maybe try subsection level? Or return None.
        test_question = (
            Question.objects.filter(subsection=target_subsection, is_active=True)
            .exclude(id=original_question.id)
            .exclude(id__in=recently_correct_ids)
            .order_by("?")
            .first()
        )

    logger.info(
        f"Selected test question {test_question.id if test_question else 'None'} for original question {original_question.id}"
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
    Records the user's answer to the test question presented in the conversation.
    Updates user skill proficiency.
    """
    attempt = UserQuestionAttempt.objects.create(
        user=user,
        question=test_question,
        selected_answer=selected_answer,
        mode=UserQuestionAttempt.Mode.CONVERSATION,
        # test_attempt = None # Not linked to a full test session
        attempted_at=timezone.now(),
        # is_correct will be calculated on save
    )
    # attempt.save() is called implicitly by create, calculating is_correct

    logger.info(
        f"Recorded conversation test attempt {attempt.id} for user {user.username}, question {test_question.id}. Correct: {attempt.is_correct}"
    )

    # Update Skill Proficiency
    if test_question.skill:
        proficiency, created = UserSkillProficiency.objects.get_or_create(
            user=user, skill=test_question.skill
        )
        proficiency.record_attempt(is_correct=attempt.is_correct)
        logger.info(
            f"Updated skill proficiency for user {user.username}, skill {test_question.skill.name}. New score: {proficiency.proficiency_score:.2f}"
        )

    # Award points (using gamification service if available)
    # try:
    #     from apps.gamification.services import award_points # Example
    #     award_points(user, 'CONVERSATION_TEST_CORRECT' if attempt.is_correct else 'CONVERSATION_TEST_ATTEMPT', related_object=attempt)
    # except ImportError:
    #      logger.warning("Gamification service not found, skipping points for conversation test.")
    # except Exception as e:
    #      logger.error(f"Error awarding points for conversation test attempt {attempt.id}: {e}")

    return attempt
