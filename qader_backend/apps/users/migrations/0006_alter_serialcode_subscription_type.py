# Generated by Django 5.2 on 2025-04-28 14:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_userprofile_admin_permissions'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serialcode',
            name='subscription_type',
            field=models.CharField(blank=True, choices=[('1_month', '1 Month'), ('3_months', '3 Months'), ('12_months', '12 Months'), ('custom', 'Custom Duration')], db_index=True, help_text='Categorizes the intended duration or type of the code.', max_length=20, null=True, verbose_name='Subscription Type'),
        ),
    ]
