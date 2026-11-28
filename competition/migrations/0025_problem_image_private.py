import posixpath

from django.db import migrations, models

OLD_DIR = 'public'
NEW_DIR = 'problems'


def move_images(apps, schema_editor, src, dst):
    """Presunie existujúce obrázky úloh medzi priečinkami v MEDIA_ROOT."""
    Problem = apps.get_model('competition', 'Problem')
    for problem in Problem.objects.exclude(image='').exclude(image__isnull=True):
        name = problem.image.name
        if posixpath.dirname(name) != src:
            continue
        storage = problem.image.storage
        if not storage.exists(name):
            continue
        with storage.open(name, 'rb') as file:
            new_name = storage.save(
                posixpath.join(dst, posixpath.basename(name)), file)
        problem.image.name = new_name
        problem.save(update_fields=['image'])
        storage.delete(name)


def forwards(apps, schema_editor):
    move_images(apps, schema_editor, OLD_DIR, NEW_DIR)


def backwards(apps, schema_editor):
    move_images(apps, schema_editor, NEW_DIR, OLD_DIR)


class Migration(migrations.Migration):

    dependencies = [
        ('competition', '0024_alter_utminfo_options_alter_level_game_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='problem',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='problems', verbose_name='Obrázok'),
        ),
        migrations.RunPython(forwards, backwards),
    ]
