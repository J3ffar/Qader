# qader_backend/apps/study/tests/conftest.py
import pytest
from apps.learning.tests.factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    QuestionFactory,
)
from apps.learning.models import LearningSection, LearningSubSection, Question
from apps.users.models import (
    UserProfile,
)  # Import needed models if factories use them implicitly
from apps.users.tests.factories import (
    UserFactory,
)  # Import if needed by other fixtures here


@pytest.fixture
def setup_learning_content(db):  # Add 'db' fixture dependency
    """Fixture to create necessary learning sections, subsections, and questions."""
    verbal_section = LearningSectionFactory(name="Verbal Section", slug="verbal")
    quant_section = LearningSectionFactory(
        name="Quantitative Section", slug="quantitative"
    )

    verbal_sub1 = LearningSubSectionFactory(
        section=verbal_section, name="Reading Comp", slug="reading-comp"
    )
    verbal_sub2 = LearningSubSectionFactory(
        section=verbal_section, name="Analogy", slug="analogy"
    )
    quant_sub1 = LearningSubSectionFactory(
        section=quant_section, name="Algebra", slug="algebra"
    )
    quant_sub2 = LearningSubSectionFactory(
        section=quant_section, name="Geometry", slug="geometry"
    )

    # Create enough questions for testing pagination and selection
    # Make sure they are active
    QuestionFactory.create_batch(15, subsection=verbal_sub1, is_active=True)
    QuestionFactory.create_batch(15, subsection=verbal_sub2, is_active=True)
    QuestionFactory.create_batch(15, subsection=quant_sub1, is_active=True)
    QuestionFactory.create_batch(15, subsection=quant_sub2, is_active=True)

    # Add a print statement for debugging if needed
    # print(f"Setup Learning Content: Created {Question.objects.count()} questions.")

    return {
        "verbal_section": verbal_section,
        "quant_section": quant_section,
    }


# Add other fixtures specific to the 'study' app tests here if needed
