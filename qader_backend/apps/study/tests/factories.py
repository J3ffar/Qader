# qader_backend/apps/study/tests/factories.py
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
from apps.learning.models import LearningSubSection, Question, Skill


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
                        "total": (
                            len(o.question_ids)
                            if isinstance(o.question_ids, list)
                            else 0
                        ),  # Ensure question_ids is a list
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
        lambda o: (
            o.selected_answer == o.question.correct_answer if o.question else False
        )
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
            test_attempt=factory.SubFactory(
                UserTestAttemptFactory,
                user=factory.SelfAttribute("....user"),
                # FIX: Rely on the 'level_assessment' trait of UserTestAttemptFactory
                # to correctly set attempt_type and its own question_ids.
                # The trait already sets attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT.
                level_assessment=True,
                # REMOVED BUGGY OVERRIDE:
                # question_ids=factory.LazyAttribute(
                #     lambda o: [o.question.id] # This was incorrect.
                # ),
            ),
            mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        )
        correct = factory.Trait(
            selected_answer=factory.LazyAttribute(
                lambda o: o.question.correct_answer if o.question else "A"
            ),
            is_correct=True,
        )
        incorrect = factory.Trait(
            selected_answer=factory.LazyAttribute(
                lambda o: next(
                    c
                    for c in ["A", "B", "C", "D"]
                    if c != (o.question.correct_answer if o.question else "A")
                )
                or "B"  # ensure there's a fallback if correct_answer is D
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
    if num_correct_answered > num_answered:
        num_correct_answered = num_answered
    if num_answered > num_questions:
        num_answered = num_questions

    questions = QuestionFactory.create_batch(num_questions)
    initial_question_ids = [q.id for q in questions]

    first_q = questions[0] if questions else None
    sub_slug = first_q.subsection.slug if first_q and first_q.subsection else "default"

    # Ensure question_ids from kwargs override the default generated ones if provided
    final_question_ids = kwargs.pop("question_ids", initial_question_ids)

    # FIX: Ensure 'actual_num_questions_selected' in config reflects final_question_ids
    config_snapshot_base = {
        "test_type": attempt_type.value,
        "config": {
            "name": f"{attempt_type.label} Test Scenario",
            "subsections": [sub_slug] if sub_slug != "default" else [],
            "skills": [],
            "num_questions": num_questions,  # Original request for the scenario
            "actual_num_questions_selected": len(
                final_question_ids
            ),  # Reflects the actual IDs used
            "starred": False,
            "not_mastered": False,
            "full_simulation": False,
            # ... other config fields ...
        },
    }
    # Allow kwargs to override the entire test_configuration if provided
    config_snapshot = kwargs.pop("test_configuration", config_snapshot_base)
    # If test_configuration was provided in kwargs, ensure its internal 'actual_num_questions_selected' is also correct,
    # or assume it's intentionally set by the caller. For safety, if it was deeply nested, we might re-ensure:
    if (
        "config" in config_snapshot
        and "actual_num_questions_selected" in config_snapshot["config"]
    ):
        config_snapshot["config"]["actual_num_questions_selected"] = len(
            final_question_ids
        )

    # Create the attempt
    attempt = UserTestAttemptFactory(
        user=user,
        status=status,
        attempt_type=attempt_type,
        question_ids=final_question_ids,
        test_configuration=config_snapshot,
        **kwargs,
    )

    questions_in_attempt = list(Question.objects.filter(id__in=final_question_ids))
    if len(questions_in_attempt) != len(final_question_ids):
        print(
            f"Warning: Mismatch between requested question IDs ({len(final_question_ids)}) and found questions ({len(questions_in_attempt)})"
        )
        final_question_ids = [q.id for q in questions_in_attempt]
        attempt.question_ids = final_question_ids
        attempt.save(
            update_fields=["question_ids"]
        )  # test_configuration might also need update here if strict

    created_attempts = []
    questions_to_answer = questions_in_attempt[:num_answered]
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
            UserTestAttempt.AttemptType.TRADITIONAL: UserQuestionAttempt.Mode.TRADITIONAL,  # Added for completeness
        }
        # Use the attempt_type from the 'attempt' object, not the function argument, as kwargs might change it
        mode = mode_map.get(attempt.attempt_type, UserQuestionAttempt.Mode.TEST)
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

    if attempt.status == UserTestAttempt.Status.COMPLETED and created_attempts:
        attempt_qs = UserQuestionAttempt.objects.filter(test_attempt=attempt)
        attempt.calculate_and_save_scores(attempt_qs)
        if not attempt.end_time:
            attempt.end_time = timezone.now()
            attempt.save(update_fields=["end_time"])

    attempt.refresh_from_db()
    return attempt, questions_in_attempt


class EmergencyModeSessionFactory(DjangoModelFactory):
    class Meta:
        model = EmergencyModeSession

    user = factory.SubFactory(UserFactory)
    reason = factory.Faker("sentence", nb_words=10)
    suggested_plan = factory.LazyFunction(
        lambda: {
            "focus_area_names": ["Quantitative"],
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
                    "current_ proficiency": None,
                    "subsection_name": "Sub Name 2",
                },
            ],
            "recommended_question_count": 15,
            "quick_review_topics": [
                {
                    "slug": "topic-a",
                    "name": "Topic A",
                    "description": "Desc A",
                },
                {"slug": "topic-b", "name": "Topic B", "description": "Desc B"},
            ],
            "motivational_tips": ["Default Tip 1", "Default Tip 2"],
        }
    )
    calm_mode_active = False
    start_time = factory.LazyFunction(timezone.now)
    end_time = None
    shared_with_admin = False
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)

    class Params:
        ended = factory.Trait(
            end_time=factory.LazyAttribute(
                lambda o: (
                    o.start_time + timedelta(minutes=random.randint(10, 30))
                    if o.start_time
                    else timezone.now()
                )
            )
        )
