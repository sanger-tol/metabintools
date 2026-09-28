from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.enums import CoverageTool
from metabintools.export.binset_exporter import BinSetExporter


@click.command("coverage")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--coverage",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Coverage file with contig-level coverage information",
    required=True,
)
@click.option(
    "--tool",
    type=click.Choice(CoverageTool),
    help="Tool used to estimate coverage",
    required=False,
    default=CoverageTool.metabat,
)
@click.option("--output", "-o", type=click.File("wb"), default="-", required=False)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    required=True,
    default="-",
    help="The BINS file to annotate",
)
def import_coverage(
    binsfile: IO,
    coverage: str,
    output: IO,
    tool: CoverageTool,
    compress: bool = False,
):
    """Add quality scores to a BINS file from a coverage file.

    The coverage file must come from Metabat2's jgi_summarize_bam_depths script.
    """
    try:
        logger.info("Reading BINS file...")
        binset = BinSet.read_binsfile(binsfile)

        logger.info(f"Adding coverage data from {Path(coverage).name}...")
        out_binset = binset.add_contig_coverage(Path(coverage), tool)

        logger.info("Updating statistics...")
        out_binset = out_binset.update_statistics()

        logger.info("Writing BINS file...")
        BinSetExporter(out_binset).write_binsfile(output, compress=compress)
        logger.info("Coverage import completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
