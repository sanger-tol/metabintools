from typing import IO

import click
from loguru import logger

from metabintools.dataclasses.binset import BinSet
from metabintools.export.binset_exporter import BinSetExporter
from metabintools.query.query_parser import get_available_fields


@click.command("view")
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
    help="Output file for filtered bins (defaults to stdout)",
)
@click.option(
    "--list-fields",
    is_flag=True,
    help="List all available fields for filtering and exit.",
)
@click.argument(
    "binsfile",
    type=click.File("rb"),
    required=False,
    help="Input BINS file to filter",
)
@click.argument(
    "query",
    required=False,
    help="Filter query expression (e.g., 'group == \"high_quality\" and completeness >= 0.9')",
)
def view_bins(
    binsfile: IO | None,
    query: str | None,
    output: IO,
    compress: bool = False,
    list_fields: bool = False,
):
    """Filter bins from a BINS file based on a query expression.

    Examples:
        # Filter by group
        metabintools filter input.bin 'group == "high_quality"' -o output.bin

        # Filter by completeness and contamination
        metabintools filter input.bin 'completeness >= 0.9 and contamination <= 0.05' -o output.bin

        # Filter by taxonomy
        metabintools filter input.bin 'phylum == "Bacteroidetes"' -o output.bin

        # Combine multiple conditions
        metabintools filter input.bin 'group == "archaea" and completeness >= 0.8' -o output.bin
    """
    try:
        if list_fields:
            click.echo("Available fields for filtering:")
            for field, description in sorted(get_available_fields().items()):
                click.echo(f"  {field:20} - {description}")
            return

        if binsfile is None:
            logger.error("BINSFILE argument is required (unless using --list-fields)")
            raise click.ClickException(
                "BINSFILE argument is required (unless using --list-fields)"
            )

        logger.info("Reading BINS file...")
        binset = BinSet.read_binsfile(binsfile)

        if query is None or query.strip() == "":
            logger.info("No filter query provided, writing full BINS file.")
            BinSetExporter(binset).write_binsfile(output, compress=compress)
            return

        if binset.bins is None:
            logger.warning("No bins found in input file.")
            BinSetExporter(binset).write_binsfile(output, compress=compress)
            return

        logger.info(f"Filtering {len(binset.bins)} bins with query: {query}")

        try:
            filtered_binset = binset.filter_bins(query)
        except ValueError as e:
            raise click.ClickException(f"Invalid filter query: {e}")

        logger.info(
            f"Filter complete: {len(filtered_binset.bins) if filtered_binset.bins else 0} "
            f"of {len(binset.bins)} bins matched."
        )

        logger.info("Writing filtered BINS file...")
        BinSetExporter(filtered_binset).write_binsfile(output, compress=compress)
        logger.info("Filter operation completed successfully.")

    except click.ClickException:
        raise
    except OSError as e:
        logger.error(f"File I/O error: {e}")
        raise click.ClickException(f"File I/O error: {e}")
