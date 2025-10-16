"""
Management command to load initial categories and product types for Pokémon TCG.
Place this file in: apps/products/management/commands/load_initial_data.py
"""
from django.core.management.base import BaseCommand
from apps.products.models import Category, ProductType

class Command(BaseCommand):
    help = 'Load initial categories and product types for Pokémon TCG'

    def handle(self, *args, **options):
        self.stdout.write('Loading product types...')
        product_types = [
            'single_card', 'booster_pack', 'elite_trainer_box',
            'booster_box', 'collection_box', 'blister',
            'theme_deck', 'tin', 'sleeve', 'deck_box',
            'binder', 'playmat', 'toploader', 'other_accessory',
        ]
        for pt in product_types:
            obj, created = ProductType.objects.get_or_create(name=pt)
            status = 'Created' if created else 'Exists'
            self.stdout.write(f'  {status} product type: {pt}')

        self.stdout.write('\nLoading main categories...')
        categories_data = [
            {
                'slug': 'single-cards',
                'order': 1,
                'translations': {
                    'en': {'name': 'Single Cards', 'description': 'Individual Pokémon TCG cards'},
                    'es': {'name': 'Cartas Sueltas', 'description': 'Cartas individuales de Pokémon TCG'},
                }
            },
            {
                'slug': 'sealed-products',
                'order': 2,
                'translations': {
                    'en': {'name': 'Sealed Products', 'description': 'Booster packs and sealed boxes'},
                    'es': {'name': 'Productos Sellados', 'description': 'Sobres y cajas selladas'},
                }
            },
            {
                'slug': 'accessories',
                'order': 3,
                'translations': {
                    'en': {'name': 'Accessories', 'description': 'Sleeves, binders, toploaders, etc.'},
                    'es': {'name': 'Accesorios', 'description': 'Fundas, álbumes, protectores, etc.'},
                }
            },
        ]
        for cat in categories_data:
            obj, created = Category.objects.get_or_create(slug=cat['slug'], defaults={'order': cat['order']})
            for lang, data in cat['translations'].items():
                obj.set_current_language(lang)
                obj.name = data['name']
                obj.description = data['description']
                obj.save()
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status} category: {cat["translations"]["en"]["name"]}')

        self.stdout.write('\nCreating subcategories under Sealed Products...')
        parent = Category.objects.get(slug='sealed-products')
        subcategories = [
            {'slug': 'booster-packs', 'order': 1, 'en': 'Booster Packs', 'es': 'Sobres'},
            {'slug': 'booster-boxes', 'order': 2, 'en': 'Booster Boxes', 'es': 'Cajas de Sobres'},
            {'slug': 'elite-trainer-boxes', 'order': 3, 'en': 'Elite Trainer Boxes', 'es': 'Cajas Entrenador Elite'},
            {'slug': 'collection-boxes', 'order': 4, 'en': 'Collection Boxes', 'es': 'Cajas de Colección'},
        ]
        for sub in subcategories:
            obj, created = Category.objects.get_or_create(
                slug=sub['slug'], defaults={'parent': parent, 'order': sub['order']}
            )
            obj.set_current_language('en')
            obj.name = sub['en']
            obj.save()
            obj.set_current_language('es')
            obj.name = sub['es']
            obj.save()
            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status} subcategory: {sub["en"]}')

        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully!'))