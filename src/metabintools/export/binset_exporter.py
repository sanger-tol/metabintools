import csv
from pathlib import Path
from typing import IO

import click
import zstandard as zstd
from loguru import logger


class BinSetExporter:
    def __init__(self, binset):
        self.binset = binset

    def write_binsfile(self, file: IO, compress: bool = False, level: int = 3):
        """
        Write the BinSet to a binary stream, optionally compressing it with zstd.

        Args:
            file: Binary output stream (file-like object)
            compress: Whether to compress the output
            level: Compression level (default: 3)
        """
        json_str = self.binset.model_dump_json()
        json_bytes = json_str.encode()

        if compress:
            cctx = zstd.ZstdCompressor(level=level)
            compressed_data = cctx.compress(json_bytes)
            file.write(compressed_data)
        else:
            file.write(json_bytes)

        file.flush()

    def export_fasta(
        self,
        outdir: Path,
        compress: bool,
        preserve_headers: bool = False,
        group_fasta: bool = False,
    ):
        """
        Export FASTA files for each bin in the BinSet.

        Args:
            outdir: Directory to save FASTA files
            compress: Whether to compress the output
            preserve_headers: Whether to preserve FASTA headers
        """
        if self.binset.bins is None:
            logger.error("No bins to export.")
            raise click.ClickException("No bins to export.")
        for bin in self.binset.bins:
            logger.info(f"Exporting FASTA for bin {bin.id}.")
            export_path = outdir
            if group_fasta:
                export_path = outdir / bin.group
                if not export_path.exists():
                    export_path.mkdir(parents=True, exist_ok=True)

            bin.export_fasta(
                self.binset.contigs, export_path, preserve_headers, compress
            )

    def export_gff(self, outdir: Path, group_gff: bool):
        """
        Export GFF files for each bin in the BinSet.

        Args:
            outdir: Directory to save FASTA files
        """
        if self.binset.bins is None:
            logger.error("No bins to export.")
            raise click.ClickException("No bins to export.")
        for bin in self.binset.bins:
            logger.info(f"Exporting GFF for bin {bin.id}.")
            export_path = outdir
            if group_gff:
                export_path = outdir / bin.group
                if not export_path.exists():
                    export_path.mkdir(parents=True, exist_ok=True)

            bin.export_gff(self.binset.contigs, export_path)

    def export_contig2bin(self, path: Path, group: str | None):
        """
        Export a contig-to-bin mapping file in DAS_Tool format.

        Args:
            path: Path to save the contig-to-bin mapping
        """
        if self.binset.bins is None:
            logger.error("No bins to export.")
            raise click.ClickException("No bins to export.")

        with open(path, "w") as f:
            for bin in self.binset.bins:
                if group is None or group == bin.group:
                    contigs = bin.contigs
                    f.writelines(f"{contig}\t{bin.id}\n" for contig in contigs)

    def summarise_bins(
        self,
        include_statistics: bool = True,
        include_taxonomy: bool = True,
    ) -> list[dict[str, str | int | float | None]]:
        """
        Flatten the bins in the BinSet into a list of dictionaries.

        Args:
            include_statistics: Whether to include statistics in the output.
            include_taxonomy: Whether to include taxonomy in the output.

        Returns:
            A dictionary summarising the bins
        """
        out_list = []
        if self.binset.bins is None:
            return out_list
        for bin in self.binset.bins:
            bin_dict = bin.model_dump(exclude={"statistics", "taxonomy", "contigs"})

            if include_statistics:
                if bin.statistics is not None:
                    bin_dict.update(bin.statistics.model_dump(exclude_none=False))
                else:
                    logger.warning(f"Bin {bin.id} has no statistics.")
            if include_taxonomy:
                if bin.taxonomy is not None:
                    bin_dict.update(bin.taxonomy.model_dump(exclude_none=False))
                else:
                    logger.warning(f"Bin {bin.id} has no taxonomy.")

            out_list.append(bin_dict)

        return out_list

    def summarise_contigs(
        self,
    ) -> list[dict[str, str | int | float | None]]:
        """
        Summarise the contigs in the binset.

        Returns:
            A list of dictionaries, each representing a contig.
        """
        out_list = []
        for contig in self.binset.contigs.values():
            contig_dict = contig.model_dump(exclude={"annotations", "sequence"})
            contig_dict.update({"trnas": ",".join(contig_dict["trnas"])})
            out_list.append(contig_dict)
        return out_list

    def write_contig_summary_tsv(self, output_path: Path) -> None:
        """
        Write a TSV file from the summarised contigs.

        Args:
            output_path: Path to write the TSV file to.
        """
        summarised = self.summarise_contigs()
        if not summarised:
            logger.warning("No contigs to write.")
            return

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(
                f, fieldnames=list(summarised[0].keys()), delimiter="\t"
            )
            writer.writeheader()
            writer.writerows(summarised)

    def write_bin_summary_tsv(
        self,
        output_path: Path,
        include_statistics: bool = True,
        include_taxonomy: bool = True,
    ) -> None:
        """
        Write a TSV file from the summarised bins.

        Args:
            output_path: Path to write the TSV file to.
            include_statistics: Whether to include statistics in the output.
            include_taxonomy: Whether to include taxonomy in the output.
        """

        summarised = self.summarise_bins(
            include_statistics=include_statistics,
            include_taxonomy=include_taxonomy,
        )

        if not summarised:
            logger.warning("No bins to write.")
            return

        # Collect all unique fieldnames from all bins
        all_fieldnames = []
        seen = set()
        for row in summarised:
            for key in row:
                if row[key] is None:
                    row[key] = ""
                if key not in seen:
                    all_fieldnames.append(key)
                    seen.add(key)

        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_fieldnames, delimiter="\t")
            writer.writeheader()
            writer.writerows(summarised)

        logger.info(f"Wrote summary to {output_path}")

    def write_group_summary_tsv(
        self,
        output_path: Path,
    ) -> None:
        """
        Write a TSV file summarising bins at the group level.

        Args:
            output_path: Path to write the TSV file to.
        """
        summaries = self.summarise_bins(include_statistics=True, include_taxonomy=False)
        out_dict = {}

        for summary in summaries:
            group = summary["group"]
            mimag = summary["mimag"]

            if out_dict.get(group) is None:
                out_dict[group] = {
                    "total": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "unknown": 0,
                }

            out_dict[group]["total"] += 1

            mimag_key = str(mimag) if mimag is not None else "unknown"
            if mimag_key in out_dict[group]:
                out_dict[group][mimag_key] += 1

        # Write to TSV
        fieldnames = ["group", "total", "high", "medium", "low", "unknown"]
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
            writer.writeheader()
            for group, counts in out_dict.items():
                row = {"group": group, **counts}
                writer.writerow(row)
