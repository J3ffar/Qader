# Generated by Django 5.2 on 2025-05-14 12:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_alter_userprofile_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='assigned_mentor',
            field=models.ForeignKey(blank=True, help_text='The Teacher or Trainer assigned to this student. Only applicable if role is Student.', limit_choices_to={'role__in': ['teacher', 'trainer']}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mentees', to='users.userprofile', verbose_name='Assigned Mentor (Teacher/Trainer)'),
        ),
    ]
