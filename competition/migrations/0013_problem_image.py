# Generated by Django 4.1.1 on 2022-11-07 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0012_alter_competitorgroup_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='problem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]
