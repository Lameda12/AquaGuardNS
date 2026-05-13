from sites import SITES, SPECIES_THRESHOLDS


def test_all_four_sites_present():
    assert set(SITES.keys()) == {"mahone_bay", "bedford_basin", "chedabucto_bay", "bras_dor"}


def test_site_has_required_fields():
    for site_id, info in SITES.items():
        assert "lat" in info, f"{site_id} missing lat"
        assert "lon" in info, f"{site_id} missing lon"
        assert "name" in info, f"{site_id} missing name"
        assert "species" in info, f"{site_id} missing species"


def test_species_thresholds_present():
    assert set(SPECIES_THRESHOLDS.keys()) == {"Atlantic Salmon", "Blue Mussel", "Eastern Oyster"}


def test_species_threshold_fields():
    for sp, thresholds in SPECIES_THRESHOLDS.items():
        assert "stress" in thresholds, f"{sp} missing stress"
        assert "critical" in thresholds, f"{sp} missing critical"
        assert "lethal" in thresholds, f"{sp} missing lethal"
        assert thresholds["stress"] < thresholds["critical"] < thresholds["lethal"]
