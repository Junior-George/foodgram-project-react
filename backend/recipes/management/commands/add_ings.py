import csv

from django.conf import settings
from django.core.management import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загрузка из csv файла'

    def handle(self, *args, **kwargs):
        with open(
            'data/ingredients.csv',
            'r',
            encoding='UTF-8'
        ) as file:
            for row in csv.reader(file):
                Ingredient.objects.get_or_create(
                    name=row[0], measurement_unit=row[1])
        self.stdout.write(self.style.SUCCESS('Все ингридиенты загружены!'))
