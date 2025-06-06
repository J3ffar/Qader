# Generated by Django 5.2 on 2025-04-19 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_serialcode_options_alter_userprofile_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='serialcode',
            name='subscription_type',
            field=models.CharField(blank=True, choices=[('1_month', '1 Month'), ('6_months', '6 Months'), ('12_months', '12 Months'), ('custom', 'Custom')], db_index=True, help_text='Categorizes the intended duration of the code (e.g., 1 Month, 6 Months).', max_length=20, null=True, verbose_name='Subscription Type'),
        ),
        migrations.AlterField(
            model_name='serialcode',
            name='duration_days',
            field=models.PositiveIntegerField(default=30, help_text='Subscription length in days granted by this code. Should align with Subscription Type if set.', verbose_name='Duration (Days)'),
        ),
    ]
