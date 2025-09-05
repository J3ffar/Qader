import logging
import random
from typing import Optional, Dict, Any, List

from django.utils.translation import gettext_lazy as _

from apps.study.models import UserTestAttempt, ConversationSession, EmergencyModeSession
from apps.study.services.ai_manager import get_ai_manager
from django.contrib.auth import get_user_model

from .constants import (
    AI_ANALYSIS_MAX_ANSWER_DETAILS,
    AI_ANALYSIS_DEFAULT_FALLBACK,
    AI_ANALYSIS_HIGH_SCORE_THRESHOLD,
    AI_ANALYSIS_LOW_SCORE_THRESHOLD,
    LEVEL_ASSESSMENT_SCORE_THRESHOLD,
    DEFAULT_EMERGENCY_TIPS,
)

User = get_user_model()
logger = logging.getLogger(__name__)


# --- Test Attempt Analysis Helpers ---
def _format_results_summary_for_ai(results_summary: Optional[Dict[str, Any]]) -> str:
    """Formats the results_summary dictionary into a string for the AI prompt."""
    if not results_summary:
        return _("No detailed breakdown by topic available.")

    summary_lines = []
    for slug, data in results_summary.items():
        if isinstance(data, dict) and "name" in data and "score" in data:
            name = data.get("name", slug)
            score = data.get("score")
            if score is not None:
                score_str = (
                    f"{score:.1f}%" if isinstance(score, (float, int)) else str(score)
                )
                summary_lines.append(f"- {name}: {score_str}")
            else:
                summary_lines.append(f"- {name}: {_('N/A')}")
    if not summary_lines:
        return _("Detailed topic scores are not available for this attempt.")
    return "\n".join(summary_lines)


def _format_user_answers_for_ai(
    user_test_attempt: UserTestAttempt,
    max_questions_to_detail: int = AI_ANALYSIS_MAX_ANSWER_DETAILS,
) -> str:
    """Formats user's question attempts into a string for the AI prompt."""
    question_attempts = list(
        user_test_attempt.question_attempts.select_related(
            "question__subsection", "question__skill"
        ).all()
    )
    if not question_attempts:
        return _("No specific answer details available for this attempt.")
    answer_details_lines = []
    incorrect_attempts = [qa for qa in question_attempts if qa.is_correct is False]
    correct_attempts = [qa for qa in question_attempts if qa.is_correct is True]
    for qa in incorrect_attempts:
        if len(answer_details_lines) >= max_questions_to_detail:
            break
        q = qa.question
        line = _(
            "Question in '{subsection}' (Skill: {skill}): Your answer '{user_ans}', Correct: '{correct_ans}' (Incorrect)."
        ).format(
            subsection=q.subsection.name if q.subsection else _("N/A"),
            skill=q.skill.name if q.skill else _("N/A"),
            user_ans=qa.selected_answer or _("Not Answered"),
            correct_ans=q.correct_answer,
        )
        answer_details_lines.append(line)
    remaining_space = max_questions_to_detail - len(answer_details_lines)
    if remaining_space > 0:
        for qa in correct_attempts[: min(remaining_space, 2)]:
            q = qa.question
            line = _(
                "Question in '{subsection}' (Skill: {skill}): Your answer '{user_ans}' (Correct)."
            ).format(
                subsection=q.subsection.name if q.subsection else _("N/A"),
                skill=q.skill.name if q.skill else _("N/A"),
                user_ans=qa.selected_answer,
            )
            answer_details_lines.append(line)
    if len(question_attempts) > len(answer_details_lines) >= max_questions_to_detail:
        answer_details_lines.append(
            _("... (and {num_more} other questions were answered).").format(
                num_more=len(question_attempts) - len(answer_details_lines)
            )
        )
    return (
        "\n".join(answer_details_lines)
        if answer_details_lines
        else _("Could not retrieve specific answer details for analysis.")
    )


def _generate_ai_performance_analysis(user: User, test_attempt: UserTestAttempt) -> str:
    """
    Generates a smart performance analysis using AI.
    Returns the AI-generated text or a fallback message.
    """
    ai_manager = get_ai_manager()
    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for performance analysis (User: {user.id}, Attempt: {test_attempt.id}). Reason: {ai_manager.init_error}"
        )
        if test_attempt.score_percentage is not None:
            if test_attempt.score_percentage >= AI_ANALYSIS_HIGH_SCORE_THRESHOLD:
                return _(
                    "Excellent work! You demonstrated strong understanding in this test."
                )
            elif test_attempt.score_percentage < AI_ANALYSIS_LOW_SCORE_THRESHOLD:
                return _(
                    "Good effort! Keep practicing to improve your score. Review your answers to learn from any mistakes."
                )
        return AI_ANALYSIS_DEFAULT_FALLBACK

    overall_score_str = (
        f"{test_attempt.score_percentage:.1f}"
        if test_attempt.score_percentage is not None
        else _("N/A")
    )
    verbal_score_str = (
        f"{test_attempt.score_verbal:.1f}%"
        if test_attempt.score_verbal is not None
        else _("N/A")
    )
    quantitative_score_str = (
        f"{test_attempt.score_quantitative:.1f}%"
        if test_attempt.score_quantitative is not None
        else _("N/A")
    )

    user_answers_details_str = _format_user_answers_for_ai(test_attempt)

    context_params = {
        "overall_score": overall_score_str,
        "verbal_score_str": verbal_score_str,
        "quantitative_score_str": quantitative_score_str,
        "results_summary_str": _format_results_summary_for_ai(
            test_attempt.results_summary
        ),
        "test_type_display": test_attempt.get_attempt_type_display(),
        "user_answers_details_str": user_answers_details_str,
    }

    system_prompt = ai_manager._construct_system_prompt(
        ai_tone_value="encouraging_analytic",
        context_key="generate_test_performance_analysis",
        context_params=context_params,
    )

    trigger_message = _(
        "Please provide a performance analysis for the test I just completed based on my scores and answer summary."
    )

    ai_response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt,
        messages_for_api=[{"role": "user", "content": trigger_message}],
        temperature=0.6,
        max_tokens=450,  # Slightly increased max_tokens for potentially more detailed analysis
        response_format=None,
        user_id_for_tracking=str(user.id),
    )

    if (
        error_msg
        or not isinstance(ai_response_content, str)
        or not ai_response_content.strip()
    ):
        logger.error(
            f"AI performance analysis generation failed for User: {user.id}, Attempt: {test_attempt.id}. Error: {error_msg or 'Empty response'}. "
            f"AI Response: '{str(ai_response_content)[:200]}...'"
        )
        # More nuanced fallback based on scores if AI fails
        if test_attempt.score_percentage is not None:
            if test_attempt.score_percentage >= AI_ANALYSIS_HIGH_SCORE_THRESHOLD:
                return _("Fantastic job on this test! Your hard work is paying off.")
            elif test_attempt.score_percentage < AI_ANALYSIS_LOW_SCORE_THRESHOLD:
                weakest_area_name = None
                min_score = 101  # Initialize higher than max score
                if test_attempt.results_summary:
                    for area_slug, data in test_attempt.results_summary.items():
                        if (
                            isinstance(data, dict)
                            and isinstance(data.get("score"), (int, float))
                            and data["score"] is not None
                        ):
                            if data["score"] < min_score:
                                min_score = data["score"]
                                weakest_area_name = data.get("name") or area_slug
                if (
                    weakest_area_name and min_score < LEVEL_ASSESSMENT_SCORE_THRESHOLD
                ):  # Using a general threshold for "weak"
                    return _(
                        "Good effort! Your results suggest focusing more practice on '{area}' where your score was {score}%."
                    ).format(area=weakest_area_name, score=round(min_score, 1))
                return _(
                    "You've completed the test. Take some time to review your answers and identify areas for growth."
                )
        return AI_ANALYSIS_DEFAULT_FALLBACK  # Ultimate fallback

    logger.info(
        f"Successfully generated AI performance analysis for User: {user.id}, Attempt: {test_attempt.id}. Analysis: {ai_response_content[:200]}..."
    )
    return ai_response_content.strip()


# --- Emergency Mode Analysis Helpers ---


def _generate_ai_emergency_tips(
    user: User,
    target_skills_data: List[Dict[str, Any]],
    focus_area_names: List[str],
    available_time_hours: Optional[float] = None,
    days_until_test: Optional[int] = None,  # <<<--- ADD NEW PARAMETER
) -> List[str]:
    ai_manager = get_ai_manager()
    # Define fallback tips here, ensuring it's always a list of 2-3 strings
    num_fallback_tips = min(
        len(DEFAULT_EMERGENCY_TIPS),
        (
            random.randint(2, 3)
            if len(DEFAULT_EMERGENCY_TIPS) >= 2
            else len(DEFAULT_EMERGENCY_TIPS)
        ),
    )
    fallback_tips = (
        random.sample(DEFAULT_EMERGENCY_TIPS, k=num_fallback_tips)
        if DEFAULT_EMERGENCY_TIPS
        else ["Stay calm and focus!"]
    )

    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for emergency tips (User {user.id}). Reason: {ai_manager.init_error}. Using default tips."
        )
        return fallback_tips

    weak_skills_summary_list = [
        f"- {s['name']} ({s.get('reason', 'Needs practice')})"
        for s in target_skills_data[:3]  # Take top 3
    ]
    weak_skills_summary_str = (
        "\n".join(weak_skills_summary_list)
        if weak_skills_summary_list
        else _("  (General review recommended or user is new)")
    )

    focus_areas_str = (
        ", ".join(focus_area_names)
        if focus_area_names
        else _("Verbal and Quantitative sections")
    )

    time_context = (
        f"The user has approximately {available_time_hours:.1f} hours available."
        if available_time_hours and available_time_hours > 0
        else "Time is limited."
    )

    days_context = "The user has not specified when their test is."
    if days_until_test is not None:
        if days_until_test == 0:
            days_context = "The user's test is TODAY. The situation is critical."
        elif days_until_test == 1:
            days_context = "The user's test is TOMORROW."
        else:
            days_context = f"The user's test is in {days_until_test} days."

    context_params_for_tips = {
        "focus_areas_str": focus_areas_str,
        "weak_skills_summary_str": weak_skills_summary_str,
        "time_context": time_context,
        "days_context": days_context,
    }

    # Emergency tips usually have a specific, direct tone.
    # The `CONTEXTUAL_INSTRUCTIONS` for `generate_emergency_tips` already sets this context.
    # The `ai_tone_value` for `_construct_system_prompt` can be a default or specific for emergency.
    system_prompt_for_tips = ai_manager._construct_system_prompt(
        ai_tone_value=ConversationSession.AiTone.SERIOUS,  # e.g., emergency mode uses a serious, direct tone
        context_key="generate_emergency_tips",
        context_params=context_params_for_tips,
    )

    parsed_json_response, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt_for_tips,
        messages_for_api=[
            {"role": "user", "content": "Please generate the emergency study tips now."}
        ],  # Trigger
        temperature=0.8,
        max_tokens=1000,
        response_format={"type": "json_object"},
        user_id_for_tracking=str(user.id),
    )

    if error_msg:  # Includes JSON parsing errors
        logger.error(
            f"AI Manager error generating emergency tips for user {user.id}: {error_msg}. Using default tips."
        )
        return fallback_tips

    if isinstance(parsed_json_response, dict) and "tips" in parsed_json_response:
        generated_tips = parsed_json_response["tips"]
        if (
            isinstance(generated_tips, list)
            and all(isinstance(tip, str) for tip in generated_tips)
            and 1 < len(generated_tips) <= 10
        ):  # Expect 2 or 10 tips
            logger.info(
                f"Successfully generated {len(generated_tips)} AI emergency tips for user {user.id}."
            )
            return generated_tips
        else:
            logger.warning(
                f"AI returned invalid 'tips' structure or count for user {user.id}. JSON: {parsed_json_response}. Using default tips."
            )
    else:
        logger.warning(
            f"AI returned non-dict or 'tips' key missing for user {user.id} emergency tips. Response: {parsed_json_response}. Using default tips."
        )

    return fallback_tips


def _generate_ai_emergency_session_feedback(
    user: User,
    session: EmergencyModeSession,
    overall_score: float,
    results_summary: Dict[str, Any],
) -> str:
    """
    Generates tailored AI feedback for a completed Emergency Mode session.
    """
    ai_manager = get_ai_manager()
    fallback_message = _(
        "Great job completing your emergency session! Review your results to see where you excelled and what you can focus on next."
    )
    if not ai_manager.is_available():
        logger.warning(
            f"AI manager not available for emergency session feedback (User: {user.id}, Session: {session.id}). Reason: {ai_manager.init_error}"
        )
        return fallback_message

    # Format data for the AI prompt
    overall_score_str = f"{overall_score:.1f}%"
    results_summary_str = _format_results_summary_for_ai(results_summary)

    context_params = {
        "overall_score_str": overall_score_str,
        "results_summary_str": results_summary_str,
        "focus_areas_str": ", ".join(
            session.suggested_plan.get("focus_area_names", [])
        ),
    }

    system_prompt = ai_manager._construct_system_prompt(
        ai_tone_value="encouraging_analytic",
        context_key="generate_emergency_session_feedback",
        context_params=context_params,
    )

    trigger_message = _(
        "Please provide a performance analysis for the emergency study session I just completed."
    )

    ai_response_content, error_msg = ai_manager.get_chat_completion(
        system_prompt_content=system_prompt,
        messages_for_api=[{"role": "user", "content": trigger_message}],
        temperature=0.6,
        max_tokens=300,
        response_format=None,
        user_id_for_tracking=str(user.id),
    )

    if (
        error_msg
        or not isinstance(ai_response_content, str)
        or not ai_response_content.strip()
    ):
        logger.error(
            f"AI emergency session feedback generation failed for User: {user.id}, Session: {session.id}. Error: {error_msg or 'Empty response'}."
        )
        return fallback_message

    logger.info(
        f"Successfully generated AI feedback for emergency session {session.id} for user {user.id}."
    )
    return ai_response_content.strip()
