# Generated by Django 4.1.1 on 2023-04-13 15:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('competition', '0020_alter_competitor_certificate_alter_game_pdf_results_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitor',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='competitor_set', to=settings.AUTH_USER_MODEL),
        ),
    ]
