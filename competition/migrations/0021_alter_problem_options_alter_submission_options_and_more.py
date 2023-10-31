# Generated by Django 4.1.1 on 2023-04-27 20:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0020_alter_competitor_certificate_alter_game_pdf_results_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='problem',
            options={'ordering': ['level', 'order'], 'verbose_name': 'Úloha', 'verbose_name_plural': 'Úlohy'},
        ),
        migrations.AlterModelOptions(
            name='submission',
            options={'get_latest_by': 'submitted_at', 'ordering': ['submitted_at'], 'verbose_name': 'Odpoveď na úlohu', 'verbose_name_plural': 'Odpovede na úlohy'},
        ),
        migrations.AddField(
            model_name='problem',
            name='order',
            field=models.PositiveSmallIntegerField(null=True, verbose_name='Poradie úlohy v leveli'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Obrázok'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='competition.level', verbose_name='Level'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='solution',
            field=models.CharField(max_length=25, verbose_name='Správna odpoveď'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='text',
            field=models.TextField(verbose_name='Zadanie'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='competitor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competition.competitor', verbose_name='Súťažiaci'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='competitor_answer',
            field=models.CharField(max_length=25, verbose_name='Odovzdaná odpoveď'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='correct',
            field=models.BooleanField(verbose_name='Správne'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='problem',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competition.problem', verbose_name='Úloha'),
        ),
        migrations.AlterField(
            model_name='submission',
            name='submitted_at',
            field=models.DateTimeField(verbose_name='Odovzdané o'),
        ),
    ]