import sys
from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("annotation")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--gff",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="The GFF file to add the annotations from.",
    required=True,
)
@click.option(
    "--overwrite",
    type=bool,
    help="Overwrite existing annotations if they already exist",
    required=False,
)
@click.option("--output", "-o", type=click.File("wb"), default="-", required=False)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    required=True,
    default="-",
    help="Input BINS file to add annotations to.",
)
def import_annotation(
    binsfile: IO, gff: str, output: IO, compress: bool = False, overwrite: bool = False
):
    """Add annotations from a GFF file to a BINS file"""
    try:
        logger.info("Reading BINS file...")
        binset = BinSet.read_binsfile(binsfile)

        logger.info(f"Adding annotations from {Path(gff).name}...")
        try:
            annotated_binset = binset.add_contig_annotations(
                Path(gff), overwrite=overwrite
            )
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to add annotations: {e}")
            raise click.ClickException(f"Failed to add annotations: {e}")

        logger.info("Updating statistics...")
        annotated_binset = annotated_binset.update_statistics()

        logger.info("Writing BINS file...")
        BinSetExporter(annotated_binset).write_binsfile(output, compress=compress)
        logger.info("Annotation import completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
