# Generated by Django 5.2 on 2025-05-04 22:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('challenges', '0001_initial'),
        ('learning', '0003_skill_is_active'),
        ('study', '0010_remove_userquestionattempt_used_solution_method_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='userquestionattempt',
            name='unique_user_question_per_test_attempt',
        ),
        migrations.RemoveConstraint(
            model_name='userquestionattempt',
            name='unique_user_question_per_challenge_attempt',
        ),
        migrations.AlterField(
            model_name='conversationmessage',
            name='related_question',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='learning.question', verbose_name='related question'),
        ),
        migrations.AlterField(
            model_name='conversationsession',
            name='current_topic_question',
            field=models.ForeignKey(blank=True, help_text='The question/concept currently being focused on.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='learning.question', verbose_name='current topic question'),
        ),
        migrations.AlterField(
            model_name='emergencymodesession',
            name='suggested_plan',
            field=models.JSONField(blank=True, help_text='Stores plan details: {"focus_skills": ["slug1", ...], "recommended_questions": N, "quick_review_topics": [...]}', null=True, verbose_name='suggested plan'),
        ),
        migrations.AlterField(
            model_name='userquestionattempt',
            name='emergency_session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_attempts', to='study.emergencymodesession', verbose_name='emergency mode session'),
        ),
        migrations.AlterField(
            model_name='usertestattempt',
            name='completion_points_awarded',
            field=models.BooleanField(default=False, help_text='Tracks if gamification points for completing this attempt have been awarded.', verbose_name='completion points awarded'),
        ),
        migrations.AlterField(
            model_name='usertestattempt',
            name='test_configuration',
            field=models.JSONField(blank=True, help_text='Snapshot of the configuration used to generate this attempt (e.g., sections, skills, num_questions). Ensure consistent structure.', null=True, verbose_name='test configuration snapshot'),
        ),
        migrations.AlterField(
            model_name='usertestattempt',
            name='test_definition',
            field=models.ForeignKey(blank=True, help_text='The Test Definition used for this attempt, if based on one.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attempts', to='study.test', verbose_name='test definition used'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['challenge_attempt', 'question'], name='study_userq_challen_49ab2a_idx'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['conversation_session', 'question'], name='study_userq_convers_59ce67_idx'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['emergency_session', 'question'], name='study_userq_emergen_0c0e1a_idx'),
        ),
        migrations.AddConstraint(
            model_name='userquestionattempt',
            constraint=models.UniqueConstraint(condition=models.Q(('test_attempt__isnull', False)), fields=('user', 'question', 'test_attempt'), name='uq_user_question_per_test_attempt'),
        ),
        migrations.AddConstraint(
            model_name='userquestionattempt',
            constraint=models.UniqueConstraint(condition=models.Q(('challenge_attempt__isnull', False)), fields=('user', 'question', 'challenge_attempt'), name='uq_user_question_per_challenge_attempt'),
        ),
        migrations.AddConstraint(
            model_name='userquestionattempt',
            constraint=models.UniqueConstraint(condition=models.Q(('conversation_session__isnull', False)), fields=('user', 'question', 'conversation_session'), name='uq_user_question_per_conversation'),
        ),
    ]
