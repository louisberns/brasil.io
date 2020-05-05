# Generated by Django 2.2 on 2020-04-14 16:09

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("covid19", "0004_auto_20200410_1958"),
    ]

    operations = [
        migrations.AlterField(
            model_name="statespreadsheet",
            name="boletim_urls",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.TextField(), help_text="Lista de URLs do(s) boletim(s)", size=None
            ),
        ),
    ]