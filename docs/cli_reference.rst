CLI Reference
==============

This page documents the complete command-line interface for metabintools.

All commands support reading from stdin (``-``) and writing to stdout (``-``), enabling Unix pipes.
Commands support compression with the ``-z`` flag, and the format is auto-detected on input.

Note that the standard binary is called ``metabintools``, but the binary ``bintools`` is provided as an alias.

Import Commands
===============

The ``import`` group contains commands for adding data to a BINS file.

import asm
----------

Import a metagenomic assembly to initialize a BINS file.

.. code-block:: bash

   metabintools import asm ASSEMBLY [OPTIONS]

Arguments:

- ``ASSEMBLY``: Input FASTA file (required; path to file)

Options:

- ``--assembler {spades,megahit,flye,metamdbg,myloasm,hifiasm_meta}``: Assembler used to generate the assembly (optional)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Features:

- Automatically detects circular contigs from assembler-specific headers
- Supports gzip-compressed FASTA files
- Validates sequence content

Example:

.. code-block:: bash

   metabintools import asm assembly.fasta --assembler metamdbg -o project.bins

import binset
-------------

Add bins from binning tool output.

.. code-block:: bash

   metabintools import binset BINSFILE FASTA [FASTA ...] --group NAME [OPTIONS]

Arguments:

- ``BINSFILE``: Existing BINS file to add bins to (use ``-`` for stdin)
- ``FASTA``: Bin FASTA files or directories containing them

Options:

- ``--group NAME``: Name for this bin group (required)
- ``--binsplit-separator SEP``: Separator for recovering contig names (e.g., ":" for VAMB/SemiBin2)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Example:

.. code-block:: bash

   metabintools import binset project.bins bins/ --group "metabat" -o project.bins

import annotation
-----------------

Add GFF3 annotations to contigs.

.. code-block:: bash

   metabintools import annotation --gff <GFF> BINSFILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to annotate (use ``-`` for stdin)

Options:

- ``--gff``: GFF3 annotation file (required)
- ``--overwrite``: Overwrite existing annotations (flag, default: false)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Example:

.. code-block:: bash

   metabintools import annotation project.bins annotations.gff -o project.bins

import coverage
---------------

Add coverage data to contigs.

.. code-block:: bash

   metabintools import coverage --coverage <TSV> --column-regex <str> BINSFILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to add coverage to (use ``-`` for stdin)

Options:

- ``--coverage``: Coverage TSV file (required)
- ``--tool {metabat}``: Tool that generated the coverage file (default: metabat)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Example:

.. code-block:: bash

   metabintools import coverage project.bins coverage.tsv --tool metabat -o project.bins

import quality
---------------

Add quality scores from binning assessment tools.

.. code-block:: bash

   metabintools import quality BINSFILE --quality FILE --tool TOOL [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to add quality to (use ``-`` for stdin)

Options:

- ``--quality FILE``: Quality assessment file (required)
- ``--tool {checkm,checkm2,busco,manual}``: QC tool used (default: manual)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Notes:

- For CheckM, CheckM2, and BUSCO: use output files directly
- For manual TSV: must have fields ``File``, ``Completeness``, and ``Contamination``

Example:

.. code-block:: bash

   metabintools import quality project.bins --quality checkm2.tsv --tool checkm2 -o project.bins

import taxonomy
----------------

Add taxonomic classifications to bins.

.. code-block:: bash

   metabintools import taxonomy BINSFILE --taxonomy FILE --tool TOOL [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to add taxonomy to (use ``-`` for stdin)

Options:

- ``--taxonomy FILE``: Taxonomy file (required)
- ``--tool {gtdbtk,gtdbtk_ncbi,manual}``: Taxonomy tool used (default: manual)
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Notes:

- For GTDB-Tk: use the ar122_summary.tsv or bac120_summary.tsv files
- For GTDB-Tk NCBI: use output from ``gtdb_to_ncbi_majority_vote.py`` script
- For manual TSV: must have fields ``File`` and ``Classification`` (lineage string format: ``k__.*;p__.*...``)

Example:

.. code-block:: bash

   metabintools import taxonomy project.bins --taxonomy gtdbtk.tsv --tool gtdbtk -o project.bins

Export Commands
===============

The ``export`` group contains commands for extracting data from BINS files.

export fasta
------------

Export bins to individual FASTA files.

.. code-block:: bash

   metabintools export fasta BINSFILE --outdir DIR [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to export (use ``-`` for stdin)

Options:

- ``--outdir, -o``: Output directory (required)
- ``--compress, -z``: Compress output FASTA files with gzip
- ``--preserve-headers, -h``: Keep original FASTA headers
- ``--group-fasta, -g``: Create subdirectories for each bin group

Example:

.. code-block:: bash

   metabintools export fasta project.bins -o bins/ --group-fasta

export gff
----------

Export bin annotations to GFF3 files.

.. code-block:: bash

   metabintools export gff BINSFILE --outdir DIR [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to export

Options:

- ``--outdir, -o``: Output directory (required)
- ``--group-gff, -g``: Create subdirectories for each bin group

Example:

.. code-block:: bash

   metabintools export gff project.bins -o annotations/

export contig2bin
------------------

Export contig-to-bin mapping in DAS_Tool format.

.. code-block:: bash

   metabintools export contig2bin BINSFILE --output FILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to export (use ``-`` for stdin)

Options:

- ``--output, -o``: Output file path (required)
- ``--group, -g``: Export only bins from a specific group (optional)

Example:

.. code-block:: bash

   metabintools export contig2bin project.bins -o contig2bin.tsv

   # Export only a specific group
   metabintools export contig2bin project.bins -o contig2bin.tsv --group metabat

View Command
==============

Filter bins from a BINS file based on a query expression.

.. code-block:: bash

   metabintools view BINSFILE [QUERY] [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to filter (use ``-`` for stdin)
- ``QUERY``: Filter expression (optional; if omitted, all bins are included)

Options:

- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)
- ``--list-fields``: Show all available filter fields and exit

Examples:

.. code-block:: bash

   # Filter by quality
   metabintools view project.bins 'completeness >= 0.9' -o hq.bins

   # Filter by multiple criteria
   metabintools view project.bins 'completeness >= 0.9 and contamination <= 0.05' -o hq.bins

   # Filter by taxonomy
   metabintools view project.bins 'phylum == "Bacteroidetes"' -o output.bins

   # Filter by group
   metabintools view project.bins 'group == "metabat"' -o output.bins

   # List available fields
   metabintools view --list-fields

Available filter fields (see ``--list-fields`` for complete list):

- **id**: Bin identifier
- **group**: Bin group name
- **length**: Total bin size in bp
- **n_contigs**: Number of contigs
- **n_circular**: Number of circular contigs
- **completeness**: Completeness estimate (0.0-1.0)
- **contamination**: Contamination estimate (0.0-1.0)
- **coverage**: Average coverage
- **mimag**: MiMAG quality level (high, medium, low)
- **kingdom, phylum, class, order, family, genus, species**: Taxonomy fields

Merge Command
=============

Combine multiple BINS files into one.

.. code-block:: bash

   metabintools merge BINSFILES [BINSFILES ...] [OPTIONS]

Arguments:

- ``BINSFILES``: BINS files to merge

Options:

- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Example:

.. code-block:: bash

   metabintools merge set1.bins set2.bins set3.bins -o merged.bins

Trim Command
============

Remove contigs not referenced by any bin.

.. code-block:: bash

   metabintools trim BINSFILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to trim

Options:

- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Example:

.. code-block:: bash

   metabintools trim project.bins -o trimmed.bins

Rename Command
==============

Rename bins using a template with field injection.

.. code-block:: bash

   metabintools rename BINSFILE --bin-name TEMPLATE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to rename bins in (use ``-`` for stdin)

Options:

- ``--bin-name, -n``: Rename template with field placeholders (required)
- ``--list-fields``: Show available fields for templates
- ``--compress, -z``: Compress output with zstd
- ``--output, -o``: Output BINS file path (default: stdout)

Templates use field names in curly braces. Available fields can be listed with ``--list-fields``:

.. code-block:: bash

   metabintools rename project.bins -n "bin_{tax_phylum}_{completeness}" -o renamed.bins

If multiple bins end up with the same name, numeric suffixes are added (_1, _2, etc.).

Summarise Commands
==================

Generate summary reports from BINS files.

summarise bins
--------------

Create a TSV summary of bins in a BINS file.

.. code-block:: bash

   metabintools summarise bins BINSFILE --output FILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to summarise (use ``-`` for stdin)

Options:

- ``--output, -o``: Output TSV file path (required)
- ``--include-statistics, -s``: Include computed statistics (default: true)
- ``--include-taxonomy, -t``: Include taxonomy information (default: true)

Example:

.. code-block:: bash

   metabintools summarise bins project.bins -o bin_summary.tsv

summarise contigs
------------------

Create a TSV summary of contigs in a BINS file.

.. code-block:: bash

   metabintools summarise contigs BINSFILE --output FILE

Arguments:

- ``BINSFILE``: BINS file to summarise (use ``-`` for stdin)

Options:

- ``--output, -o``: Output TSV file path (required)

Example:

.. code-block:: bash

   metabintools summarise contigs project.bins -o contig_summary.tsv

summarise groups
----------------

Create an aggregated TSV summary of bin groups, showing counts of bins at each MiMAG level

.. code-block:: bash

   metabintools summarise groups BINSFILE --output FILE [OPTIONS]

Arguments:

- ``BINSFILE``: BINS file to summarise (use ``-`` for stdin)

Options:

- ``--output, -o``: Output TSV file path (required)

Example:

.. code-block:: bash

   metabintools summarise groups project.bins -o bin_summary.tsv
