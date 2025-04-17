from datetime import datetime
import factory
from factory.django import DjangoModelFactory
from django.conf import settings
from django.utils import timezone
from factory.faker import Faker
from apps.learning.tests.factories import (
    LearningSubSectionFactory,
    QuestionFactory,
    SkillFactory,
)
import random

# Import UserFactory if not globally available in tests
from apps.users.tests.factories import UserFactory
from apps.study.models import UserQuestionAttempt, UserSkillProficiency, UserTestAttempt
from apps.learning.models import LearningSubSection


class UserSkillProficiencyFactory(DjangoModelFactory):
    class Meta:
        model = UserSkillProficiency
        django_get_or_create = ("user", "skill")  # Avoid duplicates

    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_score = factory.Faker(
        "pyfloat", left_digits=1, right_digits=2, min_value=0.0, max_value=1.0
    )
    attempts_count = factory.Faker("random_int", min=1, max=50)
    # --- FIX: Correct usage of Faker within LazyAttribute ---
    correct_count = factory.LazyAttribute(
        # Use Python's random which is often simpler and less prone to evaluation context issues
        lambda o: random.randint(0, o.attempts_count if o.attempts_count > 0 else 0)
        # Ensure max >= min for randint
    )


class UserTestAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserTestAttempt

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    attempt_type = UserTestAttempt.AttemptType.PRACTICE

    # Default to a simple, valid config structure
    test_configuration = factory.LazyFunction(
        lambda: {
            "config": {
                "name": "Factory Default Test",
                "subsections": [],  # Default to empty list
                "num_questions": 5,
                "actual_num_questions_selected": 0,  # Start at 0
                "starred": False,
                "not_mastered": False,
                "full_simulation": False,
            }
        }
    )
    question_ids = factory.LazyFunction(list)
    status = UserTestAttempt.Status.STARTED
    start_time = factory.LazyFunction(timezone.now)

    class Params:
        completed = factory.Trait(
            status=UserTestAttempt.Status.COMPLETED,
            end_time=factory.LazyFunction(
                lambda o: (
                    o.start_time + datetime.timedelta(minutes=10)
                    if o.start_time
                    else timezone.now() + datetime.timedelta(minutes=10)
                )
            ),
            score_percentage=factory.Faker(
                "pyfloat", left_digits=2, right_digits=1, min_value=60, max_value=95
            ),
            # --- FIX: Make results_summary more robust ---
            results_summary=factory.LazyFunction(
                lambda o: {
                    # Use .get() with defaults for safer access
                    o.test_configuration.get("config", {}).get(
                        "subsections", ["unknown_section"]
                    )[0]: (
                        {
                            "correct": 3,  # Default correct count for the factory trait
                            # Safely get question_ids length, default to config num_questions or 5
                            "total": (
                                len(o.question_ids)
                                if o.question_ids
                                else o.test_configuration.get("config", {}).get(
                                    "num_questions", 5
                                )
                            ),
                            "score": 60.0,  # Default score for the factory trait
                        }
                    )
                }
            ),
        )
        level_assessment = factory.Trait(
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            test_configuration={
                "num_questions_requested": 10,
                "actual_num_questions_selected": 10,
            },
        )
        practice = factory.Trait(attempt_type=UserTestAttempt.AttemptType.PRACTICE)
        simulation = factory.Trait(attempt_type=UserTestAttempt.AttemptType.SIMULATION)


class UserQuestionAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionAttempt

    user = factory.SubFactory("apps.users.tests.factories.UserFactory")
    question = factory.SubFactory(QuestionFactory)
    # Link to a test attempt if mode is 'test' or 'level_assessment'
    test_attempt = factory.SubFactory(
        UserTestAttemptFactory, user=factory.SelfAttribute("..user")
    )
    selected_answer = factory.Iterator(["A", "B", "C", "D"])
    is_correct = factory.LazyAttribute(
        lambda o: o.selected_answer == o.question.correct_answer
    )
    time_taken_seconds = factory.Faker("random_int", min=10, max=120)
    mode = factory.LazyAttribute(
        lambda o: (
            UserQuestionAttempt.Mode.LEVEL_ASSESSMENT
            if o.test_attempt
            and o.test_attempt.attempt_type
            == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            else (
                UserQuestionAttempt.Mode.TEST
                if o.test_attempt
                else UserQuestionAttempt.Mode.TRADITIONAL
            )
        )  # Default if no test_attempt
    )
    attempted_at = factory.LazyFunction(timezone.now)

    class Params:
        correct = factory.Trait(
            selected_answer=factory.LazyAttribute(lambda o: o.question.correct_answer),
            is_correct=True,
        )
        incorrect = factory.Trait(
            selected_answer=factory.LazyAttribute(
                lambda o: ("B" if o.question.correct_answer == "A" else "A")
            ),
            is_correct=False,
        )


def create_completed_attempt(
    user,
    num_questions=5,
    num_correct=3,
    attempt_type=UserTestAttempt.AttemptType.PRACTICE,
):
    """Creates a completed UserTestAttempt with related UserQuestionAttempts."""
    questions = QuestionFactory.create_batch(num_questions)
    question_ids = [q.id for q in questions]

    # --- FIX: Ensure a valid base config is always passed ---
    default_subsection_slug = (
        questions[0].subsection.slug
        if questions and questions[0].subsection
        else "default-subsection"
    )
    config_override = {
        "config": {
            "name": f"{attempt_type.label} Test",
            "subsections": [
                default_subsection_slug
            ],  # Ensure subsections list is not empty
            "skills": [],
            "num_questions": num_questions,
            "actual_num_questions_selected": len(question_ids),
            "starred": False,
            "not_mastered": False,
            "full_simulation": False,  # Add missing fields if needed
        }
    }

    # Pass the specific overrides needed for the completed state
    attempt = UserTestAttemptFactory(
        user=user,
        completed=True,  # Apply the trait
        attempt_type=attempt_type,
        question_ids=question_ids,
        test_configuration=config_override,  # Override the default config
        # Let the trait handle score/results_summary, but based on the provided config/questions
        # Adjust score/results within the helper if trait defaults are not sufficient
        score_percentage=(
            round((num_correct / num_questions * 100.0), 1)
            if num_questions > 0
            else 0.0
        ),
        results_summary={  # Manually set results summary based on inputs
            config_override["config"]["subsections"][0]: {
                "correct": num_correct,
                "total": num_questions,
                "score": (
                    round((num_correct / num_questions * 100.0), 1)
                    if num_questions > 0
                    else 0.0
                ),
                "name": LearningSubSection.objects.get(
                    slug=config_override["config"]["subsections"][0]
                ).name,  # Get name if needed
            }
        },
    )

    # Create related question attempts
    for i, q in enumerate(questions):
        # ... (rest of UserQuestionAttemptFactory creation as before) ...
        is_correct_flag = i < num_correct
        selected = (
            q.correct_answer
            if is_correct_flag
            else ("B" if q.correct_answer == "A" else "A")
        )
        mode = (
            UserQuestionAttempt.Mode.LEVEL_ASSESSMENT
            if attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            else UserQuestionAttempt.Mode.TEST
        )
        UserQuestionAttemptFactory(
            user=user,
            question=q,
            test_attempt=attempt,
            selected_answer=selected,
            is_correct=is_correct_flag,
            mode=mode,
            attempted_at=attempt.start_time + datetime.timedelta(seconds=30 * i),
        )
    # Optional: Recalculate score if trait might be inaccurate
    # attempt.score_percentage = round((num_correct / num_questions * 100), 1) if num_questions > 0 else 0.0
    # attempt.save(update_fields=['score_percentage'])

    return attempt, questions
