from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter
from metabintools.operations.merge import merge_binsets


@click.command("merge")
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
    help="Output file for merged BINS files (defaults to stdout)",
)
@click.argument(
    "binsfiles",
    type=click.File("rb"),
    nargs=-1,
    required=True,
    help="Input BINS files to merge",
)
def merge(
    binsfiles: list[IO],
    output: IO,
    compress: bool = False,
):
    """Merge a set of BINS files together."""
    try:
        logger.info(f"Reading {len(binsfiles)} BINS file(s)...")
        binsets = []
        for i, binsfile in enumerate(binsfiles, 1):
            logger.info(f"Reading BINS file {i}/{len(binsfiles)}: {binsfile.name}")
            binsets.append(BinSet.read_binsfile(binsfile))

        logger.info(f"Merging {len(binsfiles)} BINS files...")
        merged = merge_binsets(binsets)

        logger.info("Writing merged BINS file...")
        BinSetExporter(merged).write_binsfile(output, compress=compress)
        logger.info("Merge operation completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
