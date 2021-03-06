# Generated by Django 3.0.6 on 2020-06-01 14:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("brutaldon", "0024_auto_20200601_0945"),
    ]

    operations = [
        migrations.AddField(
            model_name="preference",
            name="preview_sensitive",
            field=models.BooleanField(
                default=False, help_text='Show preview for media marked as "sensitive"'
            ),
        ),
    ]
