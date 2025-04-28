from django.urls import path
from apps.study.api.views import traditional as views

urlpatterns = [
    path(
        "",  # Path relative to /api/v1/study/start/traditional/
        views.TraditionalPracticeStartView.as_view(),
        name="start-traditional",
    ),
    path(
        "end/<int:attempt_id>/",  # Moved attempt_id here from base path
        views.TraditionalPracticeEndView.as_view(),
        name="end-traditional",
    ),
    path(
        "questions/",  # Fetch questions on demand (no attempt context)
        views.TraditionalQuestionListView.as_view(),
        name="traditional-question-list",
    ),
    path(
        "attempts/<int:attempt_id>/questions/<int:question_id>/reveal/",
        views.TraditionalRevealAnswerView.as_view(),
        name="traditional-reveal-answer",
    ),
]
