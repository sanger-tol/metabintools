from pathlib import Path
from typing import IO

import zstandard as zstd
from loguru import logger
from pydantic import BaseModel, Field, field_validator

from metabintools.dataclasses.bin import Bin
from metabintools.dataclasses.contig import Contig
from metabintools.enums import CoverageTool, QualityTool
from metabintools.import_data.annotation import ContigAnnotator
from metabintools.import_data.binset import parse_fasta_bins
from metabintools.import_data.coverage import CoverageReader
from metabintools.import_data.quality import QualityReader
from metabintools.import_data.taxonomy import TaxonomyReader
from metabintools.operations.rename import rename_bins as apply_rename_bins
from metabintools.query.query_parser import parse_filter_query


class BinSet(BaseModel):
    contigs: dict[str, Contig] = Field(..., description="Contigs in the assembly.")
    bins: list[Bin] | None = Field(None, description="Bins in the set.")

    @property
    def bin_contig_ids(self) -> set[str]:
        """Get the set of all contig IDs in the bins."""
        if self.bins is None:
            return set()
        return {contig_id for bin in self.bins for contig_id in bin.contigs}

    @property
    def assembly_contig_ids(self) -> set[str]:
        """Get the set of all contig IDs in the assembly."""
        return {contig for contig in self.contigs}

    @field_validator("bins")
    def validate_bin_contigs(cls, bins, info):
        """Validate that all bin contigs are present in the assembly."""
        if "contigs" not in info.data:
            return bins
        assembly_ids = {c for c in info.data["contigs"]}
        if bins:
            for bin in bins:
                missing = set(bin.contigs) - assembly_ids
                if missing:
                    raise ValueError(
                        f"Bin {bin.id} references missing contigs: {missing}"
                    )
        return bins

    @classmethod
    def read_binsfile(cls, file: IO) -> "BinSet":
        """
        Read a BinSet from a binary stream, automatically detecting zstd compression.

        Args:
            file: Binary input stream (file-like object)

        Returns:
            BinSet instance

        Raises:
            ValueError: If the data is invalid or decompression fails
        """
        data = file.read()

        try:
            dctx = zstd.ZstdDecompressor()
            json_bytes = dctx.decompress(data)
        except zstd.ZstdError:
            json_bytes = data

        json_str = json_bytes.decode()
        return cls.model_validate_json(json_str)

    def add_contig_annotations(self, gff: Path, overwrite: bool = False) -> "BinSet":
        """Annotate the contigs in the BinSet with the given GFF file.

        Args:
            gff: Path to the GFF file
            overwrite: Whether to overwrite existing annotations

        Returns:
            BinSet: A new BinSet with annotated contigs
        """
        new_contigs = ContigAnnotator().annotate_contigs(self.contigs, gff, overwrite)
        return self.model_copy(update={"contigs": new_contigs})

    def add_bins_from_fasta(
        self,
        fasta: list[Path],
        group: str,
        binsplit_separator: str | None,
    ) -> "BinSet":
        """Add bins from a FASTA file to the BinSet.

        Args:
            fasta: List of paths to FASTA files
            group: Group name for the bins
            rename_prefix: Prefix to use for renaming contigs
            binsplit_separator: Separator to use for splitting contigs

        Returns:
            A new BinSet with the bins added
        """
        out_bins = [] if self.bins is None else self.bins
        new_bins = parse_fasta_bins(fasta, group, self.contigs, binsplit_separator)

        return self.model_copy(update={"bins": out_bins + new_bins})

    def add_contig_coverage(
        self,
        coverage_file: Path,
        coverage_tool: CoverageTool,
        column_regex: str,
    ) -> "BinSet":
        """Add coverage data to the BinSet from a coverage file.

        Args:
            coverage_file: Path to the coverage file
            coverage_tool: Tool used to generate the coverage file

        Returns:
            A new BinSet with the coverage data added
        """
        new_contigs = CoverageReader().add_coverage(
            contigs=self.contigs,
            coverage_file=coverage_file,
            coverage_tool=coverage_tool,
            column_regex=column_regex,
        )
        return self.model_copy(update={"contigs": new_contigs})

    def add_bin_quality_scores(
        self, quality_file: Path, qc_tool: QualityTool
    ) -> "BinSet":
        if self.bins is None:
            logger.warning("No bins to add quality scores to.")
            return self

        new_bins = QualityReader().add_quality_scores(
            bins=self.bins,
            quality_file=quality_file,
            qc_tool=qc_tool,
        )
        return self.model_copy(update={"bins": new_bins})

    def add_bin_taxonomy(
        self, taxonomy_file: Path, taxonomy_source: str | None
    ) -> "BinSet":
        if self.bins is None:
            logger.warning("No bins to add taxonomy to.")
            return self

        new_bins = TaxonomyReader().add_taxonomy(
            bins=self.bins,
            taxonomy_file=taxonomy_file,
            taxonomy_source=taxonomy_source,
        )
        return self.model_copy(update={"bins": new_bins})

    def filter_bins(self, query: str) -> "BinSet":
        if self.bins is None:
            return self.model_copy(update={"bins": None})

        filter_func = parse_filter_query(query)

        filtered_bins = [bin for bin in self.bins if filter_func(bin)]

        return self.model_copy(update={"bins": filtered_bins})

    def rename_bins(self, template: str) -> "BinSet":
        """Rename bins using a template with field name injection.

        Template placeholders are replaced with bin field values. If multiple bins
        end up with the same name, numeric suffixes are appended (_1, _2, etc.).

        Args:
            template: A template string with field placeholders like "bin_{taxon_name}"
                     Available placeholders: id, group, completeness, contamination,
                     phylum, taxon_name, and other bin/statistics/taxonomy fields.

        Returns:
            A new BinSet with renamed bins

        Raises:
            ValueError: If the template contains invalid field references

        Examples:
            binset.rename_bins("bin_{taxon_name}")
            # Returns: bin_Bacteroides sp., bin_Firmicutes sp., etc.

            binset.rename_bins("bin_{group}_{id}")
            # Returns: bin_group1_original_id, etc.
        """
        if self.bins is None:
            logger.warning("No bins to rename!")
            return self

        renamed_bins = apply_rename_bins(self.bins, template)
        return self.model_copy(update={"bins": renamed_bins})

    def remove_unreferenced_contigs(self) -> "BinSet":
        """Trim the BinSet to remove contigs not used by any bin."""
        output_contigs = {
            contig_id: contig
            for contig_id, contig in self.contigs.items()
            if contig_id in self.bin_contig_ids
        }
        return self.model_copy(update={"contigs": output_contigs})

    def update_statistics(self) -> "BinSet":
        """Update the statistics for each bin in the BinSet.

        Returns:
            A new BinSet instance with updated bin statistics.
        """
        if self.bins is None:
            return self.model_copy()

        updated_bins = [bin.update_statistics(self.contigs) for bin in self.bins]
        return self.model_copy(update={"bins": updated_bins})
