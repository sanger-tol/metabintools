from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("groups")
@click.option(
    "--output",
    "-o",
    type=click.Path(exists=False),
    required=True,
    help="Output TSV file path for group summary",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    nargs=1,
    required=True,
    help="The BINS file to summarise.",
)
def summarise_groups(
    binsfile: IO,
    output: str,
):
    """Write an aggregated summary with the total count of bins per group, separated
    by MiMAG scores if available.
    """
    try:
        logger.info("Reading BINS file(s)...")
        binset = BinSet.read_binsfile(binsfile)

        output_path = Path(output)
        logger.info(f"Writing bin summary to {output_path}")

        BinSetExporter(binset).write_group_summary_tsv(
            output_path=output_path,
        )

        logger.info("Group summary completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
