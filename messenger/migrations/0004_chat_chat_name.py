# Generated by Django 4.2.21 on 2025-06-13 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messenger', '0003_alter_chat_options_alter_message_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='chat',
            name='chat_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Название чата'),
        ),
    ]
