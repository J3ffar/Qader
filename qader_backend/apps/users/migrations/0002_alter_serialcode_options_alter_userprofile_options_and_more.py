# Generated by Django 5.2 on 2025-04-14 18:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='serialcode',
            options={'ordering': ['-created_at'], 'verbose_name': 'Serial Code', 'verbose_name_plural': 'Serial Codes'},
        ),
        migrations.AlterModelOptions(
            name='userprofile',
            options={'verbose_name': 'User Profile', 'verbose_name_plural': 'User Profiles'},
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='code',
            field=models.CharField(db_index=True, help_text='The unique serial code string.', max_length=50, unique=True, verbose_name='Code'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='created_by',
            field=models.ForeignKey(blank=True, help_text='Admin or Sub-Admin who generated the code.', limit_choices_to={'is_staff': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='generated_codes', to=settings.AUTH_USER_MODEL, verbose_name='Created By'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='duration_days',
            field=models.PositiveIntegerField(default=30, help_text='Subscription length in days granted by this code.', verbose_name='Duration (Days)'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Indicates if the code can currently be used.', verbose_name='Is Active?'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='is_used',
            field=models.BooleanField(db_index=True, default=False, help_text='Indicates if the code has already been redeemed.', verbose_name='Is Used?'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='notes',
            field=models.TextField(blank=True, help_text='Administrative notes about this code (e.g., batch identifier, purpose).', null=True, verbose_name='Notes'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='used_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp when the code was redeemed.', null=True, verbose_name='Used At'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='used_by',
            field=models.ForeignKey(blank=True, help_text='The user who redeemed this code.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='redeemed_codes', to=settings.AUTH_USER_MODEL, verbose_name='Used By'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='current_level_quantitative',
            field=models.FloatField(blank=True, help_text='Assessed proficiency level in the Quantitative section (e.g., percentage).', null=True, verbose_name='Current Quantitative Level'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='current_level_verbal',
            field=models.FloatField(blank=True, help_text='Assessed proficiency level in the Verbal section (e.g., percentage).', null=True, verbose_name='Current Verbal Level'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='current_streak_days',
            field=models.PositiveIntegerField(default=0, verbose_name='Current Study Streak'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='dark_mode_auto_enabled',
            field=models.BooleanField(default=False, verbose_name='Auto Dark Mode Enabled?'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='dark_mode_auto_time_end',
            field=models.TimeField(blank=True, null=True, verbose_name='Auto Dark Mode End Time'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='dark_mode_auto_time_start',
            field=models.TimeField(blank=True, null=True, verbose_name='Auto Dark Mode Start Time'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='dark_mode_preference',
            field=models.CharField(choices=[('light', 'Light'), ('dark', 'Dark'), ('system', 'System')], default='light', max_length=10, verbose_name='Dark Mode Preference'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='full_name',
            field=models.CharField(max_length=255, verbose_name='Full Name'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='gender',
            field=models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female')], max_length=20, null=True, verbose_name='Gender'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='grade',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Grade'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='has_taken_qiyas_before',
            field=models.BooleanField(blank=True, help_text='Has the student taken an official Qiyas test previously?', null=True, verbose_name='Taken Qiyas Before?'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_study_activity_at',
            field=models.DateTimeField(blank=True, help_text='Timestamp of the last tracked study action (e.g., question answered).', null=True, verbose_name='Last Study Activity At'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='last_visited_study_option',
            field=models.CharField(blank=True, help_text="Slug or identifier of the last viewed section in the 'Study Page'.", max_length=100, null=True, verbose_name='Last Visited Study Option'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='longest_streak_days',
            field=models.PositiveIntegerField(default=0, verbose_name='Longest Study Streak'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='notify_reminders_enabled',
            field=models.BooleanField(default=True, verbose_name='Reminders Enabled?'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='points',
            field=models.PositiveIntegerField(default=0, verbose_name='Points'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='preferred_name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Preferred Name'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='profiles/', verbose_name='Profile Picture'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='referral_code',
            field=models.CharField(blank=True, db_index=True, help_text="User's unique code to share for referrals.", max_length=20, null=True, unique=True, verbose_name='Referral Code'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='referred_by',
            field=models.ForeignKey(blank=True, help_text='The user who referred this user.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='referrals_made', to=settings.AUTH_USER_MODEL, verbose_name='Referred By'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('admin', 'Admin'), ('sub_admin', 'Sub-Admin')], db_index=True, default='student', max_length=20, verbose_name='Role'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='serial_code_used',
            field=models.ForeignKey(blank=True, help_text='The last serial code used to activate/extend subscription.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_profiles', to='users.serialcode', verbose_name='Serial Code Used'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='study_reminder_time',
            field=models.TimeField(blank=True, help_text='Preferred time of day for study reminders.', null=True, verbose_name='Study Reminder Time'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='subscription_expires_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name='Subscription Expires At'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='upcoming_test_date',
            field=models.DateField(blank=True, help_text='User-set date for their upcoming official test.', null=True, verbose_name='Upcoming Test Date'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='profile', serialize=False, to=settings.AUTH_USER_MODEL, verbose_name='User'),
        ),
    ]
