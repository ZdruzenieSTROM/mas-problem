# Generated by Django 4.1.1 on 2022-11-07 11:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("competition", "0011_remove_competitor_current_level"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="competitorgroup",
            options={
                "verbose_name": "Skupina ročníkov pre hru",
                "verbose_name_plural": "Skupiny ročníkov pre hru",
            },
        ),
        migrations.AlterModelOptions(
            name="competitorgrouplevelsettings",
            options={
                "verbose_name": "postupové podmienky",
                "verbose_name_plural": "postupové podmienky",
            },
        ),
        migrations.AlterModelOptions(
            name="resultgroup",
            options={
                "verbose_name": "výsledková skupina",
                "verbose_name_plural": "výsledkové skupiny",
            },
        ),
        migrations.AddField(
            model_name="problem",
            name="image_filename",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="competitor",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="competitor",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="competitorgrouplevelsettings",
            name="num_to_unlock",
            field=models.PositiveSmallIntegerField(
                verbose_name="Počet úloh z predhádzajúceho levelu na odomknutie"
            ),
        ),
        migrations.AlterField(
            model_name="resultgroup",
            name="name",
            field=models.CharField(
                max_length=128, verbose_name="Názov skupiny (vo výsledkovke)"
            ),
        ),
    ]
