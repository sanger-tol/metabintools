import csv
import re
from pathlib import Path

from loguru import logger

from metabintools.dataclasses.contig import Contig
from metabintools.enums import CoverageTool


class CoverageReader:
    @staticmethod
    def _read_jgi_summarise_contig_depths(
        coverage_file: Path, column_regex: str
    ) -> dict[str, float]:
        """Reads a JGI SummarizeContigDepths coverage file and returns a dictionary of contig names to coverage values."""
        coverage: dict[str, float] = {}
        regex = re.compile(column_regex)

        with open(coverage_file, "r") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if not reader.fieldnames:
                logger.error(f"No fieldnames found in coverage file: {coverage_file}")
                return coverage

            matching_columns = [
                col
                for col in reader.fieldnames
                if regex.search(col) and not col.endswith("var")
            ]

            if len(matching_columns) == 0:
                logger.error(
                    f"No matching columns found in coverage file: {coverage_file}"
                )
                return coverage

            if len(matching_columns) > 1:
                logger.error(
                    f"Too many matching columns found in coverage file: {coverage_file}"
                )
                return coverage

            for row in reader:
                contig_name = row["contigName"]
                coverage[contig_name] = float(row[matching_columns[0]])

            return coverage

    def add_coverage(
        self,
        contigs: dict[str, Contig],
        coverage_file: Path,
        coverage_tool: CoverageTool,
        column_regex: str,
    ) -> dict[str, Contig]:
        if coverage_tool == "metabat":
            coverages = self._read_jgi_summarise_contig_depths(
                coverage_file, column_regex
            )
        else:
            logger.error(f"Unknown coverage format: {coverage_tool}")
            return contigs

        return {
            contig_id: contig.model_copy(
                update={"coverage": coverages.get(contig_id, None)}
            )
            for contig_id, contig in contigs.items()
        }
