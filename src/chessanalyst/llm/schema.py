"""Output schema of the model (§9-bis.6, D-47, Appendix F), pydantic v2.

M1b uses it for V01; M1c generates the ``submit_analysis`` tool schema from it.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator

Source = Literal["engine", "feature", "maia", "theory", "mixed"]
CATEGORIES = ("natural_trap", "hard_move", "solid", "practical_alt", "improbable_error")


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class FeatureAssertion(_M):
    kind: Literal["feature"]
    key: str
    side: Literal["w", "b"] | None
    squares: list[Annotated[str, Field(pattern=r"^[a-h][1-8]$")]] = Field(default_factory=list)


class EvalBandAssertion(_M):
    kind: Literal["eval_band"]
    ref: str
    band: str


class MaiaBandAssertion(_M):
    kind: Literal["maia_band"]
    ref: str
    band: str


class ClassificationAssertion(_M):
    kind: Literal["classification"]
    ref: str
    category: Literal["natural_trap", "hard_move", "solid", "practical_alt", "improbable_error"]


Assertion = Annotated[Union[FeatureAssertion, EvalBandAssertion, MaiaBandAssertion, ClassificationAssertion],
                      Field(discriminator="kind")]


class ParagraphLite(_M):
    text: Annotated[str, Field(min_length=1)]
    source: Source
    assertions: list[Assertion] = Field(default_factory=list)


class Paragraph(_M):
    type: Literal["p"]
    text: Annotated[str, Field(min_length=1)]
    source: Source
    assertions: list[Assertion] = Field(default_factory=list)


class ListBlock(_M):
    type: Literal["ul", "ol"]
    items: Annotated[list[ParagraphLite], Field(min_length=1)]


class Line(_M):
    type: Literal["line"]
    pv: Annotated[str, Field(pattern=r"^PV[1-9][0-9]*$")]
    plies: Annotated[int, Field(ge=1)]
    caption: ParagraphLite = None  # type: ignore[assignment]  # absent, never null (Appendix F)


class DataTable(_M):
    type: Literal["table"]
    ref: Literal["T1", "T2", "T3", "T4"]
    text_cells: dict[str, dict[str, ParagraphLite]] = None  # type: ignore[assignment]


class TextTable(_M):
    type: Literal["text_table"]
    columns: Annotated[list[str], Field(min_length=2, max_length=6)]
    rows: Annotated[list[list[ParagraphLite]], Field(min_length=1)]

    @model_validator(mode="after")
    def _row_width(self) -> "TextTable":
        for k, row in enumerate(self.rows, 1):
            if len(row) != len(self.columns):
                raise ValueError(f"riga {k}: {len(row)} celle per {len(self.columns)} colonne")
        return self


Block = Annotated[Union[Paragraph, ListBlock, Line, DataTable, TextTable], Field(discriminator="type")]


class Section(_M):
    id: Annotated[str, Field(pattern=r"^S(0[1-9]|1[0-3])$")]
    blocks: Annotated[list[Block], Field(min_length=1)]


class AnalysisOutput(_M):
    schema_version: Literal["1"]
    sections: Annotated[list[Section], Field(min_length=1)]
    notes: list[str]


TOOL_NAME = "submit_analysis"
TOOL_DESCRIPTION = "Consegna l'analisi strutturata della posizione."


def _clean(node):
    """Drop pydantic-only keywords (``discriminator``, ``title``): same semantics in JSON Schema."""
    if isinstance(node, dict):
        return {k: _clean(v) for k, v in node.items()
                if k != "discriminator" and not (k == "title" and isinstance(v, str))}
    if isinstance(node, list):
        return [_clean(v) for v in node]
    return node


def input_schema() -> dict:
    return _clean(AnalysisOutput.model_json_schema())


def tool_definition() -> dict:
    """The ``submit_analysis`` tool (Appendix F), generated from the pydantic models."""
    return {"name": TOOL_NAME, "description": TOOL_DESCRIPTION, "input_schema": input_schema()}
