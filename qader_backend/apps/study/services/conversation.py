import logging
from typing import List, Optional, Dict, Any

from django.conf import settings  # Keep for MAX_HISTORY_MESSAGES
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

from apps.study.models import (
    ConversationSession,
    ConversationMessage,
    UserQuestionAttempt,
)
from apps.learning.models import Question
from django.contrib.auth import get_user_model

# Existing imports for non-AI logic
from . import get_filtered_questions, update_user_skill_proficiency

# New import for our AI manager
from .ai_manager import (
    get_ai_manager,
    AI_SPEECHLESS_MSG,
    AI_JSON_PARSE_ERROR_MSG,
)  # Import specific messages if needed

User = get_user_model()
logger = logging.getLogger(__name__)


# --- Core AI Interaction Functions (Refactored) ---


def get_ai_response(
    session: ConversationSession,
    user_message_text: str,
    current_topic_question: Optional[Question] = None,
) -> str:
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        return ai_manager.get_error_message_if_unavailable()

    history_objects = list(session.messages.order_by("timestamp").all())
    formatted_history = ai_manager._format_conversation_history(
        history_objects
    )  # Use manager's formatter

    context_message_addon = ""
    if current_topic_question:
        q_text_snippet = current_topic_question.question_text[:400]
        context_message_addon = f'\n\n[AI Context: We are currently discussing Question ID {current_topic_question.id}: "{q_text_snippet}..."]'

    system_prompt = ai_manager._construct_system_prompt(
        ai_tone_value=session.ai_tone, context_key="general_conversation"
    )

    messages_for_api = [
        *formatted_history,
        {"role": "user", "content": user_message_text + context_message_addon},
    ]

    response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt,
        messages_for_api=messages_for_api,
        user_id_for_tracking=str(session.user_id),
    )

    if error_msg:
        logger.warning(
            f"Error from AI Manager for get_ai_response (Session {session.id}): {error_msg}"
        )
        return error_msg  # Error messages are user-friendly
    if not response_content or not isinstance(response_content, str):
        logger.warning(
            f"Received non-string or empty AI response for session {session.id}. Type: {type(response_content)}"
        )
        return AI_SPEECHLESS_MSG

    logger.info(f"AI conversational response received for session {session.id}")
    return response_content


@transaction.atomic
def generate_ai_question_and_message(
    session: ConversationSession, user: User
) -> Dict[str, Any]:
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        # Original code raised ValueError for client unavailability, maintain that for caller.
        raise ValueError(ai_manager.get_error_message_if_unavailable())

    # 1. Select a Question (Logic remains unchanged)
    # ... (Copy existing question selection logic here) ...
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
    selected_question = get_filtered_questions(
        user=user, limit=1, not_mastered=True, exclude_ids=exclude_ids
    ).first()
    if not selected_question:
        selected_question = get_filtered_questions(
            user=user, limit=1, exclude_ids=exclude_ids
        ).first()
    if not selected_question:
        raise ObjectDoesNotExist(
            _("Could not find a suitable question to ask at this time.")
        )
    logger.info(
        f"Selected Q:{selected_question.id} for AI to ask in session {session.id} for user {user.id}."
    )

    # 2. Generate AI Cheer Message using AIInteractionManager
    first_skill = selected_question.skills.first()
    skill_name = first_skill.name if first_skill else "a relevant topic"
    topic_context = skill_name

    context_params_for_cheer = {
        "topic_context": topic_context,
        "question_text_snippet": selected_question.question_text[:400],
        # 'tone' is passed to _construct_system_prompt and available in template
    }

    system_prompt_for_cheer = ai_manager._construct_system_prompt(
        ai_tone_value=session.ai_tone,
        context_key="generate_cheer_message",
        context_params=context_params_for_cheer,
    )

    ai_cheer_message_text = _(
        "Okay, let's try this practice question:"
    )  # Default fallback

    # No history needed for this specific generation task
    # The "user" message is a trigger for the task defined in the system prompt.
    response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt_for_cheer,
        messages_for_api=[
            {"role": "user", "content": "Please generate the preface message now."}
        ],
        temperature=0.8,
        max_tokens=1000,
        user_id_for_tracking=str(user.id),
    )

    if error_msg:
        logger.error(
            f"AI Manager error generating cheer message for session {session.id}, Q:{selected_question.id}: {error_msg}"
        )
        # Use fallback message
    elif response_content and isinstance(response_content, str):
        ai_cheer_message_text = response_content
    else:
        logger.warning(
            f"Received empty/non-string AI cheer message for session {session.id}, Q:{selected_question.id}. Using fallback."
        )

    # 3. Save AI Message & Update Session (Logic remains unchanged)
    # ... (Copy existing save logic and session update here) ...
    ai_msg = ConversationMessage.objects.create(
        session=session,
        sender_type=ConversationMessage.SenderType.AI,
        message_text=ai_cheer_message_text,
        related_question=selected_question,
    )
    logger.info(
        f"AI 'ask-question' preface message saved (ID: {ai_msg.id}) for session {session.id}, linking Q:{selected_question.id}"
    )
    session.current_topic_question = selected_question
    session.save(update_fields=["current_topic_question", "updated_at"])

    return {"ai_message": ai_cheer_message_text, "question": selected_question}


@transaction.atomic
def prepare_understanding_test(
    session: ConversationSession, user: User
) -> Optional[Dict[str, Any]]:
    """
    Selects a test question for a concept and generates an AI message to introduce it.
    This service function is called when the user signals 'Got It'.

    Returns:
        A dict with 'ai_message' and 'test_question' object, or None if no question is found.
    """
    original_question = session.current_topic_question
    if not original_question:
        logger.warning(
            f"'Got It' logic triggered for session {session.id} but no current_topic_question set."
        )
        return None

    # 1. Select a related test question
    test_question = select_test_question_for_concept(original_question, user)
    if not test_question:
        logger.info(
            f"No suitable test question found after 'Got It' for session {session.id}, original Q {original_question.id}."
        )
        return None

    # 2. Generate an introductory AI message
    ai_manager = get_ai_manager()
    ai_message_text = _(
        "Great! Let's try a related question to solidify your understanding."
    )  # Fallback

    if ai_manager.is_available():
        # MODIFIED: Handle multiple skills, picking the first one for context.
        first_skill = original_question.skills.first()
        topic_context = first_skill.name if first_skill else "the previous topic"
        context_params = {"topic_context": topic_context}

        system_prompt = ai_manager._construct_system_prompt(
            ai_tone_value=session.ai_tone,
            context_key="generate_understanding_test_preface",
            context_params=context_params,
        )

        response_content, error_msg = ai_manager.get_chat_completion(
            system_prompt_content=system_prompt,
            messages_for_api=[
                {"role": "user", "content": "Generate the preface message now."}
            ],
            user_id_for_tracking=str(user.id),
        )

        if error_msg:
            logger.error(
                f"AI Manager error generating 'Got It' preface for session {session.id}: {error_msg}"
            )
        elif response_content and isinstance(response_content, str):
            ai_message_text = response_content

    # 3. Save the AI's message to the conversation history for context
    ConversationMessage.objects.create(
        session=session,
        sender_type=ConversationMessage.SenderType.AI,
        message_text=ai_message_text,
        # This message is a preface, not about the test question itself yet.
        # We could link it to the original question for context.
        related_question=original_question,
    )

    # 4. Return the data structure for the serializer
    return {"ai_message": ai_message_text, "test_question": test_question}


def process_user_message_with_ai(
    session: ConversationSession,
    user_message_text: str,
    current_topic_question: Optional[Question] = None,
) -> Dict[str, Any]:
    ai_manager = get_ai_manager()
    fallback_response_structure = (
        {  # Structure for successful processing, values are fallbacks
            "processed_as_answer": False,
            "user_choice": None,
            "feedback_text": _(
                "Sorry, I encountered an issue processing that. Could you try again?"
            ),
        }
    )

    if not ai_manager.is_available():
        return {
            **fallback_response_structure,
            "feedback_text": ai_manager.get_error_message_if_unavailable(),
        }

    history_objects = list(session.messages.order_by("timestamp").all())
    formatted_history = ai_manager._format_conversation_history(history_objects)

    # Prepare context parameters for the "process_user_answer_intent" template
    context_params_for_intent = {"user_message_text": user_message_text}

    # Blocks to be inserted into the CONTEXTUAL_INSTRUCTIONS template
    question_context_block_str = "[No specific question context active.]"
    intent_instructions_block_parts_str = [
        f"1. The message is NOT an answer choice to a specific question.",
        f"2. Set `processed_as_answer` to false.",
        f"3. Set `user_choice` to null.",
        f"4. Generate `feedback_text`: A helpful conversational response (in the defined {session.ai_tone} tone) to the user's message, considering the history.",
    ]

    if current_topic_question:
        correct_letter = current_topic_question.correct_answer
        explanation_snippet = (
            current_topic_question.explanation or "No explanation available."
        )[:400]
        q_text_snippet = current_topic_question.question_text[:400]
        options_snippet = f"A) {current_topic_question.option_a[:50]}... B) {current_topic_question.option_b[:50]}... C) {current_topic_question.option_c[:50]}... D) {current_topic_question.option_d[:50]}..."

        question_context_block_str = f"""
[Current Question Context (ID {current_topic_question.id}):
Text Snippet: "{q_text_snippet}..."
Options Snippet: {options_snippet}
Correct Answer Letter: '{correct_letter}']
"""
        intent_instructions_block_parts_str = [
            f"1. Check if the user message is likely an answer choice (A, B, C, D) for THIS question.",
            f"2. If YES (it's an answer choice):",
            f"   - Set `processed_as_answer` to true.",
            f"   - Set `user_choice` to the detected letter (A, B, C, or D). Ensure it's one of these exact uppercase letters.",
            f"   - Compare detected choice to '{correct_letter}'.",
            f"   - Generate `feedback_text` (in the defined {session.ai_tone} tone):",
            f"     - If correct: Brief, positive confirmation.",
            f"     - If incorrect: A guiding hint based on the concept or explanation ('{explanation_snippet}...'). DO NOT reveal the correct answer letter ('{correct_letter}') in the hint.",
            f"3. If NO (it's conversational, a question, unrelated, etc.):",
            f"   - Set `processed_as_answer` to false.",
            f"   - Set `user_choice` to null.",
            f"   - Generate `feedback_text`: A helpful conversational response (in the defined {session.ai_tone} tone) addressing the user's message, considering the history and question context.",
        ]

    context_params_for_intent["question_context_block"] = question_context_block_str
    context_params_for_intent["intent_instructions_block"] = "\n".join(
        intent_instructions_block_parts_str
    )

    system_prompt_for_intent = ai_manager._construct_system_prompt(
        ai_tone_value=session.ai_tone,
        context_key="process_user_answer_intent",
        context_params=context_params_for_intent,
    )

    messages_for_api = [
        *formatted_history,
        {
            "role": "user",
            "content": user_message_text,
        },  # The actual user message to be processed
    ]

    parsed_json_response, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt_for_intent,
        messages_for_api=messages_for_api,
        temperature=0.8,
        max_tokens=1000,
        response_format={"type": "json_object"},
        user_id_for_tracking=str(session.user_id),
    )

    if error_msg:  # Includes JSON parsing errors from manager
        logger.error(
            f"AI Manager error during intent analysis (Session {session.id}): {error_msg}. Falling back to standard conversation."
        )
        fallback_text = get_ai_response(
            session, user_message_text, current_topic_question
        )  # Call self for standard response
        return {**fallback_response_structure, "feedback_text": fallback_text}

    if not isinstance(
        parsed_json_response, dict
    ):  # Should be a dict if no error and JSON requested
        logger.error(
            f"AI Manager returned non-dict for JSON request (Session {session.id}). Response: {parsed_json_response}. Falling back."
        )
        fallback_text = get_ai_response(
            session, user_message_text, current_topic_question
        )
        return {**fallback_response_structure, "feedback_text": fallback_text}

    # Validate structure and types from parsed_json_response
    try:
        processed_as_answer = parsed_json_response.get("processed_as_answer")
        user_choice = parsed_json_response.get("user_choice")
        feedback_text = parsed_json_response.get("feedback_text")

        if not isinstance(processed_as_answer, bool) or not isinstance(
            feedback_text, str
        ):
            raise ValueError("Invalid types in JSON response from AI.")

        valid_answer_choices = (
            UserQuestionAttempt.AnswerChoice.values
        )  # ['A', 'B', 'C', 'D']
        if processed_as_answer and (
            user_choice is None or user_choice not in valid_answer_choices
        ):
            logger.warning(
                f"AI returned processed_as_answer=true but invalid/null user_choice '{user_choice}' (Session {session.id}). Treating as non-answer. JSON: {parsed_json_response}"
            )
            # Override AI decision if choice is invalid
            processed_as_answer = False
            user_choice = None
            # Consider asking AI for a purely conversational response here, or use a generic message.
            # For now, we use the feedback_text that might be confusing, or generate a new one.
            # Let's generate a simple conversational one.
            feedback_text = get_ai_response(
                session,
                f"Regarding my previous message: {user_message_text}",
                current_topic_question,
            )

        elif not processed_as_answer:
            user_choice = None  # Ensure choice is null if not an answer

        logger.info(
            f"AI intent analysis successful (Session {session.id}). Processed as answer: {processed_as_answer}, Choice: {user_choice}"
        )
        return {
            "processed_as_answer": processed_as_answer,
            "user_choice": user_choice,
            "feedback_text": feedback_text,
        }
    except (ValueError, KeyError) as validation_err:
        logger.error(
            f"Failed to validate AI JSON structure from AI manager (Session {session.id}). Error: {validation_err}. JSON: {parsed_json_response}",
            exc_info=True,
        )
        fallback_text = get_ai_response(
            session, user_message_text, current_topic_question
        )
        return {**fallback_response_structure, "feedback_text": fallback_text}


def get_ai_feedback_on_answer(
    session: ConversationSession,
    attempt: UserQuestionAttempt,
) -> str:
    ai_manager = get_ai_manager()
    default_feedback_message = _("Answer recorded.")

    if not ai_manager.is_available():
        return f"{default_feedback_message} {ai_manager.get_error_message_if_unavailable()}"

    question = attempt.question
    is_correct = attempt.is_correct
    if is_correct is None:
        logger.error(
            f"Cannot generate AI feedback for attempt {attempt.id}: is_correct is None."
        )
        return _(
            "Answer recorded, but correctness could not be determined for feedback."
        )

    context_params_for_feedback = {
        "question_id": question.id,
        "question_text_snippet": question.question_text[:150],
        "user_answer": attempt.selected_answer,
        "correct_answer": question.correct_answer,
        "is_correct": is_correct,
        "explanation_snippet": (
            question.explanation or _("No detailed explanation available.")
        )[:300],
        # 'tone' is passed to _construct_system_prompt
    }

    system_prompt_for_feedback = ai_manager._construct_system_prompt(
        ai_tone_value=session.ai_tone,
        context_key="generate_answer_feedback",
        context_params=context_params_for_feedback,
    )

    parsed_json_response, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt_for_feedback,
        messages_for_api=[
            {"role": "user", "content": "Provide feedback on the recorded answer."}
        ],  # Trigger message
        temperature=0.8,
        max_tokens=1000,
        response_format={"type": "json_object"},
        user_id_for_tracking=str(session.user_id),
    )

    if error_msg:  # Includes JSON parsing errors
        logger.error(
            f"AI Manager error getting JSON feedback for attempt {attempt.id}: {error_msg}"
        )
        # Simple fallback based on correctness
        return (
            _("Answer recorded. Correct: {is_correct}.").format(is_correct=is_correct)
            if is_correct is not None
            else default_feedback_message
        )

    if (
        not isinstance(parsed_json_response, dict)
        or "feedback_text" not in parsed_json_response
        or not isinstance(parsed_json_response["feedback_text"], str)
    ):
        logger.error(
            f"AI returned invalid JSON structure for feedback_text (Attempt {attempt.id}). JSON: {parsed_json_response}"
        )
        return _(
            "Answer recorded. I had a little trouble formatting my detailed feedback this time."
        )

    logger.info(f"AI JSON feedback parsed successfully for attempt {attempt.id}")
    return parsed_json_response["feedback_text"]


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

    # MODIFIED: The original question can have multiple skills
    target_skills = original_question.skills.all()
    target_subsection = original_question.subsection

    if not target_skills and not target_subsection:
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
    exclude_ids = set(recent_correct_conv_ids) | {original_question.id}

    test_question = None
    # Prioritize finding a question with at least one of the same skills
    if target_skills:
        # MODIFIED: Was filter(skill=target_skill)
        test_question = (
            Question.objects.filter(skills__in=target_skills, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")
            .first()
        )

    # Fallback to the same subsection if no skill-match found
    if not test_question and target_subsection:
        logger.info(
            f"No suitable test question found for Skill IDs {list(target_skills.values_list('id', flat=True)) if target_skills else 'N/A'}. Falling back to Subsection ID {target_subsection.id}."
        )
        test_question = (
            Question.objects.filter(subsection=target_subsection, is_active=True)
            .exclude(id__in=exclude_ids)
            .order_by("?")
            .first()
        )

    if test_question:
        logger.info(
            f"Selected test question {test_question.id} (Skills: {list(test_question.skills.values_list('id', flat=True))}, SubSec: {test_question.subsection_id}) related to original Q:{original_question.id} for user {user.id}."
        )
    else:
        logger.warning(
            f"No suitable *different* test question found related to original Q:{original_question.id} (Skills: {list(target_skills.values_list('id', flat=True)) if target_skills else 'N/A'}, SubSec: {target_subsection.id if target_subsection else 'N/A'}) for user {user.id}."
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
    attempt.refresh_from_db(fields=["is_correct"])  # Ensure is_correct is populated

    log_prefix = "Recorded" if created else "Updated"
    logger.info(
        f"{log_prefix} conversation test attempt {attempt.id} for user {user.username} (ID: {user.id}), Q:{test_question.id}, Session:{session.id}. Correct: {attempt.is_correct}"
    )

    # Update Skill Proficiency for EACH skill associated with the question
    if attempt.is_correct is not None:
        # MODIFIED: Loop through all skills
        for skill in test_question.skills.all():
            update_user_skill_proficiency(
                user=user, skill=skill, is_correct=attempt.is_correct
            )
    else:
        logger.warning(
            f"Skill proficiency not updated for attempt {attempt.id} as is_correct is None."
        )

    # gamification logic (e.g., call a gamification service or signal)
    # award_points_for_conversation_attempt(attempt)

    return attempt
