# Generated by Django 5.2 on 2025-04-14 18:46

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LearningSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly identifier (leave blank to auto-generate)', max_length=120, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order in UI', verbose_name='Order')),
            ],
            options={
                'verbose_name': 'Learning Section',
                'verbose_name_plural': 'Learning Sections',
                'ordering': ['order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='LearningSubSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=150, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly identifier (leave blank to auto-generate)', max_length=170, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('order', models.PositiveIntegerField(default=0, help_text='Display order in UI', verbose_name='Order')),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subsections', to='learning.learningsection', verbose_name='Section')),
            ],
            options={
                'verbose_name': 'Learning Sub-Section',
                'verbose_name_plural': 'Learning Sub-Sections',
                'ordering': ['section__order', 'order', 'name'],
                'unique_together': {('section', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Skill',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=200, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, help_text='URL-friendly identifier (leave blank to auto-generate)', max_length=220, unique=True, verbose_name='Slug')),
                ('description', models.TextField(blank=True, null=True, verbose_name='Description')),
                ('subsection', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='skills', to='learning.learningsubsection', verbose_name='Sub-Section')),
            ],
            options={
                'verbose_name': 'Skill',
                'verbose_name_plural': 'Skills',
                'ordering': ['subsection__section__order', 'subsection__order', 'name'],
                'unique_together': {('subsection', 'name')},
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('question_text', models.TextField(verbose_name='Question Text')),
                ('option_a', models.TextField(verbose_name='Option A')),
                ('option_b', models.TextField(verbose_name='Option B')),
                ('option_c', models.TextField(verbose_name='Option C')),
                ('option_d', models.TextField(verbose_name='Option D')),
                ('correct_answer', models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')], max_length=1, verbose_name='Correct Answer')),
                ('explanation', models.TextField(blank=True, null=True, verbose_name='Explanation')),
                ('hint', models.TextField(blank=True, null=True, verbose_name='Hint')),
                ('solution_method_summary', models.TextField(blank=True, null=True, verbose_name='Solution Method Summary')),
                ('difficulty', models.IntegerField(choices=[(1, 'Very Easy'), (2, 'Easy'), (3, 'Medium'), (4, 'Hard'), (5, 'Very Hard')], default=3, verbose_name='Difficulty')),
                ('is_active', models.BooleanField(db_index=True, default=True, help_text='Whether the question should be used in the platform', verbose_name='Is Active')),
                ('subsection', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='questions', to='learning.learningsubsection', verbose_name='Sub-Section')),
                ('skill', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='questions', to='learning.skill', verbose_name='Primary Skill')),
            ],
            options={
                'verbose_name': 'Question',
                'verbose_name_plural': 'Questions',
                'ordering': ['subsection', 'skill', 'id'],
            },
        ),
        migrations.CreateModel(
            name='UserStarredQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('starred_at', models.DateTimeField(auto_now_add=True, verbose_name='Starred At')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='starrers_link', to='learning.question')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='starred_questions_link', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Starred Question',
                'verbose_name_plural': 'User Starred Questions',
                'ordering': ['-starred_at'],
                'unique_together': {('user', 'question')},
            },
        ),
        migrations.AddField(
            model_name='question',
            name='starred_by',
            field=models.ManyToManyField(blank=True, related_name='starred_questions', through='learning.UserStarredQuestion', to=settings.AUTH_USER_MODEL, verbose_name='Starred By Users'),
        ),
    ]
