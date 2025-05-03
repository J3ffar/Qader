import json
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
client = None
openai_init_error = None

try:
    if settings.OPENAI_API_KEY:
        kwargs = {"api_key": settings.OPENAI_API_KEY}
        # Check if a custom base URL is provided in settings
        if settings.OPENAI_API_BASE_URL:
            kwargs["base_url"] = settings.OPENAI_API_BASE_URL
            logger.info(
                f"Initializing OpenAI client with custom base URL: {settings.OPENAI_API_BASE_URL}"
            )
        else:
            logger.info("Initializing OpenAI client with default base URL.")

        client = OpenAI(**kwargs)
        # Optional: You could add a simple ping or model list check here if needed
        # client.models.list()
    else:
        openai_init_error = (
            "OPENAI_API_KEY not configured. AI features will be disabled."
        )
        logger.warning(openai_init_error)
except Exception as e:
    openai_init_error = f"Failed to initialize OpenAI client: {e}"
    logger.exception(openai_init_error)
# ---

# --- Constants ---
AI_MODEL = settings.AI_MODEL  # Or your preferred model
MAX_HISTORY_MESSAGES = settings.MAX_HISTORY_MESSAGES  # Limit context window

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


def get_ai_response(
    session: ConversationSession,
    user_message_text: str,
    current_topic_question: Optional[Question] = None,
) -> str:
    """
    Gets a response from the AI based on session history, new user message,
    and optional current question context.
    *** Assumes this is called when the message is NOT an implicit answer. ***
    """
    if not client:
        logger.error(
            f"AI Client not available for session {session.id}. Init error: {openai_init_error}"
        )
        error_msg = _(
            "Sorry, the AI assistant is currently unavailable. Please try again later."
        )
        if openai_init_error:
            error_msg += (
                f" (Reason: {openai_init_error})"  # Provide more context if possible
            )
        return error_msg

    # 1. Prepare context
    system_prompt = SYSTEM_PROMPT_BASE + "\n" + _get_tone_instruction(session.ai_tone)
    history = list(session.messages.order_by("timestamp").all())
    formatted_history = _format_history_for_ai(history)

    # Add context about the current question if provided
    context_message = ""
    if current_topic_question:
        context_message = f'\n\n[AI Context: We are currently discussing Question ID {current_topic_question.id}: "{current_topic_question.question_text[:150]}..."]'  # Add truncated question text

    messages_for_api = [
        {"role": "system", "content": system_prompt},
        *formatted_history,
        {
            "role": "user",
            "content": user_message_text + context_message,
        },  # Append context to the user message
    ]

    # 2. Call AI API (keep existing try/except block)
    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for session {session.id} with context QID: {current_topic_question.id if current_topic_question else 'None'}."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=1000,
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
        logger.error(
            f"OpenAI API error for session {session.id} (context QID: {current_topic_question.id if current_topic_question else 'None'}): {e}",
            exc_info=True,
        )
        return _(
            "I encountered an issue communicating with my brain (the AI service). Please try again shortly."
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error calling AI for session {session.id} (context QID: {current_topic_question.id if current_topic_question else 'None'}): {e}"
        )
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
            f"AI Client not available for ask-question in session {session.id}. Init error: {openai_init_error}"
        )
        error_msg = _("Sorry, the AI assistant is currently unavailable.")
        if openai_init_error:
            error_msg += f" (Reason: {openai_init_error})"
        raise ValueError(error_msg)

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


@transaction.atomic
def handle_implicit_answer(
    session: ConversationSession,
    user: User,
    question: Question,
    submitted_answer_choice: str,
) -> str:
    """
    Handles implicit answers. Records attempt, instructs AI to generate JSON feedback
    (hint or confirmation), parses JSON, and returns the feedback text.
    """
    # Default fallback message in case of errors
    default_response = _("Got it. Thinking...")

    if not client:
        logger.error(
            f"AI Client not available for implicit answer handling in session {session.id}."
        )
        return _(
            "Your answer has been noted, but I couldn't generate feedback right now."
        )

    # 1. Record the attempt (same as before)
    attempt, created = UserQuestionAttempt.objects.update_or_create(
        user=user,
        question=question,
        conversation_session=session,
        defaults={
            "selected_answer": submitted_answer_choice,
            "mode": UserQuestionAttempt.Mode.CONVERSATION,
            "attempted_at": timezone.now(),
            "is_correct": None,
        },
    )
    attempt.refresh_from_db(fields=["is_correct"])
    is_correct = attempt.is_correct  # Backend knows the actual correctness

    logger.info(
        f"{'Recorded' if created else 'Updated'} implicit answer attempt {attempt.id} for Q {question.id}. Correct: {is_correct}"
    )

    # 2. Generate AI Hint/Guidance Prompt requesting JSON
    correct_answer = question.correct_answer
    explanation_snippet = (question.explanation or "")[:200]

    # Define the desired JSON structure
    json_structure_notes = """
    Your response MUST be a valid JSON object containing EXACTLY these two keys:
    1.  `is_correct`: boolean (true if the user's answer was correct, false otherwise). Use the value {is_correct_bool}.
    2.  `feedback_text`: string (the feedback, hint, or confirmation message for the user in {tone} tone).
    Example Correct: {{"is_correct": true, "feedback_text": "That's right! Feeling confident?"}}
    Example Incorrect: {{"is_correct": false, "feedback_text": "Not quite. Think about the concept of X. Want to try again?"}}
    """.format(
        is_correct_bool=str(is_correct).lower(), tone=session.ai_tone
    )  # Pass actual correctness to guide AI

    if is_correct:
        instruction = f"""
        The user correctly answered '{submitted_answer_choice}' to the question ID {question.id}.
        Generate JSON feedback. Confirm their answer briefly and positively. Ask if they feel confident or want another related question.
        {json_structure_notes}
        """
    else:
        instruction = f"""
        The user answered '{submitted_answer_choice}' to question ID {question.id}, but the correct answer is '{correct_answer}'.
        Generate JSON feedback. Gently guide the user. Do NOT reveal '{correct_answer}' directly. Provide a hint based on the concept or the explanation snippet: "{explanation_snippet}...". Encourage them to reconsider.
        {json_structure_notes}
        """

    messages_for_api = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_BASE
            + "\n"
            + _get_tone_instruction(session.ai_tone),
        },
        # Provide minimal context of the question text itself
        {
            "role": "assistant",
            "content": f"[Current Question Context: {question.question_text[:150]}...]",
        },
        {"role": "user", "content": instruction},
    ]

    # 3. Call AI API with JSON mode
    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for JSON hint session {session.id}, attempt {attempt.id}."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.7,
            max_tokens=200,  # Adjust if needed for JSON + text
            response_format={"type": "json_object"},  # <<< Use JSON mode
            # user=str(user.id)
        )
        ai_response_content = response.choices[0].message.content

        # 4. Parse JSON response
        try:
            parsed_json = json.loads(ai_response_content)
            ai_feedback_text = parsed_json.get("feedback_text")

            if not ai_feedback_text:
                logger.error(
                    f"AI returned valid JSON but 'feedback_text' key missing or empty for attempt {attempt.id}. JSON: {ai_response_content}"
                )
                ai_feedback_text = default_response  # Fallback
            else:
                # Optional: Log the correctness value returned by AI vs actual backend correctness
                ai_correctness = parsed_json.get("is_correct")
                if ai_correctness is not None and bool(ai_correctness) != is_correct:
                    logger.warning(
                        f"AI correctness mismatch for attempt {attempt.id}. Backend: {is_correct}, AI JSON: {ai_correctness}"
                    )
                logger.info(
                    f"AI JSON hint parsed successfully for attempt {attempt.id}"
                )

            return ai_feedback_text

        except json.JSONDecodeError as json_err:
            logger.error(
                f"Failed to parse AI JSON response for attempt {attempt.id}. Error: {json_err}. Response: '{ai_response_content}'"
            )
            return _(
                "Got your answer. Had a little trouble formatting my feedback!"
            )  # Specific fallback

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error getting JSON hint for attempt {attempt.id}: {e}",
            exc_info=True,
        )
        # Don't reveal correctness in fallback if it was wrong
        return (
            _("Got your answer. I had trouble generating a hint this time.")
            if not is_correct
            else _("Correct! Had trouble generating feedback.")
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error getting AI JSON hint for attempt {attempt.id}: {e}"
        )
        return default_response


# --- Optional: Update `get_ai_feedback_on_answer` to also use JSON ---
# (Recommended for consistency, follow similar pattern as above)
def get_ai_feedback_on_answer(
    session: ConversationSession,
    attempt: UserQuestionAttempt,
) -> str:
    """
    Generates JSON feedback from the AI for explicitly submitted answers,
    parses it, and returns the feedback text.
    """
    # Default fallback message
    default_response = _("Answer recorded.")
    if not client:
        logger.error(
            f"AI Client not available for answer feedback in session {session.id}."
        )
        return default_response

    question = attempt.question
    is_correct = attempt.is_correct  # Backend knows actual correctness
    user_answer = attempt.selected_answer
    correct_answer = question.correct_answer
    explanation = question.explanation or _("No detailed explanation available.")

    # Define the desired JSON structure (similar to handle_implicit_answer)
    json_structure_notes = """
    Your response MUST be a valid JSON object containing EXACTLY these two keys:
    1.  `is_correct`: boolean. Use the value {is_correct_bool}.
    2.  `feedback_text`: string (the detailed feedback message for the user in {tone} tone).
    Example Correct: {{"is_correct": true, "feedback_text": "Excellent! '{correct_answer}' is right because..."}}
    Example Incorrect: {{"is_correct": false, "feedback_text": "Close! The answer was '{correct_answer}'. Here's why: [brief explanation based on provided context]..."}}
    """.format(
        is_correct_bool=str(is_correct).lower(),
        tone=session.ai_tone,
        correct_answer=correct_answer,
    )

    if is_correct:
        instruction = f"""
        The user correctly answered '{user_answer}' to question ID {question.id}.
        Generate JSON feedback. Provide an encouraging confirmation. Briefly reinforce why the answer is correct, using the explanation context: "{explanation[:200]}..."
        {json_structure_notes}
        """
    else:
        instruction = f"""
        The user answered '{user_answer}' to question ID {question.id}, but the correct answer was '{correct_answer}'.
        Generate JSON feedback. Provide helpful feedback explaining why '{correct_answer}' is correct, using the explanation context: "{explanation[:300]}...". Keep it constructive.
        {json_structure_notes}
        """

    messages_for_api = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_BASE
            + "\n"
            + _get_tone_instruction(session.ai_tone),
        },
        {
            "role": "assistant",
            "content": f"[Current Question Context: {question.question_text[:150]}...]",
        },
        {"role": "user", "content": instruction},
    ]

    # Call AI API with JSON mode
    try:
        logger.info(
            f"Calling OpenAI ({AI_MODEL}) for JSON answer feedback session {session.id}, attempt {attempt.id}."
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=messages_for_api,
            temperature=0.6,
            max_tokens=250,  # Allow more tokens for potentially detailed feedback
            response_format={"type": "json_object"},  # <<< Use JSON mode
            # user=str(session.user.id)
        )
        ai_response_content = response.choices[0].message.content

        # Parse JSON response
        try:
            parsed_json = json.loads(ai_response_content)
            ai_feedback_text = parsed_json.get("feedback_text")

            if not ai_feedback_text:
                logger.error(
                    f"AI returned valid JSON but 'feedback_text' missing/empty for explicit feedback attempt {attempt.id}. JSON: {ai_response_content}"
                )
                ai_feedback_text = _("Answer recorded. Correct: {is_correct}.").format(
                    is_correct=is_correct
                )  # Simple fallback
            else:
                logger.info(
                    f"AI JSON feedback parsed successfully for explicit attempt {attempt.id}"
                )

            return ai_feedback_text

        except json.JSONDecodeError as json_err:
            logger.error(
                f"Failed to parse AI JSON feedback response for explicit attempt {attempt.id}. Error: {json_err}. Response: '{ai_response_content}'"
            )
            return _("Answer recorded. Had a little trouble formatting my feedback!")

    except OpenAIError as e:
        logger.error(
            f"OpenAI API error getting JSON feedback for explicit attempt {attempt.id}: {e}",
            exc_info=True,
        )
        return _(
            "Answer recorded. I had trouble generating detailed feedback this time."
        )
    except Exception as e:
        logger.exception(
            f"Unexpected error getting AI JSON feedback for explicit attempt {attempt.id}: {e}"
        )
        return default_response
