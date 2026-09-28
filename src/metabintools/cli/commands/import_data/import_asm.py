from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.enums import Assembler
from metabintools.export.binset_exporter import BinSetExporter
from metabintools.import_data.assembly import parse_assembly_fasta


@click.command("asm")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--assembler",
    type=click.Choice(Assembler),
    help="Name of the assembler used to produce the assembly (optional)",
    required=False,
)
@click.option("--output", "-o", type=click.File("wb"), default="-", required=False)
@click.argument(
    "assembly",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="The assembly to import.",
)
def import_assembly(
    assembly: str, assembler: Assembler | None, output: IO, compress: bool = False
):
    """Import a metagenome assembly to initialise a BINS file."""
    try:
        assembly_path = Path(assembly)
        logger.info(f"Parsing assembly: {assembly_path.name}")

        try:
            parsed_assembly = parse_assembly_fasta(
                assembly_path,
                assembler,
            )
        except RuntimeError as e:
            logger.error(f"Failed to parse assembly: {e}")
            raise click.ClickException(f"Failed to parse assembly: {e}")

        logger.info(
            f"Successfully parsed assembly with {len(parsed_assembly) if parsed_assembly else 0} contig(s)"
        )

        binset = BinSet(contigs=parsed_assembly, bins=None)

        logger.info("Writing BINS file...")
        BinSetExporter(binset).write_binsfile(output, compress=compress)
        logger.info("Assembly import completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
