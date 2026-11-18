"""Tests for MiMAG level assignment in BinStatistics."""

import pytest

from metabintools.dataclasses.bin_statistics import BinStatistics
from metabintools.enums import MiMAG


def make_stats(**overrides) -> BinStatistics:
    values = dict(
        n_contigs=10,
        n_circular=0,
        completeness=0.95,
        contamination=0.02,
        n_unique_trnas=20,
        has_5s=True,
        has_16s=True,
        has_23s=True,
    )
    values.update(overrides)
    return BinStatistics(**values)


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({}, MiMAG.HIGH),
        ({"contamination": 0.05}, MiMAG.HIGH),
        ({"contamination": 0.06}, MiMAG.MEDIUM),
        ({"contamination": 0.10}, MiMAG.MEDIUM),
        ({"contamination": 0.11}, MiMAG.LOW),
        ({"completeness": 0.6, "n_circular": 10}, MiMAG.HIGH),
        ({"completeness": 0.6, "n_circular": 0}, MiMAG.MEDIUM),
        ({"n_unique_trnas": 17}, MiMAG.MEDIUM),
        ({"has_5s": False}, MiMAG.MEDIUM),
    ],
)
def test_update_mimag_levels(overrides, expected):
    stats = make_stats(**overrides)
    stats.update_mimag()
    assert stats.mimag == expected


def test_update_mimag_missing_data_clears_level():
    stats = make_stats(has_5s=None, mimag=MiMAG.HIGH)
    stats.update_mimag()
    assert stats.mimag is None
