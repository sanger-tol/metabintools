from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.enums import QualityTool
from metabintools.export.binset_exporter import BinSetExporter


@click.command("quality")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--tool",
    type=click.Choice(QualityTool),
    help="The tool used to assess the quality of the bins.",
    required=True,
    default=QualityTool.manual,
)
@click.option(
    "--quality",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Input file containing quality scores.",
    required=True,
)
@click.option("--output", "-o", type=click.File("wb"), default="-", required=False)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    required=True,
    default="-",
    help="The BINS file to annotate",
)
def import_quality(
    binsfile: IO,
    output: IO,
    quality: str,
    tool: QualityTool,
    compress: bool = False,
):
    """Add a set of quality scores to a BINS file.

    The quality TSV can come from CheckM, CheckM2, or BUSCO, or a manual user-provided TSV.

    A user-supplied TSV must have the fields File, Completeness, and Contamination.
    """
    try:
        logger.info("Reading BINS file...")
        binset = BinSet.read_binsfile(binsfile)

        if binset.bins is None:
            logger.error("No bins found in the BINS file.")
            raise click.ClickException("No bins found in the BINS file.")

        logger.info(f"Adding quality scores from {Path(quality).name}...")
        out_binset = binset.add_bin_quality_scores(Path(quality), tool)

        logger.info("Updating statistics...")
        out_binset = out_binset.update_statistics()

        logger.info("Writing BINS file...")
        BinSetExporter(out_binset).write_binsfile(output, compress=compress)
        logger.info("Quality import completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
