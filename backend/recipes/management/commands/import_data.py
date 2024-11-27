import json

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Ingredient, Tag


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            with open('data/ingredients.json', 'r') as file:
                data = json.load(file)
                instance = (Ingredient(**ingr) for ingr in data)
                Ingredient.objects.bulk_create(instance)
        except IntegrityError:
            pass
        try:
            with open('data/tags.json', 'r') as file_tag:
                data = json.load(file_tag)
                instance = (Tag(**d) for d in data)
                Tag.objects.bulk_create(instance)
        except IntegrityError:
            pass
