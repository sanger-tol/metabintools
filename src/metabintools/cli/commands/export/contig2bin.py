from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("contig2bin")
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, file_okay=True, exists=False),
    required=True,
    default=".",
    help="Output file path for the contig2bin mapping",
)
@click.option(
    "-g",
    "--group",
    type=str,
    help="Write bins from a specific group (if not specified, all bins are included)",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    nargs=1,
    required=True,
    default="-",
    help="Input binsfile to export from.",
)
def contig2bin(
    binsfile: IO,
    output: str,
    group: str | None = None,
):
    """Write stored bin annotations to a set of GFF files."""
    try:
        logger.info(f"Reading BINS file from {binsfile.name}...")
        binset = BinSet.read_binsfile(binsfile)

        output_path = Path(output)
        logger.info(f"Writing contig2bin mapping to {output_path}")

        BinSetExporter(binset).export_contig2bin(
            path=output_path,
            group=group,
        )

        logger.info("Contig2bin export completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
