import pytest
from apps.learning.tests.factories import (
    LearningSectionFactory,
    LearningSubSectionFactory,
    QuestionFactory,
    SkillFactory,  # Add SkillFactory import
)
from apps.learning.models import (
    Question,
    LearningSubSection,
    Skill,
)  # Add Skill model import

# No UserProfile/UserFactory imports needed here if they are in root conftest


# Keep the setup_learning_content fixture as it's generally useful.
# Consider adding Skill creation here if consistently needed across study tests.
@pytest.fixture
def setup_learning_content(db):
    """Fixture to create necessary learning sections, subsections, skills and questions."""
    verbal_section = LearningSectionFactory(name="Verbal Section", slug="verbal")
    quant_section = LearningSectionFactory(
        name="Quantitative Section", slug="quantitative"
    )

    # Subsections
    reading_comp_sub = LearningSubSectionFactory(
        section=verbal_section, name="Reading Comp", slug="reading-comp"
    )
    analogy_sub = LearningSubSectionFactory(
        section=verbal_section, name="Analogy", slug="analogy"
    )
    algebra_sub = LearningSubSectionFactory(
        section=quant_section, name="Algebra", slug="algebra"
    )
    geometry_sub = LearningSubSectionFactory(
        section=quant_section, name="Geometry", slug="geometry"
    )

    # Skills (Optional but good for testing skill-related features)
    reading_skill = SkillFactory(
        subsection=reading_comp_sub, name="Main Idea", slug="main-idea"
    )
    algebra_skill = SkillFactory(
        subsection=algebra_sub, name="Linear Equations", slug="linear-equations"
    )
    geometry_skill = SkillFactory(
        subsection=geometry_sub, name="Area Calculation", slug="area-calculation"
    )

    # Questions (Assign skills where appropriate)
    QuestionFactory.create_batch(
        15, subsection=reading_comp_sub, skill=reading_skill, is_active=True
    )
    QuestionFactory.create_batch(
        15, subsection=analogy_sub, is_active=True
    )  # No specific skill assigned here
    QuestionFactory.create_batch(
        15, subsection=algebra_sub, skill=algebra_skill, is_active=True
    )
    QuestionFactory.create_batch(
        15, subsection=geometry_sub, skill=geometry_skill, is_active=True
    )
    QuestionFactory.create_batch(5, subsection=analogy_sub, skill=None, is_active=True)
    QuestionFactory.create_batch(5, subsection=algebra_sub, skill=None, is_active=True)

    # print(f"Setup Learning Content: Created {Question.objects.count()} questions.")

    return {
        "verbal_section": verbal_section,
        "quant_section": quant_section,
        "reading_comp_sub": reading_comp_sub,
        "algebra_sub": algebra_sub,
        "geometry_sub": geometry_sub,
        "reading_skill": reading_skill,
        "algebra_skill": algebra_skill,
        "geometry_skill": geometry_skill,
    }


# Add other study-specific fixtures if needed, e.g., a pre-started EmergencyModeSession
