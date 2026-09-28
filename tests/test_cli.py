"""Tests for CLI commands using Click's test runner."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from metabintools.cli.cli import cli

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def test_binset_file():
    """Path to test binset file."""
    return TEST_DATA_DIR / "test_binset.bins"


@pytest.fixture
def test_binset_file_zstd():
    """Path to test binset file (compressed)."""
    return TEST_DATA_DIR / "test_binset.bins.zstd"


@pytest.fixture
def assembly_file():
    """Path to test assembly file."""
    return TEST_DATA_DIR / "asm.fasta"


@pytest.fixture
def bin_files():
    """Paths to test bin files."""
    bins_dir = TEST_DATA_DIR / "bins"
    return [str(bins_dir / "bin1.fasta"), str(bins_dir / "bin2.fasta")]


@pytest.fixture
def quality_file():
    """Path to test quality file."""
    return TEST_DATA_DIR / "checkm2.tsv"


@pytest.fixture
def checkm_quality_file():
    """Path to CheckM v1 quality file."""
    return TEST_DATA_DIR / "checkm.tsv"


@pytest.fixture
def busco_quality_file():
    """Path to BUSCO quality file."""
    return TEST_DATA_DIR / "busco.tsv"


@pytest.fixture
def taxonomy_file():
    """Path to test taxonomy file."""
    return TEST_DATA_DIR / "gtdbtk.tsv"


@pytest.fixture
def gff_file():
    """Path to test GFF file."""
    return TEST_DATA_DIR / "asm.gff"


class TestImportCommands:
    """Tests for metabintools import commands."""

    def test_import_asm_basic(self, cli_runner, assembly_file, tmp_path):
        """Test importing an assembly file."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            ["import", "asm", str(assembly_file), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_import_asm_with_compression(self, cli_runner, assembly_file, tmp_path):
        """Test importing assembly with compression."""
        output_file = tmp_path / "output.bins.zstd"
        result = cli_runner.invoke(
            cli,
            ["import", "asm", str(assembly_file), "-z", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        # Check zstd magic number
        with open(output_file, "rb") as f:
            data = f.read()
        assert data[:4] == b"\x28\xb5\x2f\xfd"

    def test_import_asm_with_assembler(self, cli_runner, assembly_file, tmp_path):
        """Test importing with assembler detection."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "asm",
                str(assembly_file),
                "--assembler",
                "metamdbg",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_import_asm_stdout(self, cli_runner, assembly_file):
        """Test importing to stdout."""
        result = cli_runner.invoke(cli, ["import", "asm", str(assembly_file)])
        assert result.exit_code == 0
        # Output should be JSON (starts with {)
        assert result.output.startswith("{") or b"{" in result.output_bytes

    def test_import_binset(self, cli_runner, test_binset_file, bin_files, tmp_path):
        """Test importing bins into a binset."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "binset",
                str(test_binset_file),
                *bin_files,
                "--group",
                "mygroup",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_import_quality(self, cli_runner, test_binset_file, quality_file, tmp_path):
        """Test importing quality scores."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "quality",
                str(test_binset_file),
                "--tool",
                "checkm2",
                "--quality",
                str(quality_file),
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_import_taxonomy(
        self, cli_runner, test_binset_file, taxonomy_file, tmp_path
    ):
        """Test importing taxonomy."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "taxonomy",
                str(test_binset_file),
                "--tool",
                "gtdbtk",
                "--taxonomy",
                str(taxonomy_file),
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_import_annotation(self, cli_runner, test_binset_file, gff_file, tmp_path):
        """Test importing annotations."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "annotation",
                "--gff",
                str(gff_file),
                str(test_binset_file),
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_import_quality_checkm(
        self, cli_runner, test_binset_file, checkm_quality_file, tmp_path
    ):
        """Test importing CheckM v1 quality scores."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "quality",
                str(test_binset_file),
                "--tool",
                "checkm",
                "--quality",
                str(checkm_quality_file),
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_import_quality_busco(
        self, cli_runner, test_binset_file, busco_quality_file, tmp_path
    ):
        """Test importing BUSCO quality scores."""
        output_file = tmp_path / "output.bins"
        result = cli_runner.invoke(
            cli,
            [
                "import",
                "quality",
                str(test_binset_file),
                "--tool",
                "busco",
                "--quality",
                str(busco_quality_file),
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestFilterCommand:
    """Tests for metabintools filter command."""

    def test_filter_basic(self, cli_runner, test_binset_file, tmp_path):
        """Test basic filtering."""
        output_file = tmp_path / "filtered.bins"
        result = cli_runner.invoke(
            cli,
            [
                "view",
                str(test_binset_file),
                'group == "metabat"',
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_filter_by_completeness(self, cli_runner, test_binset_file, tmp_path):
        """Test filtering by completeness."""
        output_file = tmp_path / "filtered.bins"
        result = cli_runner.invoke(
            cli,
            [
                "view",
                str(test_binset_file),
                "completeness > 0.9",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_filter_with_compression(self, cli_runner, test_binset_file, tmp_path):
        """Test filtering with output compression."""
        output_file = tmp_path / "filtered.bins.zstd"
        result = cli_runner.invoke(
            cli,
            [
                "view",
                str(test_binset_file),
                "length > 0",
                "-z",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        with open(output_file, "rb") as f:
            data = f.read()
        assert data[:4] == b"\x28\xb5\x2f\xfd"

    def test_filter_compressed_input(self, cli_runner, test_binset_file_zstd, tmp_path):
        """Test filtering compressed input."""
        output_file = tmp_path / "filtered.bins"
        result = cli_runner.invoke(
            cli,
            [
                "view",
                str(test_binset_file_zstd),
                "n_contigs == 1",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_filter_list_fields(self, cli_runner, test_binset_file):
        """Test listing available filter fields."""
        result = cli_runner.invoke(
            cli, ["view", str(test_binset_file), "--list-fields"]
        )
        assert result.exit_code == 0
        assert "id" in result.output
        assert "group" in result.output
        assert "completeness" in result.output

    def test_filter_invalid_query(self, cli_runner, test_binset_file):
        """Test filter with invalid query."""
        result = cli_runner.invoke(
            cli,
            ["view", str(test_binset_file), "invalid_field == 'value'"],
        )
        assert result.exit_code != 0

    def test_filter_to_stdout(self, cli_runner, test_binset_file):
        """Test filtering to stdout."""
        result = cli_runner.invoke(
            cli,
            ["view", str(test_binset_file), "length > 0"],
        )
        assert result.exit_code == 0


class TestMergeCommand:
    """Tests for metabintools merge command."""

    def test_merge_basic(self, cli_runner, test_binset_file, tmp_path):
        """Test merging binsets."""
        output_file = tmp_path / "merged.bins"
        result = cli_runner.invoke(
            cli,
            [
                "merge",
                str(test_binset_file),
                str(test_binset_file),
                "-o",
                str(output_file),
            ],
        )
        # Should fail because bins would have duplicate IDs
        assert result.exit_code != 0

    def test_merge_with_compression(self, cli_runner, test_binset_file, tmp_path):
        """Test merge with compression."""
        output_file = tmp_path / "merged.bins.zstd"
        result = cli_runner.invoke(
            cli,
            [
                "merge",
                str(test_binset_file),
                str(test_binset_file),
                "-z",
                "-o",
                str(output_file),
            ],
        )
        # Should fail due to duplicate bins
        assert result.exit_code != 0

    def test_merge_to_stdout(self, cli_runner, test_binset_file):
        """Test merge to stdout."""
        result = cli_runner.invoke(
            cli,
            ["merge", str(test_binset_file), str(test_binset_file)],
        )
        # Should fail
        assert result.exit_code != 0


class TestTrimCommand:
    """Tests for metabintools trim command."""

    def test_trim_basic(self, cli_runner, test_binset_file, tmp_path):
        """Test trimming unused contigs."""
        output_file = tmp_path / "trimmed.bins"
        result = cli_runner.invoke(
            cli,
            ["trim", str(test_binset_file), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_trim_with_compression(self, cli_runner, test_binset_file, tmp_path):
        """Test trim with compression."""
        output_file = tmp_path / "trimmed.bins.zstd"
        result = cli_runner.invoke(
            cli,
            ["trim", str(test_binset_file), "-z", "-o", str(output_file)],
        )
        assert result.exit_code == 0
        with open(output_file, "rb") as f:
            data = f.read()
        assert data[:4] == b"\x28\xb5\x2f\xfd"

    def test_trim_compressed_input(self, cli_runner, test_binset_file_zstd, tmp_path):
        """Test trim on compressed input."""
        output_file = tmp_path / "trimmed.bins"
        result = cli_runner.invoke(
            cli,
            ["trim", str(test_binset_file_zstd), "-o", str(output_file)],
        )
        assert result.exit_code == 0

    def test_trim_to_stdout(self, cli_runner, test_binset_file):
        """Test trim to stdout."""
        result = cli_runner.invoke(cli, ["trim", str(test_binset_file)])
        assert result.exit_code == 0


class TestRenameCommand:
    """Tests for metabintools rename command."""

    def test_rename_basic(self, cli_runner, test_binset_file, tmp_path):
        """Test renaming bins."""
        output_file = tmp_path / "renamed.bins"
        result = cli_runner.invoke(
            cli,
            [
                "rename",
                str(test_binset_file),
                "-n",
                "bin_{group}",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_rename_with_taxonomy(self, cli_runner, test_binset_file, tmp_path):
        """Test renaming with taxonomy field."""
        output_file = tmp_path / "renamed.bins"
        result = cli_runner.invoke(
            cli,
            [
                "rename",
                str(test_binset_file),
                "-n",
                "{tax_phylum}_{id}",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_rename_with_compression(self, cli_runner, test_binset_file, tmp_path):
        """Test rename with compression."""
        output_file = tmp_path / "renamed.bins.zstd"
        result = cli_runner.invoke(
            cli,
            [
                "rename",
                str(test_binset_file),
                "-n",
                "hq_{group}",
                "-z",
                "-o",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        with open(output_file, "rb") as f:
            data = f.read()
        assert data[:4] == b"\x28\xb5\x2f\xfd"

    def test_rename_to_stdout(self, cli_runner, test_binset_file):
        """Test rename to stdout."""
        result = cli_runner.invoke(
            cli, ["rename", str(test_binset_file), "-n", "renamed_{id}"]
        )
        assert result.exit_code == 0


class TestExportCommands:
    """Tests for metabintools export commands."""

    def test_export_fasta(self, cli_runner, test_binset_file, tmp_path):
        """Test exporting bins to FASTA."""
        output_dir = tmp_path / "fasta"
        output_dir.mkdir()
        result = cli_runner.invoke(
            cli,
            ["export", "fasta", str(test_binset_file), "-o", str(output_dir)],
        )
        assert result.exit_code == 0
        # Check that FASTA files were created
        fasta_files = list(output_dir.glob("*.fa*"))
        assert len(fasta_files) > 0

    def test_export_fasta_compressed(self, cli_runner, test_binset_file, tmp_path):
        """Test exporting bins with compression flag."""
        output_dir = tmp_path / "fasta"
        output_dir.mkdir()
        result = cli_runner.invoke(
            cli,
            [
                "export",
                "fasta",
                str(test_binset_file),
                "-z",
                "-o",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        # Check that FASTA files were created (compressed or not)
        fasta_files = list(output_dir.glob("*.fa*"))
        assert len(fasta_files) > 0

    def test_export_gff(self, cli_runner, test_binset_file, tmp_path):
        """Test exporting bins to GFF."""
        output_dir = tmp_path / "gff"
        output_dir.mkdir()
        result = cli_runner.invoke(
            cli,
            ["export", "gff", str(test_binset_file), "-o", str(output_dir)],
        )
        # Should exit with code 0 even if no annotations
        assert result.exit_code == 0

    def test_export_contig2bin(self, cli_runner, test_binset_file, tmp_path):
        """Test exporting contig-to-bin mapping."""
        output_file = tmp_path / "contig2bin.tsv"
        result = cli_runner.invoke(
            cli,
            ["export", "contig2bin", str(test_binset_file), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        # Check content
        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) > 0


class TestSummariseCommands:
    """Tests for metabintools summarise commands."""

    def test_summarise_bins(self, cli_runner, test_binset_file, tmp_path):
        """Test summarizing bins."""
        output_file = tmp_path / "bins_summary.tsv"
        result = cli_runner.invoke(
            cli,
            ["summarise", "bins", str(test_binset_file), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        # Check TSV format
        with open(output_file) as f:
            lines = f.readlines()
        assert len(lines) > 1  # Header + at least one bin

    def test_summarise_bins_stdout(self, cli_runner, test_binset_file, tmp_path):
        """Test summarizing bins to file (no stdout support)."""
        output_file = tmp_path / "bins_summary.tsv"
        result = cli_runner.invoke(
            cli, ["summarise", "bins", str(test_binset_file), "-o", str(output_file)]
        )
        assert result.exit_code == 0

    def test_summarise_contigs(self, cli_runner, test_binset_file, tmp_path):
        """Test summarizing contigs."""
        output_file = tmp_path / "contigs_summary.tsv"
        result = cli_runner.invoke(
            cli,
            ["summarise", "contigs", str(test_binset_file), "-o", str(output_file)],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_summarise_contigs_stdout(self, cli_runner, test_binset_file, tmp_path):
        """Test summarizing contigs to file (no stdout support)."""
        output_file = tmp_path / "contigs_summary.tsv"
        result = cli_runner.invoke(
            cli, ["summarise", "contigs", str(test_binset_file), "-o", str(output_file)]
        )
        assert result.exit_code == 0


class TestPipingWorkflows:
    """Tests for composable workflows using pipes."""

    def test_filter_then_export(self, cli_runner, test_binset_file, tmp_path):
        """Test filtering then exporting workflow."""
        filter_output = tmp_path / "filtered.bins"
        fasta_dir = tmp_path / "fasta"
        fasta_dir.mkdir()

        # First filter
        result1 = cli_runner.invoke(
            cli,
            [
                "view",
                str(test_binset_file),
                "completeness > 0.9",
                "-o",
                str(filter_output),
            ],
        )
        assert result1.exit_code == 0

        # Then export
        result2 = cli_runner.invoke(
            cli,
            ["export", "fasta", str(filter_output), "-o", str(fasta_dir)],
        )
        assert result2.exit_code == 0

    def test_trim_then_summarise(self, cli_runner, test_binset_file, tmp_path):
        """Test trim then summarise workflow."""
        trim_output = tmp_path / "trimmed.bins"
        summary_output = tmp_path / "summary.tsv"

        # First trim
        result1 = cli_runner.invoke(
            cli,
            ["trim", str(test_binset_file), "-o", str(trim_output)],
        )
        assert result1.exit_code == 0

        # Then summarise
        result2 = cli_runner.invoke(
            cli,
            ["summarise", "bins", str(trim_output), "-o", str(summary_output)],
        )
        assert result2.exit_code == 0
        assert summary_output.exists()

    def test_filter_rename_export(self, cli_runner, test_binset_file, tmp_path):
        """Test filter, rename, then export workflow."""
        filter_output = tmp_path / "filtered.bins"
        rename_output = tmp_path / "renamed.bins"
        fasta_dir = tmp_path / "fasta"
        fasta_dir.mkdir()

        # Filter
        result1 = cli_runner.invoke(
            cli,
            ["view", str(test_binset_file), "length > 0", "-o", str(filter_output)],
        )
        assert result1.exit_code == 0

        # Rename
        result2 = cli_runner.invoke(
            cli,
            [
                "rename",
                str(filter_output),
                "-n",
                "hq_{group}",
                "-o",
                str(rename_output),
            ],
        )
        assert result2.exit_code == 0

        # Export
        result3 = cli_runner.invoke(
            cli,
            ["export", "fasta", str(rename_output), "-o", str(fasta_dir)],
        )
        assert result3.exit_code == 0
        assert len(list(fasta_dir.glob("*.fa*"))) > 0
