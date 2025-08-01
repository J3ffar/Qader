# Generated by Django 5.2 on 2025-07-04 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_page_content_structured_alter_faqitem_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactmessage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='contactmessage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='contentimage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='contentimage',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='faqcategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='faqcategory',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='faqitem',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='faqitem',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='homepagefeaturecard',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='homepagefeaturecard',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='homepagestatistic',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='homepagestatistic',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='page',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='page',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
        migrations.AlterField(
            model_name='partnercategory',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='Created At'),
        ),
        migrations.AlterField(
            model_name='partnercategory',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='Updated At'),
        ),
    ]
