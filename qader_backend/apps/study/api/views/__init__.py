# --- Core Attempts ---
from .attempts import (
    UserTestAttemptListView,
    UserTestAttemptDetailView,
    UserTestAttemptAnswerView,
    UserTestAttemptCompleteView,
    UserTestAttemptCancelView,
    UserTestAttemptReviewView,
    UserTestAttemptRetakeView,
)

# --- Specific Start Views ---
from .level_assessment import LevelAssessmentStartView
from .practice_simulation import PracticeSimulationStartView
from .traditional import TraditionalPracticeStartView

# --- Traditional Specific Actions ---
from .traditional import (
    TraditionalPracticeEndView,
    TraditionalQuestionListView,
    TraditionalRevealAnswerView,
)
from .level_assessment import LevelAssessmentStartView

from .statistics import UserStatisticsView
from .emergency import (
    EmergencyModeStartView,
    EmergencyModeSessionUpdateView,
    EmergencyModeAnswerView,
)

__all__ = [
    # --- Core Attempts ---
    "UserTestAttemptListView",
    "UserTestAttemptDetailView",
    "UserTestAttemptAnswerView",  # Unified Answer
    "UserTestAttemptCompleteView",  # Unified Complete
    "UserTestAttemptCancelView",  # Unified Cancel
    "UserTestAttemptReviewView",  # Unified Review
    "UserTestAttemptRetakeView",  # Unified Retake
    # --- Start Views ---
    "LevelAssessmentStartView",
    "PracticeSimulationStartView",
    "TraditionalPracticeStartView",
    # --- Traditional Practice ---
    "TraditionalPracticeEndView",
    "TraditionalQuestionListView",  # Standalone question fetch
    "TraditionalRevealAnswerView",
    # Statistics
    "UserStatisticsView",
    # Emergency Mode
    "EmergencyModeStartView",
    "EmergencyModeSessionUpdateView",
    "EmergencyModeAnswerView",
]
