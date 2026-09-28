File Format
===========

The ``.bins`` File Format
--------------------------

A ``.bins`` file is a JSON document that contains all data related to a set of metagenomic bins. It can optionally be compressed using zstd compression (as ``.bins.zstd``).

Structure
~~~~~~~~~

The file contains two main sections:

.. code-block:: text

   {
     "contigs": {
       "contig_id": { ... },
       ...
     },
     "bins": [
       { ... },
       ...
     ]
   }

Contigs
~~~~~~~

Each contig entry contains:

.. code-block:: text

   {
     "id": "contig1",
     "header": "contig1 circular=yes",
     "sequence": "ACGTACGTACGT...",
     "sequence_length": 1234,
     "topology": "circular",
     "coverage": 15.5,
     "annotations": [...],
     "gc": 0.48,
     "trnas": ["tRNA-Ala", "tRNA-Gly", ...],
     "has_5s": true,
     "has_16s": true,
     "has_23s": true
   }

Fields:

- **id**: Unique contig identifier
- **header**: Full header from original FASTA file
- **sequence**: DNA sequence (ACGTN)
- **sequence_length**: Length of the sequence in bp
- **topology**: "linear" or "circular"
- **coverage**: Average depth of coverage (optional)
- **annotations**: List of GFF annotations (optional)
- **gc**: Computed GC content (0.0-1.0)
- **trnas**: List of tRNA products found
- **has_5s, has_16s, has_23s**: Boolean flags for rRNA presence

Bins
~~~~

Each bin entry contains:

.. code-block:: text

   {
     "id": "bin.1",
     "import_name": "bin1.fa",
     "group": "metabat",
     "contigs": ["contig_1", "contig_2", ...],
     "statistics": {
       "length": 2500000,
       "longest": 150000,
       "n_contigs": 15,
       "n_circular": 1,
       "n50": 95000,
       "coverage": 15.3,
       "completeness": 0.95,
       "contamination": 0.02,
       "quality_tool": "checkm2",
       "n_unique_trnas": 18,
       "has_5s": true,
       "has_16s": true,
       "has_23s": true,
       "mimag": "high"
     },
     "taxonomy": {
       "source": "gtdbtk",
       "classification": "d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;...",
       "tax_kingdom": "Bacteria",
       "tax_phylum": "Proteobacteria",
       "tax_class": "Gammaproteobacteria",
       "tax_order": "Pseudomonadales",
       "tax_family": "Pseudomonadaceae",
       "tax_genus": "Pseudomonas",
       "tax_species": "aeruginosa",
       "taxon_name": "Pseudomonas aeruginosa"
     }
   }

Bin Statistics
~~~~~~~~~~~~~~

The statistics section contains computed metrics:

- **length**: Total size of the bin in bp
- **longest**: Size of the longest contig in bp
- **n_contigs**: Number of contigs in the bin
- **n_circular**: Number of circular contigs
- **n50**: N50 metric of the bin
- **coverage**: Average coverage across all contigs
- **completeness**: Completeness estimate (0.0-1.0)
- **contamination**: Contamination estimate (0.0-1.0)
- **quality_tool**: Tool used to compute completeness/contamination
- **n_unique_trnas**: Number of unique tRNA types
- **has_5s, has_16s, has_23s**: rRNA presence flags
- **mimag**: MiMAG quality level ("high", "medium", "low")

Taxonomy
~~~~~~~~

The taxonomy section follows GTDB format by default:

.. code-block:: text

   d__Domain;p__Phylum;c__Class;o__Order;f__Family;g__Genus;s__Species

The individual rank fields are:

- **tax_kingdom**: Domain (Bacteria/Archaea)
- **tax_phylum**: Phylum
- **tax_class**: Class
- **tax_order**: Order
- **tax_family**: Family
- **tax_genus**: Genus
- **tax_species**: Species
- **taxon_name**: Computed best-guess species name

Compression
-----------

Files ending in ``.bins.zstd`` are compressed using Zstandard. Most metabintools commands automatically detect and handle compression, so you can use compressed and uncompressed files interchangeably.

To compress an existing BINS file:

.. code-block:: bash

   metabintools view input.bins -z -o input.bins.zstd
