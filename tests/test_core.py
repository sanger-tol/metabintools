"""Core functionality tests for metabintools.

Tests assembly parsing, bin loading, and the core BinSet operations.
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from metabintools.dataclasses.binset import BinSet
from metabintools.dataclasses.contig import Contig
from metabintools.enums import Assembler
from metabintools.export.binset_exporter import BinSetExporter
from metabintools.import_data.annotation import ContigAnnotator
from metabintools.import_data.assembly import parse_assembly_fasta
from metabintools.import_data.binset import parse_fasta_bins

TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def assembly_file():
    """Path to the assembly FASTA file."""
    return TEST_DATA_DIR / "asm.fasta"


@pytest.fixture
def assembly_contigs(assembly_file):
    """Parse the assembly FASTA file."""
    return parse_assembly_fasta(assembly_file, assembler=Assembler.metamdbg)


@pytest.fixture
def bin_files():
    """Paths to valid bin FASTA files."""
    bins_dir = TEST_DATA_DIR / "bins"
    return [bins_dir / "bin1.fasta", bins_dir / "bin2.fasta"]


@pytest.fixture
def bin_files_binsplit():
    """Paths to binsplit bin FASTA files."""
    bins_dir = TEST_DATA_DIR / "bins_binsplit"
    return [bins_dir / "bin1.fasta", bins_dir / "bin2.fasta"]


@pytest.fixture
def gff_file():
    """Path to the GFF annotations file."""
    return TEST_DATA_DIR / "asm.gff"


class TestAssemblyParsing:
    """Tests for parsing assembly FASTA files."""

    def test_parse_assembly_returns_contigs(self, assembly_file):
        """Test that parse_assembly_fasta returns a dict of Contig objects."""
        contigs = parse_assembly_fasta(assembly_file, assembler=Assembler.metamdbg)
        assert isinstance(contigs, dict)
        assert len(contigs) == 3
        assert all(isinstance(c, Contig) for c in contigs.values())

    def test_contig_attributes(self, assembly_contigs):
        """Test that contigs have expected attributes."""
        contig = assembly_contigs["contig1"]
        assert contig.id == "contig1"
        assert len(contig.sequence) == contig.sequence_length
        assert contig.sequence.isupper()
        assert hasattr(contig, "topology")

    def test_circular_topology_detected(self, assembly_contigs):
        """Test that circular topology is detected from metamdbg headers."""
        assert assembly_contigs["contig1"].topology == "circular"
        assert assembly_contigs["contig2"].topology == "linear"
        assert assembly_contigs["contig3"].topology == "linear"

    def test_duplicate_sequence_id_raises_error(self, tmp_path):
        """Test that duplicate sequence IDs raise ValueError."""
        fasta_file = tmp_path / "dup.fasta"
        fasta_file.write_text(">seq1\nACGT\n>seq1\nTGCA\n")
        with pytest.raises(ValueError, match="Duplicate sequence id"):
            parse_assembly_fasta(fasta_file, assembler=None)


class TestBinParsing:
    """Tests for parsing bin FASTA files."""

    def test_parse_bins_returns_bins(self, assembly_contigs, bin_files):
        """Test that parse_fasta_bins returns a list of Bin objects."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        assert isinstance(bins, list)
        assert len(bins) == 2

    def test_bin_attributes(self, assembly_contigs, bin_files):
        """Test that bins have expected attributes."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        bin_obj = bins[0]
        assert bin_obj.id == "bin1"
        assert bin_obj.group == "test"
        assert isinstance(bin_obj.contigs, list)
        assert bin_obj.statistics is not None

    def test_bin_default_id_is_basename(self, assembly_contigs, bin_files):
        """Test that default bin ID is the file basename."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        assert bins[0].id == "bin1"
        assert bins[1].id == "bin2"

    def test_parse_bins_with_binsplit_separator(
        self, assembly_contigs, bin_files_binsplit
    ):
        """Test parse_bins with binsplit_separator to extract contig IDs."""
        bins = parse_fasta_bins(
            bin_files_binsplit,
            group="test",
            asm_contigs=assembly_contigs,
            binsplit_separator=":",
        )
        assert bins[0].contigs == ["contig1"]
        assert bins[1].contigs == ["contig2"]

    def test_parse_bins_without_binsplit_separator(self, bin_files_binsplit, tmp_path):
        """Test parse_bins without binsplit_separator keeps full IDs."""
        # Create a simple assembly with the binsplit-formatted contig IDs
        fasta_file = tmp_path / "binsplit_asm.fasta"
        fasta_file.write_text(">s1:contig1\nACGTACGTACGT\n>s2:contig2\nTGCATGCATGCA\n")
        asm_contigs = parse_assembly_fasta(fasta_file, assembler=None)
        bins = parse_fasta_bins(
            bin_files_binsplit, group="test", asm_contigs=asm_contigs
        )
        assert bins[0].contigs == ["s1:contig1"]
        assert bins[1].contigs == ["s2:contig2"]


class TestAnnotationParsing:
    """Tests for parsing and applying annotations."""

    def test_read_gff_returns_dict(self, gff_file):
        """Test that read_gff returns a dict keyed by seqname."""
        annotator = ContigAnnotator()
        result = annotator.read_gff(gff_file)
        assert isinstance(result, dict)
        assert "contig1" in result
        assert "contig2" in result

    def test_gff_annotations_parsed(self, gff_file):
        """Test that annotations are parsed with correct counts."""
        annotator = ContigAnnotator()
        result = annotator.read_gff(gff_file)
        assert len(result["contig1"]) == 21
        assert len(result["contig2"]) == 4

    def test_annotation_fields_correct(self, gff_file):
        """Test that annotation fields are parsed correctly."""
        annotator = ContigAnnotator()
        result = annotator.read_gff(gff_file)
        first = result["contig1"][0]
        assert first.seqname == "contig1"
        assert first.feature == "tRNA"
        assert first.start == 1
        assert first.end == 3

    def test_annotate_contigs(self, assembly_contigs, gff_file):
        """Test that annotate_contigs adds annotations to matching contigs."""
        annotator = ContigAnnotator()
        result = annotator.annotate_contigs(assembly_contigs, gff_file)
        assert len(result) == 3
        assert result["contig1"].annotations is not None
        assert len(result["contig1"].annotations) == 21
        assert result["contig2"].annotations is not None
        assert len(result["contig2"].annotations) == 4


class TestBinSet:
    """Tests for the BinSet dataclass."""

    def test_create_binset_with_valid_bins(self, assembly_contigs, bin_files):
        """Test creating a BinSet with valid bins."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        assert len(binset.contigs) == 3
        assert binset.bins is not None
        assert len(binset.bins) == 2

    def test_binset_validation_rejects_missing_contigs(
        self, assembly_contigs, tmp_path
    ):
        """Test that BinSet validation rejects bins with missing contigs."""
        from metabintools.dataclasses.bin import Bin

        invalid_bin = Bin(
            id="invalid",
            import_name="test.fasta",
            group="test",
            contigs=["nonexistent_contig"],
        )

        with pytest.raises(ValidationError):
            BinSet(contigs=assembly_contigs, bins=[invalid_bin])

    def test_binset_bin_contig_ids(self, assembly_contigs, bin_files):
        """Test that bin_contig_ids returns all contigs referenced by bins."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        bin_contig_ids = binset.bin_contig_ids
        assert "contig1" in bin_contig_ids
        assert "contig2" in bin_contig_ids

    def test_binset_remove_unreferenced_contigs(self, assembly_contigs, bin_files):
        """Test that remove_unreferenced_contigs removes unused contigs."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        # contig3 is not in any bin, so it should be removed
        trimmed = binset.remove_unreferenced_contigs()
        assert len(trimmed.contigs) == 2
        assert "contig3" not in trimmed.contigs

    def test_binset_write_uncompressed(self, assembly_contigs, bin_files, tmp_path):
        """Test writing uncompressed BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        outfile = tmp_path / "test.bins"

        with open(outfile, "wb") as f:
            BinSetExporter(binset).write_binsfile(f, compress=False)

        assert outfile.exists()
        with open(outfile, "rb") as f:
            data = f.read()
        # Check it's not zstd compressed (zstd magic number)
        assert data[:4] != b"\x28\xb5\x2f\xfd"

    def test_binset_write_compressed(self, assembly_contigs, bin_files, tmp_path):
        """Test writing zstd-compressed BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        outfile = tmp_path / "test.bins.zstd"

        with open(outfile, "wb") as f:
            BinSetExporter(binset).write_binsfile(f, compress=True)

        assert outfile.exists()
        with open(outfile, "rb") as f:
            data = f.read()
        # Check it IS zstd compressed (zstd magic number)
        assert data[:4] == b"\x28\xb5\x2f\xfd"

    def test_binset_roundtrip(self, assembly_contigs, bin_files, tmp_path):
        """Test that a BinSet can be written and read back."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        outfile = tmp_path / "test.bins"

        with open(outfile, "wb") as f:
            BinSetExporter(binset).write_binsfile(f, compress=False)

        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        assert len(loaded.contigs) == len(binset.contigs)
        assert loaded.bins is not None
        assert binset.bins is not None
        assert len(loaded.bins) == len(binset.bins)
        assert loaded.bins[0].id == binset.bins[0].id

    def test_binset_update_statistics(self, assembly_contigs, bin_files):
        """Test that update_statistics recalculates bin statistics."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        updated = binset.update_statistics()

        assert updated.bins is not None
        for bin in updated.bins:
            assert bin.statistics is not None
            assert bin.statistics.length is not None
            assert bin.statistics.n_contigs is not None
            assert bin.statistics.longest is not None

    def test_binset_filter_bins(self, assembly_contigs, bin_files):
        """Test filtering bins by query."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Filter for bins with only one contig
        filtered = binset.filter_bins("n_contigs == 1")
        assert filtered.bins is not None
        assert len(filtered.bins) == 2
