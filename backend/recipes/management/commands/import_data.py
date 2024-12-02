import json
from contextlib import suppress

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError
from recipes.models import Ingredient, Tag


def load_data_to_model(filename, model):
    """Загрузка данных из JSON файла в указанную модель."""
    with open(filename, "r") as file:
        data = json.load(file)
        instances = (model(**item) for item in data)
        with suppress(IntegrityError):
            model.objects.bulk_create(instances)


class Command(BaseCommand):

    def handle(self, *args, **options):
        files_to_models = {
            "data/ingredients.json": Ingredient,
            "data/tags.json": Tag,
        }

        for filename, model in files_to_models.items():
            load_data_to_model(filename, model)
