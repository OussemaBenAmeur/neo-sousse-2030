"""Orchestrates all seeders. Run: python database/seed/seed_all.py [--force]"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.connection import execute_query
from database.seed.seed_capteurs import seed_capteurs
from database.seed.seed_citoyens import seed_citoyens
from database.seed.seed_interventions import seed_interventions
from database.seed.seed_mesures import seed_mesures
from database.seed.seed_vehicules import seed_vehicules


_SEED_STEPS = [
    ("zones / techniciens / capteurs", ("zones", "techniciens", "capteurs"), seed_capteurs),
    ("citoyens", ("citoyens",), seed_citoyens),
    ("vehicules / trajets", ("vehicules", "trajets"), seed_vehicules),
    ("interventions", ("interventions",), seed_interventions),
    ("mesures", ("mesures",), seed_mesures),
]


def _table_has_rows(table: str) -> bool:
    rows = execute_query(f"SELECT COUNT(*) AS n FROM {table}")
    return bool(rows and rows[0].get("n", 0) > 0)


def seed_all(force: bool = False):
    print("Seeding Neo-Sousse 2030 database...")
    for label, tables, seeder in _SEED_STEPS:
        already_seeded = all(_table_has_rows(table) for table in tables)
        if already_seeded and not force:
            print(f"  → {label} already seeded, skipping")
            continue
        seeder()
    print("All data seeded successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Neo-Sousse 2030 database.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass row-count checks and run every seeder.",
    )
    args = parser.parse_args()
    seed_all(force=args.force)
