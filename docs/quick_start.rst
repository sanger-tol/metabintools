Quick Start
===========

This guide walks you through the basic workflow of using metabintools.

Basic Workflow
--------------

**Step 1: Initialize from assembly**

Start with your metagenomic assembly in FASTA format:

.. code-block:: bash

   metabintools import asm metagenome.fasta -o project.bins

This creates a new BINS file containing all contigs from your assembly.

**Step 2: Add bins from your binner**

Import results from your binning tool (metaBAT, VAMB, etc.):

.. code-block:: bash

   metabintools import binset project.bins bins/ --group "metabat" -o project.bins

You can add bins from multiple binners by running the command again with a different group name:

.. code-block:: bash

   metabintools import binset project.bins vamb_bins/ --group "vamb" -o project.bins

**Step 3: Add quality scores**

Import quality assessment results (CheckM, CheckM2, BUSCO):

.. code-block:: bash

   metabintools import quality project.bins checkm_results.tsv --tool checkm -o project.bins

**Step 4: Add taxonomy**

Import taxonomic classifications (GTDB-Tk, manual):

.. code-block:: bash

   metabintools import taxonomy project.bins gtdbtk.tsv --tool gtdbtk -o project.bins

**Step 5: Add annotations**

Add functional annotations (GFF format):

.. code-block:: bash

   metabintools import annotation project.bins annotations.gff -o project.bins

**Step 6: Filter high-quality bins**

Filter bins based on quality criteria:

.. code-block:: bash

   metabintools view project.bins 'completeness >= 0.9 and contamination <= 0.05' -o hq.bins

Or use MiMAG quality levels if you have the required data:

.. code-block:: bash

   metabintools view project.bins 'mimag == "high"' -o hq.bins

**Step 7: Export results**

Export your filtered bins to FASTA files:

.. code-block:: bash

   metabintools export fasta hq.bins -o output_directory/

Export annotations:

.. code-block:: bash

   metabintools export gff hq.bins -o output_directory/

Export in DAS_Tool format for merging:

.. code-block:: bash

   metabintools export contig2bin hq.bins -o contig2bin.tsv

Composable Workflows
--------------------

One of the key features of metabintools is composability via Unix pipes. This allows you to chain operations efficiently.

**Filter and export in one pipeline:**

.. code-block:: bash

   metabintools view project.bins 'group == "metabat" and completeness >= 0.8' -z | \
     metabintools export fasta -o filtered_bins/

**Merge multiple binsets and filter:**

.. code-block:: bash

   metabintools merge set1.bins.zstd set2.bins.zstd -z | \
     metabintools view - 'contamination <= 0.1' -o merged_hq.bins.zstd

**Extract high-quality archaeal bins:**

.. code-block:: bash

   metabintools view project.bins 'tax_phylum == "Archaea" and completeness >= 0.85' -o archaea_hq.bins

Common Filter Expressions
--------------------------

Filter by quality:

.. code-block:: bash

   metabintools view input.bins 'completeness >= 0.9' -o output.bins

Filter by contamination:

.. code-block:: bash

   metabintools view input.bins 'contamination <= 0.05' -o output.bins

Filter by size:

.. code-block:: bash

   metabintools view input.bins 'length > 1000000' -o output.bins

Filter by taxonomy:

.. code-block:: bash

   metabintools view input.bins 'tax_phylum == "Bacteroidetes"' -o output.bins

Combine multiple conditions:

.. code-block:: bash

   metabintools view input.bins 'completeness >= 0.9 and contamination <= 0.05 and tax_kingdom == "Bacteria"' -o output.bins

See :doc:`cli_reference` for more details on available filter fields and commands.
