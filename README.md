# metabintools

**metabintools** is a toolkit for managing and manipulating metagenomic binning outputs. It consolidates all bin data, including sequences, annotations, quality metrics, and taxonomy, into a single unified file format for streamlined analysis workflows. This file can be queried, filtered, bins can be renamed using their metadata, and separate files can easily be merged to consolidate bins into a single file.

## Overview

Metagenomic binning produces scattered outputs: bin FASTA files, quality assessments, taxonomic classifications, and annotations in separate formats. **metabintools** unifies these into a single `.bins` file (optionally compressed as `.bins.zstd`), enabling easy filtering, merging, and export via composable command-line operations.

## Key Features

- **Unified file format**: Store bins, contigs, annotations, quality scores, and taxonomy in one `.bins` file
- **Composable operations**: Chain commands via Unix pipes for flexible workflows
- **Powerful filtering**: Query bins by any property (completeness, contamination, taxonomy, etc.)
- **Compression support**: Optional zstd compression for efficient storage
- **Multiple input sources**: Import bin metadata from many metagenomics tools (CheckM, GTDB-Tk, etc.)

## Installation

```bash
pip install metabintools
```

## Quick Start

### 1. Create a BINS file from your assembly

```bash
metabintools import asm assembly.fasta -o binset.bins
```

### 2. Add annotations to your BINS file

```bash
metabintools import annotations binset.bins annotations.gff -o binset.bins
```

### 3. Add bins from your binner

```bash
metabintools import binset binset.bins bins/ --group "myBinner" -o binset.bins
```

### 4. Add quality scores

```bash
metabintools import quality binset.bins checkm_results.tsv --tool checkm -o binset.bins
```

### 5. Add taxonomy

```bash
metabintools import taxonomy binset.bins gtdbtk.tsv --tool gtdbtk -o binset.bins
```

### 6. Filter high-quality bins

```bash
metabintools view binset.bins 'completeness >= 0.9 and contamination <= 0.05' -o hq.bins
```

or, if the required data for MiMAG calls is present (completeness, contamination, tRNAs, rRNAs):

```bash
metabintools view binset.bins 'mimag == "high"' -o hq.bins
```

### 7. Export to FASTA

```bash
metabintools export fasta hq.bins -o output_directory/
```

## Composable Workflows

The real power of metabintools is composability via piping:

```bash
# Filter and export in one pipeline
metabintools view binset.bins 'group == "metabat" and completeness >= 0.8' -z | \
  metabintools export fasta -o filtered_bins/

# Merge multiple binsets and filter
metabintools merge set1.bins.zstd set2.bins.zstd -z | \
  metabintools view - 'contamination <= 0.1' -o merged_hq.bins.zstd

# Extract high-quality archaeal bins
metabintools view binset.bins 'tax_kingdom == "Archaea" and completeness >= 0.85' -o archaea_hq.bins
```

## Filter Query Guide

The `view` command uses simple Python-like syntax:

```bash
# Basic comparisons
metabintools view input.bins 'completeness >= 0.9' -o output.bins
metabintools view input.bins 'length > 1000000' -o output.bins

# Logical operators
metabintools view input.bins 'completeness >= 0.9 and contamination <= 0.05' -o output.bins
metabintools view input.bins 'group == "vamb" or group == "metabat"' -o output.bins

# Taxonomy filtering
metabintools view input.bins 'tax_phylum == "Bacteroidetes"' -o output.bins

# Complex queries
metabintools view input.bins 'group == "archaea" and completeness >= 0.8 and contamination <= 0.1' -o output.bins
```

### Available Filter Fields

List all available fields:

```bash
metabintools view --list-fields
```

## Commands

### import

Import data into a BINS file with validation and error handling:

- **`metabintools import asm`** - Initialize from assembly FASTA
  - Can detect circular contigs from metaMDBG and myloasm

- **`metabintools import binset`** - Add contig clusters from binning
  - Optional binsplit separator recovery (SemiBin2, VAMB compatibility)

- **`metabintools import annotation`** - Add GFF annotations to contigs

- **`metabintools import coverage`** - Add coverage data to contigs
  - Supports multiple coverage tools (e.g., CoverM, custom formats)

- **`metabintools import taxonomy`** - Add taxonomic classifications to bins
  - Supports multiple taxonomy tools (GTDB-Tk, gtdb_to_ncbi_majority_vote.py, manual)

- **`metabintools import quality`** - Add quality scores (CheckM, CheckM2, BUSCO) to bins
  - Supports multiple quality assessment tools

### view

Decompress a bins file, or filter bins by query expression with comprehensive validation:

```bash
metabintools view input.bins.zstd -o input.bins  # decompress
```

or

```bash
metabintools view input.bins 'completeness >= 0.9' -o output.bins
metabintools view input.bins 'completeness >= 0.9' -z -o output.bins.zstd  # compressed
metabintools view --list-fields  # Show all available filter fields
```

### export

Export data from a BINS file:

- **`metabintools export fasta`** - Export each bin to a FASTA file
- **`metabintools export gff`** - Export each bin's annotations to a GFF file
- **`metabintools export contig2bin`** - Export a set of bins to a contig-to-bin mapping (DAS_Tool format)

### merge

Combine multiple BINS files with progress tracking and validation:

```bash
metabintools merge set1.bins set2.bins set3.bins -o merged.bins
```

### trim

Remove unused contigs from a BINS file:

```bash
metabintools trim input.bins -o trimmed.bins
```

### rename

Rename bins in a BINS file with template support. Field options can be listed with `--list-fields`.

```bash
metabintools rename input.bins -n "bin_{tax_phylum}" -o output.bins
# bin1, bin2 > bin_Pseudomonadota_1, bin_Pseudomonadota_2
```

### summarise

Generate summary reports:

- **`metabintools summarise bins`** - Export bin summary to TSV
- **`metabintools summarise groups`** - Export an aggregated summary of bin groups, showing counts of bins at each MiMAG level, to TSV
- **`metabintools summarise contigs`** - Export contig summary to TSV

## File Format

A `.bins` file is a zstd-compressed (or uncompressed) JSON document containing:

```json
{
  "contigs": {
    "contig_id": {
      "id": "contig_id",
      "sequence": "ACGTACGT...",
      "sequence_length": 1234,
      "annotations": [...],
      "coverage": 15.5,
      "topology": "circular"
    }
  },
  "bins": [
    {
      "id": "bin.1",
      "group": "metabat",
      "contigs": ["contig_1", "contig_2"],
      "statistics": {
        "completeness": 0.95,
        "contamination": 0.02,
        "length": 2500000
      },
      "taxonomy": {
        "classification": "k__Bacteria;p__Proteobacteria;..."
      }
    }
  ]
}
```

## Examples

### Workflow: Filter and Export High-Quality Bins

```bash
# Start with assembly
metabintools import asm metagenome.fasta -o project.bins

# Add binning results
metabintools import binset project.bins bins/ --group "metabat" -o project.bins

# Add quality scores
metabintools import quality project.bins checkm_results.tsv --tool checkm -o project.bins

# Add taxonomy
metabintools import taxonomy project.bins gtdbtk.tsv --tool gtdbtk -o project.bins

# Filter to high-quality bins
metabintools view project.bins 'completeness >= 0.9 and contamination <= 0.05' \
  -o high_quality.bins

# Export to FASTA
metabintools export fasta high_quality.bins -o bins_fasta/
```

## License

MIT © 2026 Genome Research Ltd
