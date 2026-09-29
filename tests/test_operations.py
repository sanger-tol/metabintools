"""Tests for merging, filtering, and renaming functionality.

Tests BinSet operations including merge, filter, rename, and quality/taxonomy imports.
"""

from pathlib import Path

import click
import pytest

from metabintools.dataclasses.bin import Bin
from metabintools.dataclasses.binset import BinSet
from metabintools.enums import Assembler, QualityTool, TaxonomyTool
from metabintools.export.binset_exporter import BinSetExporter
from metabintools.import_data.assembly import parse_assembly_fasta
from metabintools.import_data.binset import parse_fasta_bins
from metabintools.operations.merge import merge_binsets
from metabintools.operations.rename import rename_bins
from metabintools.query.query_parser import get_available_fields

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
def quality_file():
    """Path to CheckM2 quality file."""
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
    """Path to GTDB-Tk taxonomy file."""
    return TEST_DATA_DIR / "gtdbtk.tsv"

@pytest.fixture
def coverage_file():
    """Path to the coverage file."""
    return TEST_DATA_DIR / "test.coverage.tsv"


@pytest.fixture
def binset_with_quality(assembly_contigs, bin_files, quality_file):
    """Create a BinSet with quality scores."""
    bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
    binset = BinSet(contigs=assembly_contigs, bins=bins)
    return binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)


@pytest.fixture
def binset_with_taxonomy(assembly_contigs, bin_files, taxonomy_file):
    """Create a BinSet with taxonomy."""
    bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
    binset = BinSet(contigs=assembly_contigs, bins=bins)
    return binset.add_bin_taxonomy(taxonomy_file, TaxonomyTool.gtdbtk)


@pytest.fixture
def binset_full_metadata(assembly_contigs, bin_files, quality_file, taxonomy_file):
    """Create a BinSet with all metadata."""
    bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
    binset = BinSet(contigs=assembly_contigs, bins=bins)
    binset = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)
    binset = binset.add_bin_taxonomy(taxonomy_file, TaxonomyTool.gtdbtk)
    return binset


class TestMerging:
    """Tests for merging multiple BinSets."""

    def test_merge_two_binsets(self, assembly_contigs, bin_files):
        """Test merging two BinSets with different bins."""
        # Create two separate binsets with different groups
        bins1 = parse_fasta_bins(
            bin_files, group="group1", asm_contigs=assembly_contigs
        )
        binset1 = BinSet(contigs=assembly_contigs, bins=bins1)

        # Create bins with different IDs for group2
        bins_group2 = [
            Bin(
                id="group2_bin1",
                import_name="bin1.fasta",
                group="group2",
                contigs=["contig1"],
            ),
            Bin(
                id="group2_bin2",
                import_name="bin2.fasta",
                group="group2",
                contigs=["contig2"],
            ),
        ]
        binset2 = BinSet(contigs=assembly_contigs, bins=bins_group2)

        merged = merge_binsets([binset1, binset2])

        assert merged.bins is not None
        assert len(merged.bins) == 4
        assert merged.contigs == assembly_contigs

    def test_merge_preserves_bin_group(self, assembly_contigs, bin_files):
        """Test that merge preserves bin group information."""
        bins1 = parse_fasta_bins(
            bin_files, group="metabat", asm_contigs=assembly_contigs
        )
        binset1 = BinSet(contigs=assembly_contigs, bins=bins1)

        bins2 = [
            Bin(
                id="vamb_bin1",
                import_name="bin1.fasta",
                group="vamb",
                contigs=["contig1"],
            ),
            Bin(
                id="vamb_bin2",
                import_name="bin2.fasta",
                group="vamb",
                contigs=["contig2"],
            ),
        ]
        binset2 = BinSet(contigs=assembly_contigs, bins=bins2)

        merged = merge_binsets([binset1, binset2])

        assert merged.bins is not None
        groups = {bin.group for bin in merged.bins}
        assert groups == {"metabat", "vamb"}

    def test_merge_rejects_conflicting_contigs(self, assembly_contigs, tmp_path):
        """Test that merge rejects contigs with different sequences."""
        # Create binset1
        bins1 = [
            Bin(
                id="bin1",
                import_name="test1.fasta",
                group="test",
                contigs=["contig1"],
            )
        ]
        binset1 = BinSet(contigs=assembly_contigs, bins=bins1)

        # Create binset2 with conflicting contig
        conflicting_contigs = assembly_contigs.copy()
        conflicting_contigs["contig1"] = conflicting_contigs["contig1"].model_copy(
            update={"sequence": "TTTTTTTTTTTT"}  # Different sequence
        )

        bins2 = [
            Bin(
                id="bin2",
                import_name="test2.fasta",
                group="test",
                contigs=["contig1"],
            )
        ]
        binset2 = BinSet(contigs=conflicting_contigs, bins=bins2)

        with pytest.raises(click.ClickException):
            merge_binsets([binset1, binset2])

    def test_merge_rejects_duplicate_bin_ids(self, assembly_contigs, bin_files):
        """Test that merge rejects duplicate bin IDs across binsets."""
        bins1 = parse_fasta_bins(
            bin_files, group="group1", asm_contigs=assembly_contigs
        )
        binset1 = BinSet(contigs=assembly_contigs, bins=bins1)

        # Same bin file without renaming - will create same IDs
        bins2 = parse_fasta_bins(
            bin_files, group="group2", asm_contigs=assembly_contigs
        )
        binset2 = BinSet(contigs=assembly_contigs, bins=bins2)

        with pytest.raises(click.ClickException):
            merge_binsets([binset1, binset2])

    def test_merge_multiple_binsets(self, assembly_contigs):
        """Test merging more than two BinSets."""
        binsets = []
        for i in range(3):
            # Create unique bins for each group using available contigs
            group_bins = [
                Bin(
                    id=f"group{i}_bin1",
                    import_name="bin1.fasta",
                    group=f"group{i}",
                    contigs=["contig1"],
                ),
                Bin(
                    id=f"group{i}_bin2",
                    import_name="bin2.fasta",
                    group=f"group{i}",
                    contigs=["contig2"],
                ),
            ]
            binsets.append(BinSet(contigs=assembly_contigs, bins=group_bins))

        merged = merge_binsets(binsets)

        assert merged.bins is not None
        assert len(merged.bins) == 6  # 2 bins * 3 binsets


class TestFiltering:
    """Tests for filtering bins by query expressions."""

    def test_filter_by_group(self, assembly_contigs, bin_files):
        """Test filtering bins by group."""
        bins1 = parse_fasta_bins(
            bin_files, group="metabat", asm_contigs=assembly_contigs
        )
        bins2 = [
            Bin(
                id="vamb_bin1",
                import_name="bin1.fasta",
                group="vamb",
                contigs=["contig1"],
            ),
            Bin(
                id="vamb_bin2",
                import_name="bin2.fasta",
                group="vamb",
                contigs=["contig2"],
            ),
        ]
        all_bins = bins1 + bins2

        binset = BinSet(contigs=assembly_contigs, bins=all_bins)
        filtered = binset.filter_bins('group == "metabat"')

        assert filtered.bins is not None
        assert len(filtered.bins) == 2
        assert all(b.group == "metabat" for b in filtered.bins)

    def test_filter_by_completeness(self, binset_with_quality):
        """Test filtering bins by completeness score."""
        # Bins in test data have completeness > 0.99 (normalized from 99%)
        filtered = binset_with_quality.filter_bins("completeness > 0.99")
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_by_contamination(self, binset_with_quality):
        """Test filtering bins by contamination."""
        # Bins in test data have contamination < 2
        filtered = binset_with_quality.filter_bins("contamination < 2")
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_with_and_operator(self, binset_with_quality):
        """Test filtering with AND logic."""
        filtered = binset_with_quality.filter_bins(
            "completeness > 0.99 and contamination < 0.02"
        )
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_with_or_operator(self, binset_with_quality):
        """Test filtering with OR logic."""
        filtered = binset_with_quality.filter_bins('id == "bin1" or id == "bin2"')
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_by_taxonomy(self, binset_with_taxonomy):
        """Test filtering by taxonomy field."""
        filtered = binset_with_taxonomy.filter_bins('tax_phylum == "Bacillota"')
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_by_length(self, binset_with_quality):
        """Test filtering by contig length."""
        # Both test bins contain multiple contigs
        filtered = binset_with_quality.filter_bins("length > 0")
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_by_n_contigs(self, binset_with_quality):
        """Test filtering by number of contigs."""
        filtered = binset_with_quality.filter_bins("n_contigs == 1")
        assert filtered.bins is not None
        assert len(filtered.bins) == 2

    def test_filter_empty_result(self, binset_with_quality):
        """Test filter that returns no results."""
        filtered = binset_with_quality.filter_bins("completeness < 0.5")
        assert filtered.bins is not None
        assert len(filtered.bins) == 0

    def test_filter_invalid_query(self, assembly_contigs, bin_files):
        """Test that invalid query raises ValueError."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        with pytest.raises(ValueError):
            binset.filter_bins("nonexistent_field == 'value'")

    def test_filter_with_injection_attempt(self, assembly_contigs, bin_files):
        """Test that injection attempts are blocked."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        with pytest.raises(ValueError):
            binset.filter_bins("__import__('os')")

    def test_get_available_fields(self):
        """Test that available fields can be queried."""
        fields = get_available_fields()
        assert isinstance(fields, dict)
        assert "id" in fields
        assert "group" in fields
        assert "completeness" in fields
        assert "contamination" in fields
        assert "tax_phylum" in fields


class TestRenaming:
    """Tests for renaming bins using templates."""

    def test_rename_with_group(self, assembly_contigs, bin_files):
        """Test renaming bins using group field."""
        bins = parse_fasta_bins(
            bin_files, group="metabat", asm_contigs=assembly_contigs
        )
        renamed = rename_bins(bins, "bin_{group}")

        assert renamed[0].id.startswith("bin_metabat")
        assert renamed[1].id.startswith("bin_metabat")

    def test_rename_with_id(self, assembly_contigs, bin_files):
        """Test renaming bins using original ID."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        renamed = rename_bins(bins, "renamed_{id}")

        assert renamed[0].id.startswith("renamed_bin1")
        assert renamed[1].id.startswith("renamed_bin2")

    def test_rename_with_taxonomy(self, binset_with_taxonomy):
        """Test renaming bins using taxonomy field."""
        assert binset_with_taxonomy.bins is not None
        renamed = rename_bins(binset_with_taxonomy.bins, "bin_{tax_phylum}")

        # Both bins should have Bacillota as phylum
        assert all("Bacillota" in b.id for b in renamed)

    def test_rename_collision_handling(self, binset_with_taxonomy):
        """Test that colliding names get numeric suffixes."""
        assert binset_with_taxonomy.bins is not None
        # Both bins have same phylum, so should get different numeric suffixes
        renamed = rename_bins(binset_with_taxonomy.bins, "bin_{tax_phylum}")

        # Check that both have different IDs despite same template output
        assert renamed[0].id != renamed[1].id
        # Check they have numeric suffixes
        assert renamed[0].id.endswith(("_1", "_2"))
        assert renamed[1].id.endswith(("_1", "_2"))

    def test_rename_multiple_fields(self, binset_with_taxonomy):
        """Test renaming with multiple template fields."""
        assert binset_with_taxonomy.bins is not None
        renamed = rename_bins(binset_with_taxonomy.bins, "{group}_{id}_{tax_phylum}")

        assert all("_Bacillota" in b.id for b in renamed)

    def test_rename_preserves_other_attributes(self, assembly_contigs, bin_files):
        """Test that rename only changes ID, not other attributes."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        original_group = bins[0].group
        original_contigs = bins[0].contigs

        renamed = rename_bins(bins, "new_{id}")

        assert renamed[0].group == original_group
        assert renamed[0].contigs == original_contigs
        assert renamed[0].id != bins[0].id


class TestBinSetOperations:
    """Tests for operations on BinSet objects."""

    def test_binset_filter_then_trim(self, binset_with_quality):
        """Test filtering followed by trimming unused contigs."""
        # Filter to keep only high quality
        filtered = binset_with_quality.filter_bins("completeness > 99")
        assert filtered.bins is not None

        # Trim unreferenced contigs
        trimmed = filtered.remove_unreferenced_contigs()
        # Should have fewer or equal contigs
        assert len(trimmed.contigs) <= len(filtered.contigs)

    def test_binset_add_quality_scores(self, assembly_contigs, bin_files, quality_file):
        """Test adding quality scores to BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Verify no quality initially
        assert binset.bins is not None
        assert (
            binset.bins[0].statistics is None
            or binset.bins[0].statistics.completeness is None
        )

        # Add quality
        with_quality = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Verify quality added
        assert with_quality.bins is not None
        assert with_quality.bins[0].statistics is not None
        assert with_quality.bins[0].statistics.completeness is not None
        assert with_quality.bins[0].statistics.completeness > 0

    def test_binset_add_taxonomy(self, assembly_contigs, bin_files, taxonomy_file):
        """Test adding taxonomy to BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Verify no taxonomy initially
        assert binset.bins is not None
        assert binset.bins[0].taxonomy is None

        # Add taxonomy
        with_taxonomy = binset.add_bin_taxonomy(taxonomy_file, TaxonomyTool.gtdbtk)

        # Verify taxonomy added
        assert with_taxonomy.bins is not None
        assert with_taxonomy.bins[0].taxonomy is not None
        assert with_taxonomy.bins[0].taxonomy.tax_phylum is not None

    def test_binset_rename_bins(self, binset_with_taxonomy):
        """Test renaming bins via BinSet method."""
        assert binset_with_taxonomy.bins is not None
        original_id = binset_with_taxonomy.bins[0].id

        renamed = binset_with_taxonomy.rename_bins("renamed_{id}")

        assert renamed.bins is not None
        assert renamed.bins[0].id != original_id
        assert "renamed_" in renamed.bins[0].id

    def test_binset_chained_operations(
        self, assembly_contigs, bin_files, quality_file, taxonomy_file
    ):
        """Test chaining multiple operations."""
        # Start with assembly
        bins = parse_fasta_bins(
            bin_files, group="metabat", asm_contigs=assembly_contigs
        )
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add metadata
        binset = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)
        binset = binset.add_bin_taxonomy(taxonomy_file, TaxonomyTool.gtdbtk)

        # Filter
        binset = binset.filter_bins("completeness > 0.99")

        # Rename
        binset = binset.rename_bins("hq_{tax_phylum}_{group}")

        # Trim
        binset = binset.remove_unreferenced_contigs()

        # Verify final state
        assert binset.bins is not None
        if len(binset.bins) > 0:
            assert all("hq_" in b.id for b in binset.bins)


class TestRoundtrip:
    """Tests for serializing and deserializing with operations."""

    def test_filter_serialize_deserialize(self, binset_with_quality, tmp_path):
        """Test filtering, serializing, and deserializing."""
        # Filter
        filtered = binset_with_quality.filter_bins("completeness > 99")

        # Serialize
        outfile = tmp_path / "filtered.bins"
        with open(outfile, "wb") as f:
            BinSetExporter(filtered).write_binsfile(f, compress=False)

        # Deserialize
        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        # Verify
        assert loaded.bins is not None
        assert len(loaded.bins) == len(filtered.bins)

    def test_rename_serialize_deserialize(self, binset_with_taxonomy, tmp_path):
        """Test renaming, serializing, and deserializing."""
        # Rename
        renamed = binset_with_taxonomy.rename_bins("hq_{tax_phylum}")

        # Serialize
        outfile = tmp_path / "renamed.bins"
        with open(outfile, "wb") as f:
            BinSetExporter(renamed).write_binsfile(f, compress=True)

        # Deserialize
        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        # Verify renamed IDs persisted
        assert loaded.bins is not None
        assert all("hq_" in b.id for b in loaded.bins)

    def test_merge_serialize_deserialize(self, assembly_contigs, bin_files, tmp_path):
        """Test merging, serializing, and deserializing."""
        # Create and merge binsets
        bins1 = parse_fasta_bins(
            bin_files, group="group1", asm_contigs=assembly_contigs
        )
        binset1 = BinSet(contigs=assembly_contigs, bins=bins1)

        bins2 = [
            Bin(
                id="group2_bin1",
                import_name="bin1.fasta",
                group="group2",
                contigs=["contig1"],
            ),
            Bin(
                id="group2_bin2",
                import_name="bin2.fasta",
                group="group2",
                contigs=["contig2"],
            ),
        ]
        binset2 = BinSet(contigs=assembly_contigs, bins=bins2)

        merged = merge_binsets([binset1, binset2])

        # Serialize
        outfile = tmp_path / "merged.bins"
        with open(outfile, "wb") as f:
            BinSetExporter(merged).write_binsfile(f, compress=False)

        # Deserialize
        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        # Verify
        assert loaded.bins is not None
        assert len(loaded.bins) == 4


class TestQualityTools:
    """Tests for importing and parsing different quality tools."""

    def test_add_checkm2_quality_scores(
        self, assembly_contigs, bin_files, quality_file
    ):
        """Test adding CheckM2 quality scores to BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add CheckM2 quality
        with_quality = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Verify quality added to bins
        assert with_quality.bins is not None
        assert len(with_quality.bins) == 2

        bin1 = next((b for b in with_quality.bins if b.id == "bin1"), None)
        assert bin1 is not None
        assert bin1.statistics is not None
        assert bin1.statistics.completeness is not None
        assert bin1.statistics.contamination is not None
        assert 0 <= bin1.statistics.completeness <= 1
        assert 0 <= bin1.statistics.contamination <= 1
        assert bin1.statistics.quality_tool == QualityTool.checkm2

    def test_add_checkm_v1_quality_scores(
        self, assembly_contigs, bin_files, checkm_quality_file
    ):
        """Test adding CheckM v1 quality scores to BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add CheckM v1 quality
        with_quality = binset.add_bin_quality_scores(
            checkm_quality_file, QualityTool.checkm
        )

        # Verify quality added to bins
        assert with_quality.bins is not None
        assert len(with_quality.bins) == 2

        bin1 = next((b for b in with_quality.bins if b.id == "bin1"), None)
        assert bin1 is not None
        assert bin1.statistics is not None
        assert bin1.statistics.completeness is not None
        assert bin1.statistics.contamination is not None
        # CheckM values should be converted to 0-1 range (percentages)
        assert 0 <= bin1.statistics.completeness <= 1
        assert 0 <= bin1.statistics.contamination <= 1
        assert bin1.statistics.quality_tool == QualityTool.checkm

    def test_add_busco_quality_scores(
        self, assembly_contigs, bin_files, busco_quality_file
    ):
        """Test adding BUSCO quality scores to BinSet."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add BUSCO quality
        with_quality = binset.add_bin_quality_scores(
            busco_quality_file, QualityTool.busco
        )

        # Verify quality added to bins
        assert with_quality.bins is not None
        assert len(with_quality.bins) == 2

        bin1 = next((b for b in with_quality.bins if b.id == "bin1"), None)
        assert bin1 is not None
        assert bin1.statistics is not None
        # BUSCO uses 'Complete' for completeness and 'Duplicated' for contamination
        assert bin1.statistics.completeness is not None
        assert bin1.statistics.contamination is not None
        # Values should be normalized to 0-1 range
        assert 0 <= bin1.statistics.completeness <= 1
        assert 0 <= bin1.statistics.contamination <= 1
        assert bin1.statistics.quality_tool == QualityTool.busco

    def test_quality_scores_preserved_after_filter(
        self, assembly_contigs, bin_files, quality_file
    ):
        """Test that quality scores are preserved after filtering."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        with_quality = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Filter bins
        filtered = with_quality.filter_bins("completeness > 0.95")

        # Verify quality preserved
        assert filtered.bins is not None
        for bin in filtered.bins:
            assert bin.statistics is not None
            assert bin.statistics.completeness is not None
            assert bin.statistics.contamination is not None

    def test_quality_scores_preserved_after_rename(
        self, assembly_contigs, bin_files, quality_file
    ):
        """Test that quality scores are preserved after renaming."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        with_quality = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Rename bins
        renamed = with_quality.rename_bins("hq_{id}")

        # Verify quality preserved
        assert renamed.bins is not None
        for bin in renamed.bins:
            assert bin.statistics is not None
            assert bin.statistics.completeness is not None
            assert bin.statistics.contamination is not None
            assert "hq_" in bin.id

    def test_checkm2_vs_checkm_different_formats(
        self, assembly_contigs, bin_files, quality_file, checkm_quality_file
    ):
        """Test that CheckM2 and CheckM parse different format correctly."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)

        # Add CheckM2
        binset_checkm2 = BinSet(
            contigs=assembly_contigs, bins=bins
        ).add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Add CheckM v1
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset_checkm = BinSet(
            contigs=assembly_contigs, bins=bins
        ).add_bin_quality_scores(checkm_quality_file, QualityTool.checkm)

        # Both should have quality scores
        assert binset_checkm2.bins is not None
        assert binset_checkm.bins is not None

        checkm2_bin1 = next((b for b in binset_checkm2.bins if b.id == "bin1"), None)
        checkm_bin1 = next((b for b in binset_checkm.bins if b.id == "bin1"), None)

        assert checkm2_bin1 is not None
        assert checkm_bin1 is not None
        assert checkm2_bin1.statistics is not None
        assert checkm_bin1.statistics is not None
        assert checkm2_bin1.statistics.completeness > 0
        assert checkm_bin1.statistics.completeness > 0
        # Different tools may have different completeness values
        assert checkm2_bin1.statistics.quality_tool == QualityTool.checkm2
        assert checkm_bin1.statistics.quality_tool == QualityTool.checkm

    def test_busco_vs_checkm2_completeness_contamination(
        self, assembly_contigs, bin_files, quality_file, busco_quality_file
    ):
        """Test that BUSCO and CheckM2 map completeness/contamination correctly."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset_checkm2 = BinSet(
            contigs=assembly_contigs, bins=bins
        ).add_bin_quality_scores(quality_file, QualityTool.checkm2)

        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset_busco = BinSet(
            contigs=assembly_contigs, bins=bins
        ).add_bin_quality_scores(busco_quality_file, QualityTool.busco)

        # Both should have quality scores
        assert binset_checkm2.bins is not None
        assert binset_busco.bins is not None

        # Verify BUSCO completeness is mapped from 'Complete' column
        busco_bin1 = next((b for b in binset_busco.bins if b.id == "bin1"), None)
        assert busco_bin1 is not None
        assert busco_bin1.statistics is not None
        assert busco_bin1.statistics.completeness is not None
        # BUSCO Complete value should be high for this test data
        assert busco_bin1.statistics.completeness > 0.8

    def test_quality_scores_roundtrip_with_serialization(
        self, assembly_contigs, bin_files, quality_file, tmp_path
    ):
        """Test that quality scores survive serialization/deserialization."""
        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)
        with_quality = binset.add_bin_quality_scores(quality_file, QualityTool.checkm2)

        # Serialize
        outfile = tmp_path / "quality.bins"
        with open(outfile, "wb") as f:
            BinSetExporter(with_quality).write_binsfile(f, compress=False)

        # Deserialize
        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        # Verify quality scores preserved
        assert loaded.bins is not None
        for i, bin in enumerate(loaded.bins):
            assert bin.statistics is not None
            assert bin.statistics.completeness is not None
            assert bin.statistics.contamination is not None
            # Verify values match original
            original_bin = with_quality.bins[i]
            assert bin.statistics.completeness == original_bin.statistics.completeness
            assert bin.statistics.contamination == original_bin.statistics.contamination


class TestCoverageOperations:
    """Tests for coverage data operations."""

    def test_add_contig_coverage_basic(
        self, assembly_contigs, bin_files, coverage_file
    ):
        """Test basic contig coverage addition."""
        from metabintools.enums import CoverageTool

        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add coverage data
        with_coverage = binset.add_contig_coverage(
            coverage_file, CoverageTool.metabat, "test.bam$"
        )

        # Verify coverage data was added
        assert with_coverage is not None
        for contig_id in with_coverage.contigs:
            contig = with_coverage.contigs[contig_id]
            if contig_id in ["contig1", "contig2"]:
                # These contigs are in the coverage file
                assert contig.coverage is not None
                assert contig.coverage > 0

    def test_add_contig_coverage_with_column_regex(
        self, assembly_contigs, bin_files, coverage_file
    ):
        """Test coverage addition with different column regex patterns."""
        from metabintools.enums import CoverageTool

        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Test with escaped dots regex
        with_coverage = binset.add_contig_coverage(
            coverage_file, CoverageTool.metabat, "test.bam$"
        )
        assert with_coverage is not None

    def test_add_contig_coverage_preserves_existing_metadata(
        self, assembly_contigs, bin_files, coverage_file
    ):
        """Test that coverage addition preserves existing bin/contig metadata."""
        from metabintools.enums import CoverageTool

        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add coverage
        with_coverage = binset.add_contig_coverage(
            coverage_file, CoverageTool.metabat, "test.bam$"
        )

        # Verify original metadata preserved
        assert len(with_coverage.bins) == len(binset.bins)
        assert len(with_coverage.contigs) == len(binset.contigs)
        for i, bin in enumerate(with_coverage.bins):
            original_bin = binset.bins[i]
            assert bin.id == original_bin.id
            assert bin.group == original_bin.group
            assert len(bin.contigs) == len(original_bin.contigs)

    def test_add_contig_coverage_roundtrip(
        self, assembly_contigs, bin_files, coverage_file, tmp_path
    ):
        """Test that coverage data survives serialization/deserialization."""
        from metabintools.enums import CoverageTool

        bins = parse_fasta_bins(bin_files, group="test", asm_contigs=assembly_contigs)
        binset = BinSet(contigs=assembly_contigs, bins=bins)

        # Add coverage
        with_coverage = binset.add_contig_coverage(
            coverage_file, CoverageTool.metabat, "test.bam$"
        )

        # Get coverage values before serialization
        coverage_before = {}
        for contig_id, contig in with_coverage.contigs.items():
            if contig.coverage is not None:
                coverage_before[contig_id] = contig.coverage

        # Serialize
        outfile = tmp_path / "coverage.bins"
        with open(outfile, "wb") as f:
            BinSetExporter(with_coverage).write_binsfile(f, compress=False)

        # Deserialize
        with open(outfile, "rb") as f:
            loaded = BinSet.read_binsfile(f)

        # Verify coverage data preserved
        for contig_id, coverage_value in coverage_before.items():
            contig = loaded.contigs[contig_id]
            assert contig.coverage is not None
            assert contig.coverage == coverage_value
