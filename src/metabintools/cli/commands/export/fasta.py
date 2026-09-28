from pathlib import Path
from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter


@click.command("fasta")
@click.option(
    "--compress",
    "-z",
    "compress",
    is_flag=True,
    help="(optional) Compress the output using zstd.",
)
@click.option(
    "--outdir",
    "-o",
    type=click.Path(dir_okay=True, file_okay=False),
    required=True,
    default=".",
    help="Output directory for FASTA files",
)
@click.option(
    "--preserve-headers",
    "-h",
    is_flag=True,
    help="(optional) Preserve headers in the output FASTA file.",
    default=False,
)
@click.option(
    "--group-fasta",
    "-g",
    is_flag=True,
    help="(optional) Write each FASTA in a subdirectory named after the bin's group.",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    nargs=1,
    required=True,
    default="-",
    help="Input binsfile to export from",
)
def fasta(
    binsfile: IO,
    outdir: str,
    compress: bool = False,
    preserve_headers: bool = False,
    group_fasta: bool = False,
):
    """Export a BINS file to FASTA."""
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
            f"Exporting {len(binset.bins) if binset.bins else 0} bin(s) to FASTA..."
        )
        BinSetExporter(binset).export_fasta(
            outdir=outdir_path,
            compress=compress,
            preserve_headers=preserve_headers,
            group_fasta=group_fasta,
        )
        logger.info("FASTA export completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
