from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("gff")
@click.option(
    "--outdir",
    "-o",
    type=click.Path(dir_okay=True, file_okay=False),
    required=True,
    default=".",
    help="Output directory for GFF files",
)
@click.option(
    "-g",
    "--group-gff",
    is_flag=True,
    help="(optional) Write each FASTA in a subdirectory named after the bin's group.",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    nargs=1,
    required=True,
    default="-",
    help="Input BINS file to export (use '-' for stdin)",
)
def gff(
    binsfile: IO,
    outdir: str,
    group_gff: bool = False,
):
    """Write stored bin annotations to a set of GFF files."""
    try:
        logger.info(f"Reading BINS file from {binsfile.name}...")
        binset = BinSet.read_binsfile(binsfile)

        outdir_path = Path(outdir)
        if not outdir_path.exists():
            logger.info(f"Creating output directory: {outdir_path}")
            try:
                outdir_path.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create output directory: {e}")
                raise click.ClickException(
                    f"Failed to create output directory {outdir}: {e}"
                )

        logger.info(
            f"Exporting {len(binset.bins) if binset.bins else 0} bin(s) to GFF..."
        )
        BinSetExporter(binset).export_gff(
            outdir=outdir_path,
            group_gff=group_gff,
        )
        logger.info("GFF export completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
