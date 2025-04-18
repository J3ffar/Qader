# qader_backend/apps/study/tests/factories.py
import factory
from factory.django import DjangoModelFactory
from django.utils import timezone
from datetime import timedelta
import random

# Use specific imports for clarity
from apps.learning.tests.factories import QuestionFactory, SkillFactory
from apps.users.tests.factories import UserFactory
from apps.study.models import UserQuestionAttempt, UserSkillProficiency, UserTestAttempt
from apps.learning.models import LearningSubSection, Question  # Needed for helper


class UserSkillProficiencyFactory(DjangoModelFactory):
    class Meta:
        model = UserSkillProficiency
        django_get_or_create = ("user", "skill")  # Avoid duplicates

    user = factory.SubFactory(UserFactory)
    skill = factory.SubFactory(SkillFactory)
    proficiency_score = factory.Faker(
        "pyfloat", left_digits=1, right_digits=4, min_value=0.0, max_value=1.0
    )
    attempts_count = factory.Faker("random_int", min=1, max=50)
    # Simplified correct_count using random.randint which works fine in LazyAttribute
    correct_count = factory.LazyAttribute(
        lambda o: random.randint(0, o.attempts_count) if o.attempts_count > 0 else 0
    )
    last_calculated_at = factory.LazyFunction(timezone.now)


class UserTestAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserTestAttempt

    user = factory.SubFactory(UserFactory)
    attempt_type = UserTestAttempt.AttemptType.PRACTICE  # Default type
    test_definition = None  # Default to no predefined test
    # Default to a simple, valid config structure for dynamic tests
    test_configuration = factory.LazyFunction(
        lambda: {
            "config": {
                "name": "Factory Default Test",
                "subsections": [],
                "skills": [],
                "num_questions": 5,
                "actual_num_questions_selected": 0,  # Updated when questions are assigned
                "starred": False,
                "not_mastered": False,
                "full_simulation": False,
            }
        }
    )
    question_ids = factory.LazyFunction(
        list
    )  # Should be populated after creation if needed
    status = UserTestAttempt.Status.STARTED
    start_time = factory.LazyFunction(timezone.now)
    end_time = None
    score_percentage = None
    score_verbal = None
    score_quantitative = None
    results_summary = None

    class Params:
        # Trait for completed state
        completed = factory.Trait(
            status=UserTestAttempt.Status.COMPLETED,
            end_time=factory.LazyAttribute(
                lambda o: o.start_time + timedelta(minutes=random.randint(5, 20))
            ),
            # Default score, can be overridden or calculated later
            score_percentage=factory.Faker(
                "pyfloat", left_digits=2, right_digits=1, min_value=50.0, max_value=99.9
            ),
            # Placeholder results summary, better calculated based on actual questions/answers
            results_summary=factory.LazyAttribute(
                lambda o: {
                    "placeholder_section": {
                        "correct": 3,
                        "total": 5,
                        "score": 60.0,
                        "name": "Placeholder Section",
                    }
                }
            ),
        )
        # Traits for specific types
        level_assessment = factory.Trait(
            attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,
            test_configuration=factory.LazyFunction(
                lambda: {  # Use LazyFunction for dynamic dict
                    "sections_requested": ["verbal", "quantitative"],
                    "num_questions_requested": 10,
                    "actual_num_questions_selected": 0,
                }
            ),
        )
        practice = factory.Trait(attempt_type=UserTestAttempt.AttemptType.PRACTICE)
        simulation = factory.Trait(attempt_type=UserTestAttempt.AttemptType.SIMULATION)


class UserQuestionAttemptFactory(DjangoModelFactory):
    class Meta:
        model = UserQuestionAttempt

    user = factory.SubFactory(UserFactory)
    question = factory.SubFactory(QuestionFactory)
    # Only link test_attempt if mode requires it (set explicitly or via trait)
    test_attempt = None
    selected_answer = factory.Iterator(["A", "B", "C", "D"])
    is_correct = factory.LazyAttribute(
        lambda o: o.selected_answer == o.question.correct_answer
    )
    time_taken_seconds = factory.Faker("random_int", min=10, max=120)
    # Default mode, can be overridden
    mode = UserQuestionAttempt.Mode.TRADITIONAL
    attempted_at = factory.LazyFunction(timezone.now)

    class Params:
        # Trait for linking to a test attempt and setting mode
        in_test = factory.Trait(
            test_attempt=factory.SubFactory(
                UserTestAttemptFactory, user=factory.SelfAttribute("....user")
            ),
            mode=UserQuestionAttempt.Mode.TEST,  # Default mode when in test
        )
        in_level_assessment = factory.Trait(
            test_attempt=factory.SubFactory(
                UserTestAttemptFactory,
                user=factory.SelfAttribute("....user"),
                attempt_type=UserTestAttempt.AttemptType.LEVEL_ASSESSMENT,  # Ensure attempt type matches
            ),
            mode=UserQuestionAttempt.Mode.LEVEL_ASSESSMENT,
        )
        correct = factory.Trait(
            selected_answer=factory.LazyAttribute(lambda o: o.question.correct_answer),
            is_correct=True,
        )
        incorrect = factory.Trait(
            # Ensure incorrect answer is different from correct one
            selected_answer=factory.LazyAttribute(
                lambda o: next(
                    c for c in ["A", "B", "C", "D"] if c != o.question.correct_answer
                )
            ),
            is_correct=False,
        )


# Helper function to create a realistic completed test attempt scenario
def create_completed_attempt(
    user,
    num_questions=5,
    num_correct=3,
    attempt_type=UserTestAttempt.AttemptType.PRACTICE,
):
    """Creates a completed UserTestAttempt with related UserQuestionAttempts and calculated scores."""
    if num_correct > num_questions:
        raise ValueError("num_correct cannot be greater than num_questions")

    questions = QuestionFactory.create_batch(num_questions)
    question_ids = [q.id for q in questions]

    # Define a basic config based on the first question's subsection
    first_q_subsection = questions[0].subsection if questions else None
    subsection_slug = (
        first_q_subsection.slug if first_q_subsection else "default-subsection"
    )
    subsection_name = (
        first_q_subsection.name if first_q_subsection else "Default Subsection"
    )
    section_slug = (
        first_q_subsection.section.slug
        if first_q_subsection and first_q_subsection.section
        else "unknown"
    )

    config_snapshot = {
        "test_type": attempt_type.value,  # Store value
        "config": {
            "name": f"Completed {attempt_type.label} Test",
            "subsections": [subsection_slug],
            "skills": [],
            "num_questions": num_questions,
            "actual_num_questions_selected": len(question_ids),
            "starred": False,
            "not_mastered": False,
            "full_simulation": False,
        },
    }

    # Create the attempt first (without scores)
    attempt = UserTestAttemptFactory(
        user=user,
        status=UserTestAttempt.Status.STARTED,  # Start as started
        attempt_type=attempt_type,
        question_ids=question_ids,
        test_configuration=config_snapshot,
    )

    # Create related question attempts
    created_attempts = []
    for i, q in enumerate(questions):
        is_correct_flag = i < num_correct
        selected = (
            q.correct_answer
            if is_correct_flag
            else next(c for c in ["A", "B", "C", "D"] if c != q.correct_answer)
        )
        mode = (
            UserQuestionAttempt.Mode.LEVEL_ASSESSMENT
            if attempt_type == UserTestAttempt.AttemptType.LEVEL_ASSESSMENT
            else UserQuestionAttempt.Mode.TEST
        )
        qa = UserQuestionAttemptFactory(
            user=user,
            question=q,
            test_attempt=attempt,
            selected_answer=selected,
            is_correct=is_correct_flag,
            mode=mode,
            attempted_at=attempt.start_time
            + timedelta(seconds=random.randint(10, 50) * i),
        )
        created_attempts.append(qa)

    # Now calculate and save scores using the model method
    attempt.calculate_and_save_scores(created_attempts)

    # Mark as completed
    attempt.status = UserTestAttempt.Status.COMPLETED
    attempt.end_time = attempt.start_time + timedelta(minutes=random.randint(5, 15))
    attempt.save(update_fields=["status", "end_time", "updated_at"])

    attempt.refresh_from_db()  # Ensure final state is loaded
    return attempt, questions
