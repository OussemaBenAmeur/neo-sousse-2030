"""Seeds zones, techniciens, and capteurs tables."""

from database.connection import execute_query

ZONES = [
    ("Médina",             "Centre historique de Sousse",                  35.8264, 10.6378, 2.3),
    ("Zone Industrielle",  "Zone industrielle Sousse Sud",                 35.7850, 10.6550, 8.5),
    ("Corniche",           "Front de mer et plage Boujaafar",              35.8150, 10.6050, 3.1),
    ("Aéroport / Enfidha", "Zone aéroportuaire, Sousse Sud",               35.7800, 10.6800, 12.0),
    ("Cité Sportive",      "Stade olympique et quartier résidentiel",      35.8290, 10.6550, 4.2),
    ("Port",               "Port de Sousse et zone commerciale",           35.8207, 10.6290, 5.8),
    ("Zone Nord",          "Quartier nord vers Hammam Sousse",             35.8650, 10.5980, 6.1),
    ("Zone Sud",           "Quartier sud vers Akouda",                     35.7980, 10.6400, 7.3),
]

TECHNICIENS = [
    ("Ben Ali",   "Mohamed",  "électronique"),
    ("Trabelsi",  "Fatma",    "mécanique"),
    ("Mansour",   "Karim",    "informatique"),
    ("Chaabane",  "Nour",     "électronique"),
    ("Bouzid",    "Yassine",  "mécanique"),
]

CAPTEUR_TYPES = ["qualite_air", "temperature", "trafic", "bruit", "humidite"]
FABRICANTS = ["SensorTech", "AirMetrics", "UrbanSense", "SmartCity"]
STATUTS = ["ACTIF", "ACTIF", "ACTIF", "ACTIF", "SIGNALÉ", "EN_MAINTENANCE", "HORS_SERVICE"]


def seed_capteurs():
    print("  → Seeding zones, techniciens, capteurs...")
    # Insert zones
    for nom, desc, lat, lon, sup in ZONES:
        execute_query(
            """INSERT INTO zones (nom, description, geom_lat, geom_lon, superficie)
               VALUES (:nom, :desc, :lat, :lon, :sup)
               ON CONFLICT (nom) DO NOTHING""",
            {"nom": nom, "desc": desc, "lat": lat, "lon": lon, "sup": sup},
        )

    # Insert techniciens
    for nom, prenom, spec in TECHNICIENS:
        execute_query(
            """INSERT INTO techniciens (nom, prenom, specialite)
               VALUES (:nom, :prenom, :spec)
               ON CONFLICT DO NOTHING""",
            {"nom": nom, "prenom": prenom, "spec": spec},
        )

    # Get zone IDs
    zones = execute_query("SELECT id FROM zones ORDER BY id")
    zone_ids = [z["id"] for z in zones]

    import random
    random.seed(42)
    from datetime import datetime, timedelta

    for i in range(1, 51):
        ctype = CAPTEUR_TYPES[i % len(CAPTEUR_TYPES)]
        zone_id = zone_ids[i % len(zone_ids)]
        statut = STATUTS[i % len(STATUTS)]
        fab = FABRICANTS[i % len(FABRICANTS)]
        install_date = datetime.now() - timedelta(days=random.randint(30, 730))

        execute_query(
            """INSERT INTO capteurs (nom, type, zone_id, statut, date_installation,
               fabricant, modele, latitude, longitude)
               VALUES (:nom, :type, :zone_id, :statut, :install_date,
                       :fab, :mod, :lat, :lon)
               ON CONFLICT DO NOTHING""",
            {
                "nom": f"Capteur-{ctype[:3].upper()}-{i:03d}",
                "type": ctype,
                "zone_id": zone_id,
                "statut": statut,
                "install_date": install_date,
                "fab": fab,
                "mod": f"Model-{random.choice(['X1','X2','Pro','Elite'])}",
                "lat": 35.8282 + random.uniform(-0.05, 0.05),
                "lon": 10.6358 + random.uniform(-0.05, 0.05),
            },
        )

    # Seed FSM states for capteurs
    capteurs = execute_query("SELECT id, statut FROM capteurs")
    for c in capteurs:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('capteur', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": c["id"], "state": c["statut"]},
        )

    print(f"     - {len(zones)} zones, {len(TECHNICIENS)} techniciens, 50 capteurs")
