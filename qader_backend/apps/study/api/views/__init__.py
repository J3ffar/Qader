from .level_assessment import LevelAssessmentStartView
from .tests import (
    UserTestAttemptListView,
    StartTestAttemptView,
    UserTestAttemptDetailView,
    ReviewTestAttemptView,
    RetakeSimilarTestAttemptView,
)
from .statistics import UserStatisticsView
from .emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeAnswerView,
)
from .attempts import (
    TestAttemptAnswerView,
    CompleteTestAttemptView,
    CancelTestAttemptView,
    StartTraditionalAttemptView,  # <-- ADD
    RevealAnswerView,  # <-- ADD
    EndTraditionalAttemptView,
)

__all__ = [
    # Level Assessment
    "LevelAssessmentStartView",
    # Traditional Learning
    "StartTraditionalAttemptView",
    "EndTraditionalAttemptView",
    "ReviewTestAttemptView",
    "RetakeSimilarTestAttemptView",
    # --- In-Progress Helpers ---
    "RevealAnswerView",
    # Tests
    "StartTestAttemptView",  # Start Practice/Simulation
    "UserTestAttemptListView",  # List all attempt types
    "UserTestAttemptDetailView",  # Detail for any attempt type
    "TestAttemptAnswerView",  # NEW: Submit single answer (any type)
    "CompleteTestAttemptView",  # NEW: Complete attempt (any type)
    "CancelTestAttemptView",  # NEW: Cancel attempt (any type)
    "ReviewTestAttemptView",  # Review completed attempt (any type)
    "RetakeSimilarTestAttemptView",
    # Statistics
    "UserStatisticsView",
    # Emergency Mode
    "EmergencyModeStartView",
    "EmergencyModeSessionUpdateView",
    "EmergencyModeAnswerView",
]
