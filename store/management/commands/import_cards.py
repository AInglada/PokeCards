"""
Import command that creates Generation -> CardSet -> Card entries
from PokemonTCG.io, resilient to timeouts and mapping missing generation.
"""
import os
import time
import random
from datetime import datetime
from typing import Optional, Dict, Any

import requests
from requests.exceptions import RequestException, HTTPError

from django.core.management.base import BaseCommand, CommandError

from store.models import Generation, CardSet, Card, Language

API_BASE = "https://api.pokemontcg.io/v2"
API_KEY = os.environ.get("POKEMON_TCG_API_KEY")
HEADERS = {"X-Api-Key": API_KEY} if API_KEY else {}


def _http_get(url: str, params: Optional[dict] = None, max_retries: int = 3, timeout: float = 30.0) -> Dict[str, Any]:
    """
    GET with retries, backoff and jitter. Returns parsed JSON or raises.
    """
    attempt = 0
    while True:
        try:
            resp = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status in (429, 502, 503, 504) and attempt < max_retries:
                attempt += 1
                backoff = (2 ** attempt) + random.uniform(0, 1)
                print(f"HTTP {status} — retrying in {backoff:.1f}s (attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                continue
            raise
        except RequestException as e:
            if attempt < max_retries:
                attempt += 1
                backoff = (2 ** attempt) + random.uniform(0, 1)
                print(f"Request error: {e} — retrying in {backoff:.1f}s (attempt {attempt}/{max_retries})...")
                time.sleep(backoff)
                continue
            raise


class Command(BaseCommand):
    help = "Import card sets/cards from PokemonTCG.io (full). Ensure Generation exists."

    def add_arguments(self, parser):
        parser.add_argument("--from-api", action="store_true", help="Import from remote API")
        parser.add_argument("--set-id", type=str, help="(optional) import only a specific set by id (eg: swsh1)")
        parser.add_argument("--page-size", type=int, default=250, help="API page size")
        parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout seconds")
        parser.add_argument("--max-retries", type=int, default=3, help="Max retries per request")

    def handle(self, *args, **options):
        if not (options.get("from_api") or options.get("from-api")):
            raise CommandError("Use --from-api to import from the API")

        set_id = options.get("set_id")
        page_size = options.get("page_size") or 250
        timeout = options.get("timeout") or 30.0
        max_retries = options.get("max_retries") or 3

        # Ensure languages exist (catalog import doesn't create Inventory)
        for code, name in [("en", "English"), ("es", "Español"), ("jp", "Japanese")]:
            from store.models import Language  # local import to avoid startup ordering issues
            Language.objects.get_or_create(code=code, defaults={"name": name})

        self.stdout.write(self.style.NOTICE("Starting import from PokemonTCG.io"))
        try:
            self.import_from_api(set_id=set_id, page_size=page_size, timeout=timeout, max_retries=max_retries)
        except Exception as e:
            raise CommandError(f"Import failed: {e}")

    def import_from_api(self, set_id: Optional[str], page_size: int, timeout: float, max_retries: int):
        self.stdout.write("Fetching sets list...")

        sets_data = []
        if set_id:
            payload = _http_get(f"{API_BASE}/sets/{set_id}", max_retries=max_retries, timeout=timeout)
            sd = payload.get("data")
            if sd:
                sets_data = [sd]
            else:
                self.stdout.write(self.style.WARNING(f"No set found for id {set_id}"))
                return
        else:
            page = 1
            while True:
                params = {"page": page, "pageSize": page_size}
                payload = _http_get(f"{API_BASE}/sets", params=params, max_retries=max_retries, timeout=timeout)
                page_sets = payload.get("data", []) or []
                if not page_sets:
                    break
                sets_data.extend(page_sets)
                self.stdout.write(f"Fetched sets page {page} ({len(page_sets)})")
                if len(page_sets) < page_size:
                    break
                page += 1

        total_sets = len(sets_data)
        self.stdout.write(self.style.SUCCESS(f"Found {total_sets} set(s)"))

        for idx, s in enumerate(sets_data, start=1):
            set_name = s.get("name") or s.get("id")
            set_code = s.get("id")
            series_name = s.get("series") or "Unknown"

            self.stdout.write(self.style.NOTICE(f"[{idx}/{total_sets}] Processing set {set_name} ({set_code}) — series: {series_name}"))

            # Ensure Generation exists (use 'series' field to map)
            generation, _ = Generation.objects.get_or_create(name=series_name, defaults={"release_year": 0})

            # parse release date
            release_date = None
            rd = s.get("releaseDate")
            if rd:
                try:
                    release_date = datetime.strptime(rd, "%Y/%m/%d").date()
                except Exception:
                    try:
                        release_date = datetime.fromisoformat(rd).date()
                    except Exception:
                        release_date = None

            card_set, created = CardSet.objects.get_or_create(
                code=set_code,
                defaults={
                    "name": set_name,
                    "generation": generation,
                    "release_date": release_date,
                }
            )
            if not created:
                # ensure generation is set if previously created without it
                if card_set.generation is None:
                    card_set.generation = generation
                    card_set.save(update_fields=["generation"])

            # import cards for this set (paginated)
            page = 1
            set_imported = 0
            while True:
                params = {"q": f"set.id:{set_code}", "page": page, "pageSize": page_size}
                try:
                    data = _http_get(f"{API_BASE}/cards", params=params, max_retries=max_retries, timeout=timeout)
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed fetching cards page {page} for set {set_code}: {e}"))
                    break

                cards = data.get("data", []) or []
                if not cards:
                    break

                for c in cards:
                    api_global_id = c.get("id")
                    api_number = c.get("number", "")

                    defaults = {
                        "global_id": api_global_id,
                        "name": c.get("name", "") or "",
                        "supertype": c.get("supertype"),
                        "subtypes": ",".join(c.get("subtypes", [])) if c.get("subtypes") else None,
                        "hp": c.get("hp"),
                        "types": ",".join(c.get("types", [])) if c.get("types") else None,
                        "evolves_from": c.get("evolvesFrom"),
                        "rarity": c.get("rarity"),
                        "card_type": ",".join(c.get("types", [])) if c.get("types") else None,
                        "image_url_small": (c.get("images") or {}).get("small"),
                        "image_url_large": (c.get("images") or {}).get("large"),
                        "artist": c.get("artist"),
                        "flavor_text": c.get("flavorText"),
                        "national_pokedex_numbers": c.get("nationalPokedexNumbers") or [],
                        "attacks": c.get("attacks") or [],
                        "abilities": c.get("abilities") or [],
                        "weaknesses": c.get("weaknesses") or [],
                        "retreat_cost": c.get("retreatCost") or [],
                        "market_url_tcgplayer": (c.get("tcgplayer") or {}).get("url"),
                        "market_url_cardmarket": (c.get("cardmarket") or {}).get("url"),
                        "is_holo": ("Holo" in (c.get("rarity") or "")) or False,
                    }

                    card = None
                    if api_global_id:
                        card = Card.objects.filter(global_id=api_global_id).first()
                    if not card:
                        card = Card.objects.filter(set=card_set, set_number=api_number).first()

                    if card:
                        for k, v in defaults.items():
                            setattr(card, k, v)
                        card.save()
                        action = "updated"
                    else:
                        card = Card.objects.create(set=card_set, set_number=api_number, **defaults)
                        action = "created"

                    set_imported += 1
                    self.stdout.write(f"  - {action} card {card.name} ({card_set.code}#{card.set_number})")

                time.sleep(0.2)
                page += 1

            self.stdout.write(self.style.SUCCESS(f"Imported {set_imported} cards for set {card_set.name}"))

        self.stdout.write(self.style.SUCCESS("Import finished"))
