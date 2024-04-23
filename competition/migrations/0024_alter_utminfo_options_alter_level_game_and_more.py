# Generated by Django 4.1.1 on 2024-04-23 16:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0023_utminfo_alter_game_options_alter_problem_order'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='utminfo',
            options={'verbose_name': 'UTM info', 'verbose_name_plural': 'UTM info'},
        ),
        migrations.AlterField(
            model_name='level',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='levels', to='competition.game'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='public', verbose_name='Obrázok'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='competitor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='competition.competitor', verbose_name='Súťažiaci'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submissions', to='competition.problem', verbose_name='Úloha'),
        ),
        migrations.AlterField(
            model_name='utminfo',
            name='campaign',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='utminfo',
            name='content',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='utminfo',
            name='medium',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='utminfo',
            name='source',
            field=models.CharField(blank=True, max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='utminfo',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
