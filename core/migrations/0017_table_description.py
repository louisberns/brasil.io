# Generated by Django 3.0.5 on 2020-04-02 19:21

from django.db import migrations
import markdownx.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_auto_20190217_0102'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='description',
            field=markdownx.models.MarkdownxField(blank=True, null=True),
        ),
    ]
