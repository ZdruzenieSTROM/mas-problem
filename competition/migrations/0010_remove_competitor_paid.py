# Generated by Django 4.1.1 on 2022-10-17 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0009_payment_paid_payment_payment_reference_number_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='competitor',
            name='paid',
        ),
    ]
