from pydantic import BaseModel, Field

from metabintools.enums import MiMAG, QualityTool


class BinStatistics(BaseModel):
    length: int | None = Field(None, gt=0, description="Length of the bin in bp")
    longest: int | None = Field(
        None, gt=0, description="Length of the longest contig in the bin in bp"
    )
    n_contigs: int | None = Field(
        None, gt=0, description="Number of contigs in the bin"
    )
    n_circular: int | None = Field(
        None, ge=0, description="Number of circular contigs in the bin"
    )
    n50: int | None = Field(None, ge=0, description="N50 of the bin")
    coverage: float | None = Field(None, ge=0, description="Coverage of the bin")
    completeness: float | None = Field(
        None, ge=0, le=1, description="Completeness of the bin"
    )
    contamination: float | None = Field(
        None, ge=0, le=1, description="Contamination of the bin"
    )
    quality_tool: QualityTool | None = Field(
        None, description="Quality tool used to assess the bin"
    )
    n_unique_trnas: int | None = Field(
        None, description="Number of unique tRNAs in the bin"
    )
    has_5s: bool | None = Field(None, description="Whether the bin contains 5S rRNA")
    has_16s: bool | None = Field(None, description="Whether the bin contains 16S rRNA")
    has_23s: bool | None = Field(None, description="Whether the bin contains 23S rRNA")
    mimag: MiMAG | None = Field(None, description="MiMAG level of the bin")

    def update_mimag(self) -> None:
        """
        Update the MiMAG level of the bin based on the number of contigs, circularity, completeness, contamination, and unique tRNAs.
        """
        if (
            self.n_contigs is not None
            and self.n_circular is not None
            and self.completeness is not None
            and self.contamination is not None
            and self.n_unique_trnas is not None
            and self.has_5s is not None
            and self.has_16s is not None
            and self.has_23s is not None
        ):
            conditions = {
                MiMAG.HIGH: (
                    self.contamination <= 5
                    and self.n_unique_trnas >= 18
                    and self.has_5s
                    and self.has_16s
                    and self.has_23s
                    and (
                        (self.completeness >= 0.5 and self.n_contigs == self.n_circular)
                        or self.completeness >= 0.9
                    )
                ),
                MiMAG.MEDIUM: self.completeness >= 0.5 and self.contamination <= 0.1,
                MiMAG.LOW: True,
            }
            self.mimag = next(quality for quality, met in conditions.items() if met)

        else:
            self.mimag = None
