# Generated by Django 5.2 on 2025-04-16 17:05

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('learning', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TestDefinition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Test Name')),
                ('slug', models.SlugField(help_text='Unique identifier for API usage', max_length=255, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('test_type', models.CharField(choices=[('level_assessment', 'Level Assessment'), ('practice', 'Practice Set'), ('simulation', 'Simulation'), ('custom', 'Custom Test'), ('challenge', 'Challenge')], db_index=True, default='practice', max_length=20, verbose_name='Test Type')),
                ('default_configuration', models.JSONField(blank=True, help_text='e.g., {"num_questions": 30, "sections": ["verbal", "quantitative"]}', null=True, verbose_name='Default Configuration')),
                ('is_active', models.BooleanField(default=True, help_text='Whether this test definition can be used.', verbose_name='Is Active')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Test Definition',
                'verbose_name_plural': 'Test Definitions',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='UserTestAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('configuration', models.JSONField(blank=True, null=True, verbose_name='Test Configuration Used')),
                ('status', models.CharField(choices=[('started', 'Started'), ('completed', 'Completed'), ('abandoned', 'Abandoned')], db_index=True, default='started', max_length=15, verbose_name='Status')),
                ('start_time', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Start Time')),
                ('end_time', models.DateTimeField(blank=True, null=True, verbose_name='End Time')),
                ('score_percentage', models.FloatField(blank=True, null=True, verbose_name='Score Percentage')),
                ('score_verbal', models.FloatField(blank=True, null=True, verbose_name='Verbal Score')),
                ('score_quantitative', models.FloatField(blank=True, null=True, verbose_name='Quantitative Score')),
                ('results_summary', models.JSONField(blank=True, null=True, verbose_name='Results Summary')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('test_definition', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='attempts', to='study.testdefinition', verbose_name='Test Definition')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='test_attempts', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User Test Attempt',
                'verbose_name_plural': 'User Test Attempts',
                'ordering': ['-start_time'],
            },
        ),
        migrations.CreateModel(
            name='UserQuestionAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('selected_answer', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, verbose_name='Selected Answer')),
                ('is_correct', models.BooleanField(verbose_name='Is Correct')),
                ('time_taken_seconds', models.PositiveIntegerField(blank=True, null=True, verbose_name='Time Taken (seconds)')),
                ('used_hint', models.BooleanField(default=False, verbose_name='Used Hint')),
                ('used_elimination', models.BooleanField(default=False, verbose_name='Used Elimination')),
                ('used_solution_method', models.BooleanField(default=False, verbose_name='Used Solution Method')),
                ('mode', models.CharField(choices=[('traditional', 'Traditional Learning'), ('test', 'Test'), ('emergency', 'Emergency Mode'), ('conversation', 'Conversational Learning'), ('challenge', 'Challenge')], db_index=True, max_length=20, verbose_name='Attempt Mode')),
                ('attempted_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name='Attempted At')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_attempts', to='learning.question', verbose_name='Question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='question_attempts', to=settings.AUTH_USER_MODEL, verbose_name='User')),
                ('test_attempt', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='question_attempts', to='study.usertestattempt', verbose_name='Test Attempt')),
            ],
            options={
                'verbose_name': 'User Question Attempt',
                'verbose_name_plural': 'User Question Attempts',
                'ordering': ['-attempted_at'],
            },
        ),
        migrations.CreateModel(
            name='UserSkillProficiency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('proficiency_score', models.FloatField(default=0.0, verbose_name='Proficiency Score')),
                ('attempts_count', models.PositiveIntegerField(default=0, verbose_name='Attempts Count')),
                ('correct_count', models.PositiveIntegerField(default=0, verbose_name='Correct Count')),
                ('last_calculated_at', models.DateTimeField(auto_now=True, verbose_name='Last Calculated At')),
                ('skill', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_proficiencies', to='learning.skill', verbose_name='Skill')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skill_proficiencies', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'User Skill Proficiency',
                'verbose_name_plural': 'User Skill Proficiencies',
                'ordering': ['user', 'skill'],
                'indexes': [models.Index(fields=['user', 'skill'], name='study_users_user_id_32dbe3_idx')],
                'unique_together': {('user', 'skill')},
            },
        ),
        migrations.AddIndex(
            model_name='usertestattempt',
            index=models.Index(fields=['user', 'test_definition'], name='study_usert_user_id_72919d_idx'),
        ),
        migrations.AddIndex(
            model_name='usertestattempt',
            index=models.Index(fields=['user', 'status'], name='study_usert_user_id_9729f5_idx'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['user', 'question'], name='study_userq_user_id_263e08_idx'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['user', 'mode'], name='study_userq_user_id_d2ed12_idx'),
        ),
        migrations.AddIndex(
            model_name='userquestionattempt',
            index=models.Index(fields=['test_attempt'], name='study_userq_test_at_9c8b08_idx'),
        ),
    ]
