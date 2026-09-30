from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, computed_field

from metabintools.dataclasses.annotation import Annotation


class Contig(BaseModel):
    id: str = Field(..., description="Contig ID.")
    header: str = Field(..., description="Full contig header including ID.")
    sequence: Annotated[str, StringConstraints(pattern=r"^[ACGTN]+$")] = Field(
        ..., description="Sequence of the contig."
    )
    sequence_length: Annotated[int, Field(gt=0)] = Field(
        ..., description="Length of the sequence."
    )
    topology: Literal["linear", "circular"] | None = Field(
        None, description="Topology of the contig."
    )
    coverage: Annotated[float, Field(ge=0)] | None = Field(
        None, description="Depth of the contig in the originating sample."
    )
    annotations: list[Annotation] | None = Field(
        None, description="Annotations of the contig."
    )

    @computed_field
    @property
    def gc(self) -> float:
        return (
            self.sequence.count("G") + self.sequence.count("C")
        ) / self.sequence_length

    @computed_field
    @property
    def trnas(self) -> list[str]:
        if self.annotations is None:
            return []
        return [
            isotype
            for a in self.annotations
            if a.feature == "tRNA"
            and (isotype := a.attributes.get("isotype")) is not None
        ]

    def _has_any_rrna(self, names: list[str]) -> bool:
        if self.annotations is None:
            return False

        return any(
            bool(a.attributes.get("product") in names)
            for a in self.annotations
            if a.feature == "rRNA"
        )

    @computed_field
    @property
    def has_5s(self) -> bool:
        return self._has_any_rrna(["5S", "5S ribosomal RNA", "5S rRNA"])

    @computed_field
    @property
    def has_16s(self) -> bool:
        return self._has_any_rrna(["16S", "16S ribosomal RNA", "16S rRNA"])

    @computed_field
    @property
    def has_23s(self) -> bool:
        return self._has_any_rrna(["23S", "23S ribosomal RNA", "23S rRNA"])
