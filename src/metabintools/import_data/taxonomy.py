import csv
from pathlib import Path

import click
from loguru import logger

from metabintools.bin_utils import get_basename
from metabintools.dataclasses.bin import Bin
from metabintools.dataclasses.bin_taxonomy import BinTaxonomy


class TaxonomyReader:
    @staticmethod
    def _read_taxonomy_file(
        file: Path,
        bin_name_column: str,
        classification_column: str,
        taxonomy_source: str,
    ) -> dict[str, BinTaxonomy]:
        out_taxonomy = {}
        with open(file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for result in reader:
                bin_name = get_basename(result[bin_name_column])
                out_taxonomy[bin_name] = BinTaxonomy(
                    tax_source=taxonomy_source,
                    tax_classification=result[classification_column],
                )
        return out_taxonomy

    def add_taxonomy(
        self, bins: list[Bin], taxonomy_file: Path, taxonomy_source: str | None
    ) -> list[Bin]:
        """
        Annotate bins with taxonomy information from a taxonomy file.
        """

        if taxonomy_source == "gtdbtk":
            taxonomy = self._read_taxonomy_file(
                taxonomy_file, "user_genome", "classification", "gtdbtk"
            )
        elif taxonomy_source == "gtdbtk_ncbi":
            taxonomy = self._read_taxonomy_file(
                taxonomy_file, "Genome ID", "Majority vote NCBI classification", "ncbi"
            )
        elif taxonomy_source == "manual":
            taxonomy = self._read_taxonomy_file(
                taxonomy_file, "File", "Classification", "manual"
            )
        else:
            logger.error(f"Unknown taxonomy source: {taxonomy_source}")
            raise click.ClickException(f"Unknown taxonomy source: {taxonomy_source}")

        out_bins = []
        for bin in bins:
            out_bin = bin.model_copy()
            out_bin.taxonomy = taxonomy.get(bin.id, None)
            out_bins.append(out_bin)

        return out_bins
