from django.conf import settings
from django.utils.translation import gettext_lazy as _

# --- Proficiency & Question Filtering ---
DEFAULT_PROFICIENCY_THRESHOLD = getattr(settings, "DEFAULT_PROFICIENCY_THRESHOLD", 0.7)

# --- Emergency Mode ---
EMERGENCY_MODE_DEFAULT_QUESTIONS = getattr(
    settings, "EMERGENCY_MODE_DEFAULT_QUESTIONS", 15
)
EMERGENCY_MODE_WEAK_SKILL_COUNT = getattr(
    settings, "EMERGENCY_MODE_WEAK_SKILL_COUNT", 7
)
EMERGENCY_MODE_MIN_QUESTIONS = getattr(settings, "EMERGENCY_MODE_MIN_QUESTIONS", 5)
EMERGENCY_MODE_ESTIMATED_MINS_PER_Q = getattr(
    settings, "EMERGENCY_MODE_ESTIMATED_MINS_PER_Q", 2.5
)
DEFAULT_EMERGENCY_TIPS = [
    _("Take deep breaths before starting."),
    _("Focus on one question at a time."),
    _("Read questions carefully."),
    _("Manage your time effectively, but don't rush needlessly."),
    _("Trust your preparation and stay positive!"),
]


# --- Test Analysis & Scoring ---
LEVEL_ASSESSMENT_SCORE_THRESHOLD = getattr(
    settings, "LEVEL_ASSESSMENT_SCORE_THRESHOLD", 60
)
AI_ANALYSIS_DEFAULT_FALLBACK = _(
    "Test completed! Review your detailed results to identify areas for improvement."
)
AI_ANALYSIS_LOW_SCORE_THRESHOLD = getattr(
    settings, "AI_ANALYSIS_LOW_SCORE_THRESHOLD", 50
)
AI_ANALYSIS_HIGH_SCORE_THRESHOLD = getattr(
    settings, "AI_ANALYSIS_HIGH_SCORE_THRESHOLD", 85
)
AI_ANALYSIS_MAX_ANSWER_DETAILS = getattr(settings, "AI_ANALYSIS_MAX_ANSWER_DETAILS", 10)
