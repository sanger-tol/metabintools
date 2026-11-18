"""Tests for ENA submittable taxon lookup and its caching, with requests mocked."""

from collections import Counter

import pytest

from metabintools.ena_taxonomy import ena_taxonomy
from metabintools.ena_taxonomy.ena_taxonomy import EnaSubmittableTaxonomy


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def clear_caches():
    EnaSubmittableTaxonomy._query_cache.clear()
    EnaSubmittableTaxonomy._suggest_cache.clear()
    EnaSubmittableTaxonomy._lineage_cache.clear()
    yield
    EnaSubmittableTaxonomy._query_cache.clear()
    EnaSubmittableTaxonomy._suggest_cache.clear()
    EnaSubmittableTaxonomy._lineage_cache.clear()


@pytest.fixture
def fake_ena(monkeypatch):
    """Patch requests.get; returns a dict of request URLs and a route table."""
    requested = Counter()
    routes = {
        "suggest-for-submission/Bacteroides sp.": [
            {"taxId": 1, "scientificName": "Bacteroides sp."}
        ],
    }

    def fake_get(url):
        requested[url] += 1
        key = url.split("/rest/")[1]
        return FakeResponse(routes.get(key, []))

    monkeypatch.setattr(ena_taxonomy.requests, "get", fake_get)
    return {"requested": requested, "routes": routes}


def lineage(genus: str, species: str) -> str:
    return (
        "d__Bacteria;p__Bacteroidota;c__Bacteroidia;o__Bacteroidales;"
        f"f__Bacteroidaceae;g__{genus};s__{species}"
    )


def test_species_miss_falls_back_to_genus(fake_ena):
    result = EnaSubmittableTaxonomy().ena_suggest_lineage_taxid(
        lineage("Bacteroides", "Bacteroides fragilis")
    )

    assert result == {"taxId": 1, "scientificName": "Bacteroides sp."}


def test_higher_level_lookups_are_cached_across_lineages(fake_ena):
    requested = fake_ena["requested"]

    for genus in ["Genus1", "Genus2"]:
        with pytest.raises(ValueError):
            EnaSubmittableTaxonomy().ena_suggest_lineage_taxid(
                lineage(genus, f"{genus} sp1")
            )

    phylum_requests = {
        url: count for url, count in requested.items() if "Bacteroidota" in url
    }
    assert phylum_requests, "expected phylum-level requests to be made"
    assert all(count == 1 for count in phylum_requests.values())


def test_repeated_lineage_makes_no_new_requests(fake_ena):
    requested = fake_ena["requested"]
    taxonomy = EnaSubmittableTaxonomy()

    first = taxonomy.ena_suggest_lineage_taxid(
        lineage("Bacteroides", "Bacteroides fragilis")
    )
    calls_after_first = sum(requested.values())
    second = taxonomy.ena_suggest_lineage_taxid(
        lineage("Bacteroides", "Bacteroides fragilis")
    )

    assert second == first
    assert sum(requested.values()) == calls_after_first
