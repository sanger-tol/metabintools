from pathlib import Path

import pyfastx
from loguru import logger

from metabintools.bin_utils import get_basename
from metabintools.dataclasses.bin import Bin
from metabintools.dataclasses.contig import Contig


def parse_fasta_bins(
    fasta: list[Path],
    group: str,
    asm_contigs: dict[str, Contig],
    binsplit_separator: str | None = None,
) -> list[Bin]:
    """
    Parse a list of bin files into a list of Bin objects.

    Args:
        bins: A list of paths to the bin files.
        group: The group to assign to the bins.
        binsplit_separator: If binsplitting was used to generate the contigs, the separator to use to split the contig id and sample id.

    Returns:
        A list of Bin objects.
    """
    output_bins = []

    for idx, bin_path in enumerate(fasta):
        b = pyfastx.Fastx(bin_path)

        if binsplit_separator:
            contigs = [id.split(binsplit_separator)[1] for id, seq in b]
        else:
            contigs = [id for id, seq in b]

        id = get_basename(bin_path)

        bin_obj = Bin(
            id=id,
            import_name=bin_path.name,
            group=group,
            contigs=contigs,
            statistics=None,
        )
        bin_obj = bin_obj.update_statistics(asm_contigs)
        output_bins.append(bin_obj)

    logger.info(f"Parsed {len(output_bins)} bins.")
    for bin in output_bins:
        logger.debug(f"Parsed bin: {bin.id}")

    return output_bins
