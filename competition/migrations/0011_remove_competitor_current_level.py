# Generated by Django 4.1.1 on 2022-10-24 21:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0010_remove_competitor_paid'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competitor',
            name='current_level',
        ),
    ]