# Generated by Django 4.1.1 on 2022-11-12 23:11

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0015_competitor_certificate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='competitor',
            name='certificate',
            field=models.FileField(blank=True, null=True, upload_to=pathlib.PureWindowsPath('C:/Users/petko/Documents/GitHub/webstrom/mas-problem/diplomy')),
        ),
    ]
