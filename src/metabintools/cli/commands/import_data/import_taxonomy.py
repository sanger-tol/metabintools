from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.enums import TaxonomyTool
from metabintools.export.binset_exporter import BinSetExporter


@click.command("taxonomy")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--tool",
    type=click.Choice(TaxonomyTool),
    help="Tool used to assign taxonomy to the bins",
    required=True,
)
@click.option(
    "--taxonomy",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
    help="Input file containing bin-level taxonomy information",
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
def import_taxonomy(
    binsfile: IO,
    output: IO,
    taxonomy: str,
    tool: TaxonomyTool,
    compress: bool = False,
):
    """Add a set of quality scores to a BINS file.

    The taxonomy TSV can come from GTDB-Tk or GTDB-Tk's gtdb_to_ncbi_majority_vote.py script, or a manual user-provided TSV.

    A manual TSV must have the fields File and Classification (a lineage string of format k__.*;p__.*...).
    """
    try:
        logger.info("Reading BINS file...")
        binset = BinSet.read_binsfile(binsfile)

        if binset.bins is None:
            logger.error("No bins found in the BINS file.")
            raise click.ClickException("No bins found in the BINS file.")

        logger.info(f"Adding taxonomy from {Path(taxonomy).name}...")
        out_binset = binset.add_bin_taxonomy(Path(taxonomy), tool)

        logger.info("Writing BINS file...")
        BinSetExporter(out_binset).write_binsfile(output, compress=compress)
        logger.info("Taxonomy import completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
