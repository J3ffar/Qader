import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
import random

from apps.learning.tests.factories import QuestionFactory, SkillFactory
from apps.users.tests.factories import UserFactory
from apps.study.models import (
    EmergencyModeSession,
    UserQuestionAttempt,
    UserSkillProficiency,
    UserTestAttempt,
)
from apps.learning.models import LearningSubSection, Question, Skill  # Added Skill


class UserSkillProficiencyFactory(DjangoModelFactory):
    class Meta:
        model = UserSkillProficiency
        django_get_or_create = ("user", "skill")

    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_score = factory.Faker(
        "pyfloat", left_digits=1, right_digits=4, min_value=0.0, max_value=1.0
    )
    attempts_count = factory.Faker("random_int", min=1, max=50)
    correct_count = factory.LazyAttribute(
        lambda o: random.randint(0, o.attempts_count) if o.attempts_count > 0 else 0
    )
    last_calculated_at = factory.LazyFunction(timezone.now)


class UserTestAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserTestAttempt

    user = factory.SubFactory(UserFactory)
    attempt_type = UserTestAttempt.AttemptType.PRACTICE
    test_definition = None
    test_configuration = factory.LazyFunction(
        lambda: {
            "test_type": UserTestAttempt.AttemptType.PRACTICE.value,
            "config": {
                "name": "Factory Default Test",
                "subsections": [],
                "skills": [],
                "num_questions": 5,
                "actual_num_questions_selected": 5,  # Match generated q_ids
                "starred": False,
                "not_mastered": False,
                "full_simulation": False,
            },
        }
    )
    # Generate default question IDs matching the config num_questions
    question_ids = factory.LazyFunction(
        lambda: [q.id for q in QuestionFactory.create_batch(5)]
    )
    status = UserTestAttempt.Status.STARTED
    start_time = factory.LazyFunction(timezone.now)
    end_time = None
    score_percentage = None
    score_verbal = None
    score_quantitative = None
    results_summary = None

    class Params:
        completed = factory.Trait(
            status=UserTestAttempt.Status.COMPLETED,
            end_time=factory.LazyAttribute(
                lambda o: o.start_time + timedelta(minutes=random.randint(5, 20))
            ),
            score_percentage=factory.Faker(
                "pyfloat", left_digits=2, right_digits=1, min_value=50.0, max_value=99.9
            ),
            results_summary=factory.LazyAttribute(
                lambda o: {
                    "placeholder_section": {
                        "correct": 3,
                        "total": len(o.question_ids),
                        "score": 60.0,
                        "name": "Placeholder Section",
                    }
                }
            ),
        )
        abandoned = factory.Trait(
            status=UserTestAttempt.Status.ABANDONED,
            end_time=factory.LazyAttribute(
                lambda o: o.start_time + timedelta(minutes=random.randint(2, 10))
            ),
        )
        level_assessment = factory.Trait(
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            test_configuration=factory.LazyFunction(
                lambda: {
                    "test_type": UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.value,
                    "sections_requested": ["verbal", "quantitative"],
                    "num_questions_requested": 10,
                    "actual_num_questions_selected": 10,  # Match generated q_ids
                }
            ),
            question_ids=factory.LazyFunction(
                lambda: [q.id for q in QuestionFactory.create_batch(10)]
            ),
        )
        practice = factory.Trait(attempt_type=UserTestAttempt.AttemptType.PRACTICE)
        simulation = factory.Trait(attempt_type=UserTestAttempt.AttemptType.SIMULATION)


class UserQuestionAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionAttempt

    user = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)
    test_attempt = None
    selected_answer = factory.Iterator(["A", "B", "C", "D"])
    is_correct = factory.LazyAttribute(
        lambda o: o.selected_answer == o.question.correct_answer
    )
    time_taken_seconds = factory.Faker("random_int", min=10, max=120)
    mode = UserQuestionAttempt.Mode.TRADITIONAL
    attempted_at = factory.LazyFunction(timezone.now)

    class Params:
        in_test = factory.Trait(
            test_attempt=factory.SubFactory(
                UserTestAttemptFactory, user=factory.SelfAttribute("....user")
            ),
            mode=UserQuestionAttempt.Mode.TEST,
        )
        in_level_assessment = factory.Trait(
            # Ensure the linked attempt has the correct type
            test_attempt=factory.SubFactory(
                UserTestAttemptFactory,
                user=factory.SelfAttribute("....user"),
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
                # Make sure question_ids in the attempt factory match questions being created for attempts
                question_ids=factory.LazyAttribute(
                    lambda o: [o.question.id]
                ),  # Simplification: just link this question
            ),
            mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        )
        correct = factory.Trait(
            selected_answer=factory.LazyAttribute(lambda o: o.question.correct_answer),
            is_correct=True,
        )
        incorrect = factory.Trait(
            selected_answer=factory.LazyAttribute(
                lambda o: next(
                    c for c in ["A", "B", "C", "D"] if c != o.question.correct_answer
                )
            ),
            is_correct=False,
        )


# Modified helper function to create a scenario ready for completion or already completed
def create_attempt_scenario(
    user,
    num_questions=5,
    num_answered=5,  # How many answers to create
    num_correct_answered=3,  # How many of the answered are correct
    attempt_type=UserTestAttempt.AttemptType.PRACTICE,
    status=UserTestAttempt.Status.STARTED,  # Default to started
    **kwargs,  # Pass other args to UserTestAttemptFactory
):
    """Creates a UserTestAttempt with related questions and optional UserQuestionAttempts."""
    # --- FIX: Add validation ---
    if num_correct_answered > num_answered:
        num_correct_answered = num_answered  # Ensure correct <= answered
        # Or raise ValueError("num_correct_answered cannot be greater than num_answered")
    if num_answered > num_questions:
        num_answered = num_questions  # Ensure answered <= total
        # Or raise ValueError("num_answered cannot be greater than num_questions")
    # --------------------------

    questions = QuestionFactory.create_batch(num_questions)
    question_ids = [q.id for q in questions]

    first_q = questions[0] if questions else None
    sub_slug = first_q.subsection.slug if first_q and first_q.subsection else "default"
    config_snapshot = {
        "test_type": attempt_type.value,
        "config": {
            "name": f"{attempt_type.label} Test Scenario",
            "subsections": [sub_slug] if sub_slug != "default" else [],
            "skills": [],
            "num_questions": num_questions,
            "actual_num_questions_selected": len(question_ids),
            # ... other config fields ...
        },
        **(kwargs.pop("test_configuration", {})),
    }

    # Ensure question_ids from kwargs override the default generated ones if provided
    final_question_ids = kwargs.pop("question_ids", question_ids)

    # Create the attempt
    attempt = UserTestAttemptFactory(
        user=user,
        status=status,
        attempt_type=attempt_type,
        question_ids=final_question_ids,  # Use final list
        test_configuration=config_snapshot,
        **kwargs,  # Apply overrides like 'completed=True' trait etc.
    )

    # Ensure questions match the final_question_ids
    questions_in_attempt = list(Question.objects.filter(id__in=final_question_ids))
    if len(questions_in_attempt) != len(final_question_ids):
        # This indicates a potential issue where specified IDs don't exist
        # Or the earlier generation didn't match kwargs override
        print(
            f"Warning: Mismatch between requested question IDs ({len(final_question_ids)}) and found questions ({len(questions_in_attempt)})"
        )
        # Fallback to using the questions actually found
        final_question_ids = [q.id for q in questions_in_attempt]
        attempt.question_ids = final_question_ids
        attempt.save(update_fields=["question_ids"])

    # Create related question attempts if num_answered > 0
    created_attempts = []
    # --- FIX: Ensure we only try to answer questions actually in the attempt ---
    questions_to_answer = questions_in_attempt[:num_answered]
    # --------------------------------------------------------------------------
    for i, q in enumerate(questions_to_answer):
        is_correct_flag = i < num_correct_answered
        selected = (
            q.correct_answer
            if is_correct_flag
            else next(c for c in ["A", "B", "C", "D"] if c != q.correct_answer)
        )
        mode_map = {
            UserTestAttempt.AttemptType.LEVEL_ASSESSMENT: UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
            UserTestAttempt.AttemptType.PRACTICE: UserQuestionAttempt.Mode.TEST,
            UserTestAttempt.AttemptType.SIMULATION: UserQuestionAttempt.Mode.TEST,
        }
        mode = mode_map.get(attempt_type, UserQuestionAttempt.Mode.TEST)
        qa = UserQuestionAttemptFactory(
            user=user,
            question=q,
            test_attempt=attempt,
            selected_answer=selected,
            is_correct=is_correct_flag,
            mode=mode,
            attempted_at=attempt.start_time
            + timedelta(seconds=random.randint(10, 50) * (i + 1)),
        )
        created_attempts.append(qa)

    # If the attempt was created with 'completed' status, calculate scores now
    if attempt.status == UserTestAttempt.Status.COMPLETED and created_attempts:
        # --- FIX: Pass the queryset correctly ---
        attempt_qs = UserQuestionAttempt.objects.filter(test_attempt=attempt)
        # -----------------------------------------
        attempt.calculate_and_save_scores(attempt_qs)
        # Ensure end_time is set if completed
        if not attempt.end_time:
            attempt.end_time = timezone.now()
            attempt.save(update_fields=["end_time"])

    attempt.refresh_from_db()
    return attempt, questions_in_attempt  # Return the actual questions used


class EmergencyModeSessionFactory(DjangoModelFactory):
    class Meta:
        model = EmergencyModeSession

    user = factory.SubFactory(UserFactory)
    reason = factory.Faker("sentence", nb_words=10)
    # Provide a default valid plan structure
    suggested_plan = factory.LazyFunction(
        lambda: {
            "focus_area_names": ["Quantitative"],  # Plain string
            "estimated_duration_minutes": 30,
            "target_skills": [
                {
                    "slug": "skill-slug-1",
                    "name": "Skill Name 1",
                    "reason": "Low score",
                    "current_proficiency": 0.2,
                    "subsection_name": "Sub Name 1",
                },
                {
                    "slug": "skill-slug-2",
                    "name": "Skill Name 2",
                    "reason": "Not attempted",
                    "current_proficiency": None,
                    "subsection_name": "Sub Name 2",
                },
            ],
            "recommended_question_count": 15,
            "quick_review_topics": [
                {
                    "slug": "topic-a",
                    "name": "Topic A",
                    "description": "Desc A",
                },  # Plain strings
                {"slug": "topic-b", "name": "Topic B", "description": "Desc B"},
            ],
            "motivational_tips": ["Default Tip 1", "Default Tip 2"],  # Plain strings
        }
    )
    calm_mode_active = False
    start_time = factory.LazyFunction(timezone.now)
    end_time = None  # Active by default
    shared_with_admin = False
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    class Params:
        # Trait for an ended session
        ended = factory.Trait(
            end_time=factory.LazyAttribute(
                lambda o: (
                    o.start_time + timedelta(minutes=random.randint(10, 30))
                    if o.start_time
                    else timezone.now()
                )
            )
        )
