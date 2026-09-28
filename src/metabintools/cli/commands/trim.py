from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("trim")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--output",
    "-o",
    type=click.File("wb"),
    default="-",
    required=False,
    help="Output file for trimmed bins (defaults to stdout)",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    nargs=1,
    required=True,
    help="Input BINS file to trim.",
)
def trim(
    binsfile: IO,
    output: IO,
    compress: bool = False,
):
    """Trim a BINS file by removing unreferenced contigs."""
    try:
        logger.info(f"Reading BINS file from {binsfile.name}...")
        binset = BinSet.read_binsfile(binsfile)

        logger.info("Trimming unreferenced contigs...")
        trimmed_binset = binset.remove_unreferenced_contigs()

        logger.info("Writing trimmed BINS file...")
        BinSetExporter(trimmed_binset).write_binsfile(output, compress=compress)
        logger.info("Trim operation completed successfully.")

    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
