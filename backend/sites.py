"""Site configuration and species risk thresholds for NS aquaculture."""

SITES: dict[str, dict] = {
    "mahone_bay":     {"lat": 44.50, "lon": -64.30, "name": "Mahone Bay",     "species": "Atlantic Salmon"},
    "bedford_basin":  {"lat": 44.72, "lon": -63.63, "name": "Bedford Basin",  "species": "Blue Mussel"},
    "chedabucto_bay": {"lat": 45.40, "lon": -61.10, "name": "Chedabucto Bay", "species": "Eastern Oyster"},
    "bras_dor":       {"lat": 45.83, "lon": -60.90, "name": "Bras d'Or Lake", "species": "Blue Mussel"},
}

SPECIES_THRESHOLDS: dict[str, dict[str, float]] = {
    "Atlantic Salmon": {"stress": 16.0, "critical": 18.0, "lethal": 23.0},
    "Blue Mussel":     {"stress": 20.0, "critical": 24.0, "lethal": 27.0},
    "Eastern Oyster":  {"stress": 28.0, "critical": 32.0, "lethal": 35.0},
}
