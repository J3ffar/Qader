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
from .emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeAnswerView,
)

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
    # Emergency Mode
    "EmergencyModeStartView",
    "EmergencyModeSessionUpdateView",
    "EmergencyModeAnswerView",
]
