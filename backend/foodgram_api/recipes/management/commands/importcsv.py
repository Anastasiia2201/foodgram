from django.core import management
from django.core.management.base import BaseCommand
from django.db import models
from django.contrib.auth import get_user_model

from recipes.models import Ingredient

CSV_DIR = '../../data/'
FILE_NAME = 'ingredients.csv'

User = get_user_model()

def import_model(file_path: str, model: models.Model):
    """Импорт данных из cvs файла в модель."""
    with open(file_path, 'r', encoding='utf-8') as file:
        id = 1
        for row in file:
            if '"' not in row:
                measurement_unit = row.split(',')[1][:-2]
                name = row.split(',')[0]
                model.objects.get_or_create(id=id, measurement_unit=measurement_unit, name=name)
            else:
                measurement_unit = row.split('",')[1][:-2]
                name = row.split('",')[0].replace('"', '')
                model.objects.get_or_create(id=id, measurement_unit=measurement_unit, name=name)
            id += 1


class Command(BaseCommand):
    help = 'import CSV Data into model Ingredient'

    management.call_command('migrate')

    def handle(self, *args, **options):
        import_model(CSV_DIR + FILE_NAME, Ingredient)
        self.stdout.write(self.style.SUCCESS('Данные добавлены'))
