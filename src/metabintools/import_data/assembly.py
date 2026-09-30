import re
from pathlib import Path

import pyfastx
from loguru import logger

from metabintools.dataclasses.contig import Contig
from metabintools.enums import Assembler


def parse_assembly_fasta(
    assembly: Path, assembler: Assembler | None
) -> dict[str, Contig]:
    """
    Parse an assembly FASTA file into a list of Contig objects.

    Args:
        assembly: The path to the assembly FASTA file.
        assembler: The assembler used to generate the assembly.

    Returns:
        A dict of Contig objects sorted by sequence length (longest first).
    """
    _CIRCULAR_REGEX = {
        "myloasm": re.compile(r"circular-yes|circular-possibly"),
        "metamdbg": re.compile(r"circular=yes"),
    }

    parser = pyfastx.Fastx(str(assembly), comment=True)
    topology_regex = _CIRCULAR_REGEX.get(str(assembler))

    names = set()
    contigs = {}

    for id, seq, comment in parser:
        if id in names:
            raise ValueError(f"Duplicate sequence id: {id}")
        names.add(id)

        topology = "linear"
        if topology_regex and topology_regex.search(f"{id} {comment}"):
            topology = "circular"

        logger.debug(f"ADDING CONTIG: {id}, topology={topology}")

        sequence = seq.upper()
        contig = Contig(
            id=id,
            header=f"{id} {comment}",
            sequence=sequence,
            sequence_length=len(sequence),
            topology=topology,
        )
        contigs[id] = contig

    sorted_contigs = dict(
        sorted(
            contigs.items(),
            key=lambda item: item[1].sequence_length,
            reverse=True,
        )
    )
    return sorted_contigs
