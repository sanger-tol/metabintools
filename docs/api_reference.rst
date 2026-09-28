API Reference
=============

This page provides detailed documentation of the metabintools Python API for programmatic use.

Core Data Structures
====================

BinSet
------

.. autoclass:: metabintools.dataclasses.binset.BinSet
   :members:
   :undoc-members:
   :show-inheritance:

The main class representing a collection of contigs and bins.

Bin
---

.. autoclass:: metabintools.dataclasses.bin.Bin
   :members:
   :undoc-members:
   :show-inheritance:

Represents a single metagenomic bin with statistics and taxonomy.

BinStatistics
-------------

.. autoclass:: metabintools.dataclasses.bin_statistics.BinStatistics
   :members:
   :undoc-members:
   :show-inheritance:

Statistics computed for a bin.

BinTaxonomy
-----------

.. autoclass:: metabintools.dataclasses.bin_taxonomy.BinTaxonomy
   :members:
   :undoc-members:
   :show-inheritance:

Taxonomy information for a bin.

Contig
------

.. autoclass:: metabintools.dataclasses.contig.Contig
   :members:
   :undoc-members:
   :show-inheritance:

Represents a single contig sequence.

Annotation
----------

.. autoclass:: metabintools.dataclasses.annotation.Annotation
   :members:
   :undoc-members:
   :show-inheritance:

GFF-format annotation for a contig.

Import Functions
================

Assembly Parsing
----------------

.. automodule:: metabintools.import_data.assembly
   :members:
   :undoc-members:

Bin Parsing
-----------

.. automodule:: metabintools.import_data.binset
   :members:
   :undoc-members:

Annotation Processing
---------------------

.. automodule:: metabintools.import_data.annotation
   :members:
   :undoc-members:

Coverage Data
-------------

.. automodule:: metabintools.import_data.coverage
   :members:
   :undoc-members:

Quality Scores
--------------

.. automodule:: metabintools.import_data.quality
   :members:
   :undoc-members:

Taxonomy
--------

.. automodule:: metabintools.import_data.taxonomy
   :members:
   :undoc-members:

Export Functions
================

.. autoclass:: metabintools.export.binset_exporter.BinSetExporter
   :members:
   :undoc-members:

Query and Filtering
===================

.. automodule:: metabintools.query.query_parser
   :members:
   :undoc-members:

Operations
==========

Merging
-------

.. automodule:: metabintools.operations.merge
   :members:
   :undoc-members:

Renaming
--------

.. automodule:: metabintools.operations.rename
   :members:
   :undoc-members:

Enumerations
============

.. automodule:: metabintools.enums
   :members:
   :undoc-members:

Utilities
=========

Bin Statistics Calculation
---------------------------

.. automodule:: metabintools.binstatistics
   :members:
   :undoc-members:

File Utilities
--------------

.. automodule:: metabintools.bin_utils
   :members:
   :undoc-members:

Example Usage
=============

Programmatic Workflow
---------------------

Here's an example of using metabintools as a Python library:

.. code-block:: python

   from pathlib import Path
   from metabintools.dataclasses.binset import BinSet
   from metabintools.import_data.assembly import parse_assembly_fasta
   from metabintools.import_data.binset import parse_fasta_bins
   from metabintools.enums import Assembler

   # Load assembly
   assembly_path = Path("metagenome.fasta")
   contigs = parse_assembly_fasta(assembly_path, Assembler.metamdbg)

   # Load bins
   bin_paths = [Path("bins/bin1.fa"), Path("bins/bin2.fa")]
   bins = parse_fasta_bins(bin_paths, group="metabat", asm_contigs=contigs)

   # Create BinSet
   binset = BinSet(contigs=contigs, bins=bins)

   # Filter bins
   filtered = binset.filter_bins("completeness >= 0.9")

   # Export to FASTA
   from metabintools.export.binset_exporter import BinSetExporter
   exporter = BinSetExporter(filtered)
   exporter.export_fasta(Path("output/"), compress=False)

Reading and Writing BINS files
-----------------------------

.. code-block:: python

   from metabintools.dataclasses.binset import BinSet
   from metabintools.export.binset_exporter import BinSetExporter

   # Read a BINS file
   with open("project.bins", "rb") as f:
       binset = BinSet.read_binsfile(f)

   # Perform operations
   filtered = binset.filter_bins("tax_phylum == 'Bacteroidetes'")

   # Write back (optionally compressed)
   with open("output.bins.zstd", "wb") as f:
       exporter = BinSetExporter(filtered)
       exporter.write_binsfile(f, compress=True)
