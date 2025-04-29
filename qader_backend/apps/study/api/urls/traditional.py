from django.urls import path
from apps.study.api.views import traditional as views

urlpatterns = [
    path(
        "",  # Path relative to /api/v1/study/start/traditional/
        views.TraditionalPracticeStartView.as_view(),
        name="start-traditional",
    ),
    path(
        "questions/",  # Fetch questions on demand (no attempt context)
        views.TraditionalQuestionListView.as_view(),
        name="traditional-question-list",
    ),
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/hint/",
        views.TraditionalUseHintView.as_view(),
        name="traditional-use-hint",
    ),
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/eliminate/",
        views.TraditionalUseEliminationView.as_view(),
        name="traditional-use-eliminate",
    ),
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/reveal-answer/",
        views.TraditionalRevealAnswerView.as_view(),
        name="traditional-reveal-answer",
    ),
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/reveal-explanation/",
        views.TraditionalRevealExplanationView.as_view(),
        name="traditional-reveal-explanation",
    ),
]
