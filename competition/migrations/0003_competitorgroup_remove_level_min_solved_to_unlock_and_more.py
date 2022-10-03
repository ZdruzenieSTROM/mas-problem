# Generated by Django 4.1.1 on 2022-09-18 09:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0002_competitor_first_name_competitor_second_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompetitorGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Skupina ročníkov pre hru',
            },
        ),
        migrations.RemoveField(
            model_name='level',
            name='min_solved_to_unlock',
        ),
        migrations.AddField(
            model_name='competitor',
            name='started_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='game',
            name='name',
            field=models.CharField(default='', max_length=128),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='level',
            name='previous_level',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='levels', to='competition.level'),
        ),
        migrations.AlterField(
            model_name='problem',
            name='level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='problems', to='competition.level'),
        ),
        migrations.CreateModel(
            name='ResultGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competition.game')),
                ('grades', models.ManyToManyField(to='competition.grade')),
            ],
            options={
                'verbose_name': 'výsledkové skupiny',
            },
        ),
        migrations.CreateModel(
            name='CompetitorGroupLevelSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('num_to_unlock', models.PositiveSmallIntegerField()),
                ('competitor_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setting_groups', to='competition.competitorgroup')),
                ('level', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='setting_groups', to='competition.level')),
            ],
            options={
                'verbose_name': 'postupové podmienky',
            },
        ),
        migrations.AddField(
            model_name='competitorgroup',
            name='end_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups_ending', to='competition.level'),
        ),
        migrations.AddField(
            model_name='competitorgroup',
            name='game',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='competition.game'),
        ),
        migrations.AddField(
            model_name='competitorgroup',
            name='grades',
            field=models.ManyToManyField(to='competition.grade'),
        ),
        migrations.AddField(
            model_name='competitorgroup',
            name='start_level',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='groups_starting', to='competition.level'),
        ),
    ]