# qader_backend/apps/study/api/views/__init__.py
from .level_assessment import LevelAssessmentStartView, LevelAssessmentSubmitView
from .traditional import (
    TraditionalLearningQuestionListView,
    TraditionalLearningAnswerView,
)
from .tests import (
    UserTestAttemptListView,
    StartTestAttemptView,
    UserTestAttemptDetailView,
    SubmitTestAttemptView,
    ReviewTestAttemptView,
    RetakeSimilarTestAttemptView,
)
from .statistics import UserStatisticsView

__all__ = [
    # Level Assessment
    "LevelAssessmentStartView",
    "LevelAssessmentSubmitView",
    # Traditional Learning
    "TraditionalLearningQuestionListView",
    "TraditionalLearningAnswerView",
    # Tests
    "UserTestAttemptListView",
    "StartTestAttemptView",
    "UserTestAttemptDetailView",
    "SubmitTestAttemptView",
    "ReviewTestAttemptView",
    "RetakeSimilarTestAttemptView",
    # Statistics
    "UserStatisticsView",
]
