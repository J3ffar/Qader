import logging
from typing import List, Optional, Dict, Any
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from openai import OpenAI, OpenAIError  # Import OpenAI client and errors
from django.core.exceptions import ObjectDoesNotExist


from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
    UserSkillProficiency,
)
from apps.learning.models import Question, Skill
from apps.users.models import UserProfile
from django.contrib.auth import get_user_model
from .services import get_filtered_questions  # Import question filtering service

User = get_user_model()
logger = logging.getLogger(__name__)

# --- AI Client Initialization ---
try:
    if settings.OPENAI_API_KEY:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    else:
        client = None
        logger.warning("OPENAI_API_KEY not configured. AI features will be disabled.")
except Exception as e:
    client = None
    logger.exception(f"Failed to initialize OpenAI client: {e}")
# ---

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
Do not reveal answers or detailed solutions unless explicitly asked or when explaining a concept the user struggled with.
When asked to provide a question, give a motivational message first, then clearly state the question.
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
    # Get recent history, potentially filtering system messages if needed
    for msg in messages[-MAX_HISTORY_MESSAGES:]:
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
    if not client:
        logger.error(f"AI Client not available for session {session.id}.")
        return _(
            "Sorry, the AI assistant is currently unavailable. Please try again later."
        )

    # 1. Prepare context
    system_prompt = SYSTEM_PROMPT_BASE + "\n" + _get_tone_instruction(session.ai_tone)
    # Fetch history *before* the current user message is saved
    history = list(session.messages.order_by("timestamp").all())
    formatted_history = _format_history_for_ai(history)

    messages_for_api = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {"role": "user", "content": user_message_text},  # Include the new user message
    ]

    # 2. Call AI API
    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for session {session.id} with {len(messages_for_api)} messages."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.7,  # Adjust creativity/focus
            max_tokens=1000,  # Limit response length
            # Add user identifier for moderation/tracking if needed
            # user=str(session.user.id)
        )
        ai_response_text = response.choices[0].message.content.strip()

        # Basic check for empty response
        if not ai_response_text:
            logger.warning(f"Received empty AI response for session {session.id}.")
            ai_response_text = _("I seem to be speechless! Could you try rephrasing?")

        logger.info(f"AI response received for session {session.id}")
        return ai_response_text

    except OpenAIError as e:
        logger.error(f"OpenAI API error for session {session.id}: {e}", exc_info=True)
        # More specific error messages based on e.type if needed
        return _(
            "I encountered an issue communicating with my brain (the AI service). Please try again shortly."
        )
    except Exception as e:
        logger.exception(f"Unexpected error calling AI for session {session.id}: {e}")
        return _(
            "An unexpected error occurred while generating my response. Please try again."
        )


def select_test_question_for_concept(
    original_question: Question, user: User
) -> Optional[Question]:
    """
    Selects a *different* question related to the same skill/subsection
    to test the user's understanding after they say "Got it".
    Avoids questions the user recently answered correctly in this mode.
    """
    if not original_question:
        logger.warning("Cannot select test question: Original question is missing.")
        return None

    target_skill = original_question.skill
    target_subsection = original_question.subsection

    if not target_skill and not target_subsection:
        logger.warning(
            f"Cannot select test question: Original question {original_question.id} has no skill or subsection."
        )
        return None

    # Get IDs of questions user recently answered correctly in CONVERSATION mode
    recent_correct_conv_ids = list(
        UserQuestionAttempt.objects.filter(
            user=user,
            is_correct=True,
            mode=UserQuestionAttempt.Mode.CONVERSATION,
            attempted_at__gte=timezone.now()
            - timezone.timedelta(days=7),  # Limit to last 7 days?
        )
        .order_by("-attempted_at")
        .values_list("question_id", flat=True)[:20]  # Limit check further
    )
    exclude_ids = recent_correct_conv_ids + [original_question.id]

    # Prioritize same skill, then same subsection
    test_question = None
    if target_skill:
        test_question = (
            Question.objects.filter(skill=target_skill, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")  # Random suitable question
            .first()
        )

    if not test_question and target_subsection:
        logger.info(
            f"No suitable test question found for skill {target_skill.name if target_skill else 'N/A'}. Falling back to subsection {target_subsection.name}."
        )
        test_question = (
            Question.objects.filter(subsection=target_subsection, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")
            .first()
        )

    if not test_question:
        logger.warning(
            f"No suitable *different* test question found for original Q: {original_question.id} (Skill: {target_skill}, SubSection: {target_subsection})."
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
    Updates user skill proficiency. Uses update_or_create.
    """
    defaults = {
        "selected_answer": selected_answer,
        "mode": UserQuestionAttempt.Mode.CONVERSATION,
        "conversation_session": session,
        "attempted_at": timezone.now(),
        # is_correct will be calculated on save by the model if None initially
        "is_correct": None,
    }

    # Allow user to retry the same question within the same conversation session if needed
    attempt, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        question=test_question,
        conversation_session=session,  # Uniqueness constraint includes session
        defaults=defaults,
    )

    # Model's save() should have calculated is_correct. Refresh to be sure.
    attempt.refresh_from_db(fields=["is_correct"])

    logger.info(
        f"{'Recorded' if created else 'Updated'} conversation test attempt {attempt.id} for user {user.username}, Q {test_question.id}. Correct: {attempt.is_correct}"
    )

    # Update Skill Proficiency only if the answer was correctly determined
    if attempt.is_correct is not None and test_question.skill:
        try:
            proficiency, p_created = UserSkillProficiency.objects.get_or_create(
                user=user, skill=test_question.skill
            )
            proficiency.record_attempt(is_correct=attempt.is_correct)
            logger.info(
                f"Updated skill proficiency for user {user.username}, skill {test_question.skill.name}. New score: {proficiency.proficiency_score:.2f}"
            )
        except Exception as e:
            logger.exception(
                f"Error updating skill proficiency during conversation test attempt {attempt.id}: {e}"
            )

    # Award points (using gamification service if available)
    # ... (keep existing gamification logic) ...

    return attempt


# --- NEW SERVICE FUNCTION ---
@transaction.atomic
def generate_ai_question_and_message(
    session: ConversationSession, user: User
) -> Dict[str, Any]:
    """
    Selects a question for the AI to ask, generates a cheer message,
    saves the AI message, and returns data for the API response.
    """
    if not client:
        logger.error(
            f"AI Client not available for ask-question in session {session.id}."
        )
        raise ValueError(_("Sorry, the AI assistant is currently unavailable."))

    # 1. Select a Question
    # Strategy: Find a question from a skill the user is weak in or hasn't tried much.
    # Use the existing filtering logic, perhaps targeting 'not_mastered'.
    # Avoid questions already asked in this session or recently answered correctly.

    # Get questions already mentioned or tested in this specific session
    session_question_ids = list(
        ConversationMessage.objects.filter(
            session=session, related_question__isnull=False
        )
        .values_list("related_question_id", flat=True)
        .distinct()
    )
    session_test_attempt_ids = list(
        UserQuestionAttempt.objects.filter(conversation_session=session)
        .values_list("question_id", flat=True)
        .distinct()
    )
    exclude_ids = list(set(session_question_ids + session_test_attempt_ids))

    # Try finding a 'not_mastered' question first
    selected_question = get_filtered_questions(
        user=user, limit=1, not_mastered=True, exclude_ids=exclude_ids
    ).first()

    if not selected_question:
        logger.info(
            f"No 'not_mastered' question found for ask-question session {session.id}. Trying random."
        )
        # Fallback: Get any random question not recently excluded
        selected_question = get_filtered_questions(
            user=user, limit=1, exclude_ids=exclude_ids
        ).first()

    if not selected_question:
        logger.error(
            f"Could not find any suitable question for ask-question session {session.id}."
        )
        raise ObjectDoesNotExist(
            _("Could not find a suitable question to ask at this time.")
        )

    # 2. Generate AI Cheer Message using the selected question context
    prompt_for_cheer = f"""
    The user wants you to ask them a practice question.
    The question is about the topic: '{selected_question.skill.name if selected_question.skill else selected_question.subsection.name}'.
    Its text is: "{selected_question.question_text}"
    Generate a short, encouraging message ({session.ai_tone} tone) to preface this question.
    Keep the message brief (1-2 sentences). Do NOT include the question text itself in your generated message, just the cheer.
    """

    ai_cheer_message_text = _("Let's try this one!")  # Default fallback

    try:
        logger.info(
            f"Calling OpenAI for cheer message (ask-question) session {session.id}."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_BASE
                    + "\n"
                    + _get_tone_instruction(session.ai_tone),
                },
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
            logger.warning(f"Received empty AI cheer message for session {session.id}.")

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error generating cheer message for session {session.id}: {e}",
            exc_info=True,
        )
        # Use fallback message
    except Exception as e:
        logger.exception(
            f"Unexpected error generating AI cheer message for session {session.id}: {e}"
        )
        # Use fallback message

    # 3. Save AI Message linked to the Question
    ai_msg = ConversationMessage.objects.create(
        session=session,
        sender_type=ConversationMessage.SenderType.AI,
        message_text=ai_cheer_message_text,  # Save the generated cheer
        related_question=selected_question,  # Link the question the AI is about to present
    )
    logger.info(
        f"AI 'ask-question' message saved (ID: {ai_msg.id}) for session {session.id}, linking Q:{selected_question.id}"
    )

    # 4. Update session context (optional, depends on desired flow)
    session.current_topic_question = selected_question
    session.save(update_fields=["current_topic_question", "updated_at"])

    # 5. Prepare data for the serializer
    return {
        "ai_message": ai_cheer_message_text,
        "question": selected_question,  # Pass the full Question object
    }
