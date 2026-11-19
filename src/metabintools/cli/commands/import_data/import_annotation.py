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
    help="A GFF file to add the annotations from. Can be supplied multiple times.",
    required=True,
    multiple=True,
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
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
    binsfile: IO,
    gff: tuple[str, ...],
    output: IO,
    compress: bool = False,
    overwrite: bool = False,
):
    """Add annotations from one or more GFF files to a BINS file"""
    try:
        logger.info("Reading BINS file...")
        annotated_binset = BinSet.read_binsfile(binsfile)

        for i, gff_path in enumerate(gff):
            logger.info(f"Adding annotations from {Path(gff_path).name}...")
            try:
                # Only the first file may overwrite; later files append so that
                # annotations from earlier GFFs are not discarded.
                annotated_binset = annotated_binset.add_contig_annotations(
                    Path(gff_path), overwrite=overwrite and i == 0
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
