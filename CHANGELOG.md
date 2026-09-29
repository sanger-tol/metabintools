# metabintools: changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [[0.3.1](https://github.com/sanger-tol/metabintools/releases/tag/0.3.1)] - [2026-09-29]

- Fixed a problem where bins with a '.' could not be matched against data from external files

## [[0.3.0](https://github.com/sanger-tol/metabintools/releases/tag/0.3.0)] - [2026-09-29]

- Coverage now requires a regular expression to be provided to identify the required column from the TSV.

## [[0.2.5](https://github.com/sanger-tol/metabintools/releases/tag/0.2.5)] - [2026-09-28]

- All import commands now apply the data file to be imported with an option rather than an argument.
- File format is now always referred to as a BINS file.

## [[0.2.4](https://github.com/sanger-tol/metabintools/releases/tag/0.2.4)] - [2026-09-25]

- Fix argument mismatch

## [[0.2.3](https://github.com/sanger-tol/metabintools/releases/tag/0.2.3)] - [2026-09-25]

- Fix erroneous import

## [[0.2.2](https://github.com/sanger-tol/metabintools/releases/tag/0.2.2)] - [2026-09-25]

- Change build system to hatchling for Conda build

## [[0.2.1](https://github.com/sanger-tol/metabintools/releases/tag/0.2.1)] - [2026-09-24]

- Read the isotype field of a tRNA annotation to get the gene, enabling compatibility with tRNAScan-SE

## [[0.2.0](https://github.com/sanger-tol/metabintools/releases/tag/0.2.0)] - [2026-09-24]

- Rename package to metabintools to avoid PyPi conflicts.
- Add `metabintools summarise groups` command which prints an aggregated TSV summary of MiMAG counts for each bin group.
- If importing NCBI taxonomy, now tries to find and set a submittable taxonomic name and taxID by querying ENA.

## [[0.1.0](https://github.com/sanger-tol/metabintools/releases/tag/v0.1.0)] - [2026-09-23]

Base release of metabintools.
