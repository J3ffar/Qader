from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.users.models import UserProfile, RoleChoices


class Conversation(models.Model):
    student = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_student",
        verbose_name=_("Student Profile"),
        limit_choices_to={"role": RoleChoices.STUDENT},
    )
    teacher = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="chat_conversations_as_teacher",
        verbose_name=_("Teacher/Trainer Profile"),
        limit_choices_to={"role__in": [RoleChoices.TEACHER, RoleChoices.TRAINER]},
    )
    created_at = models.DateTimeField(_("Created At"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Last Message At"), auto_now=True)

    class Meta:
        verbose_name = _("Conversation")
        verbose_name_plural = _("Conversations")
        unique_together = ("student", "teacher")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat between {self.student.user.username} and {self.teacher.user.username}"

    def clean(self):
        super().clean()
        if self.student_id and self.teacher_id:
            if self.student.role != RoleChoices.STUDENT:
                raise ValidationError(_("The 'student' must have the role of STUDENT."))
            if self.teacher.role not in [RoleChoices.TEACHER, RoleChoices.TRAINER]:
                raise ValidationError(
                    _("The 'teacher' must have the role of TEACHER or TRAINER.")
                )
            if self.student.assigned_mentor != self.teacher:
                raise ValidationError(
                    f"Conversation can only be between student '{self.student.user.username}' and "
                    f"their assigned mentor '{self.student.assigned_mentor.user.username if self.student.assigned_mentor else 'None'}'. "
                    f"Attempted with teacher '{self.teacher.user.username}'."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_or_create_conversation(
        cls, student_profile: UserProfile, teacher_profile: UserProfile
    ) -> tuple["Conversation", bool]:
        if not student_profile or student_profile.role != RoleChoices.STUDENT:
            raise ValueError("Invalid student profile provided.")
        if not teacher_profile or teacher_profile.role not in [
            RoleChoices.TEACHER,
            RoleChoices.TRAINER,
        ]:
            raise ValueError("Invalid teacher profile provided.")
        if student_profile.assigned_mentor != teacher_profile:
            raise PermissionError(
                "Cannot create or get conversation: The teacher is not the student's assigned mentor."
            )
        # The clean method will be called upon saving if 'created' is True
        conversation, created = cls.objects.get_or_create(
            student=student_profile, teacher=teacher_profile
        )
        return conversation, created


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Conversation"),
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
        verbose_name=_("Sender"),
    )
    content = models.TextField(_("Content"))
    timestamp = models.DateTimeField(_("Timestamp"), auto_now_add=True, db_index=True)
    is_read = models.BooleanField(_("Is Read?"), default=False)

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["timestamp"]

    def __str__(self):
        return f"Message from {self.sender.username} in Conv ID {self.conversation.id} at {self.timestamp}"

    def clean(self):
        super().clean()
        if not (
            self.sender == self.conversation.student.user
            or self.sender == self.conversation.teacher.user
        ):
            raise ValidationError(
                _("Sender must be a participant in the conversation.")
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.conversation.updated_at = self.timestamp
            self.conversation.save(update_fields=["updated_at"])
