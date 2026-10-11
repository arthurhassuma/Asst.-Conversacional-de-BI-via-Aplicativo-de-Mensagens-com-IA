"""Contrato do conjunto congelado e validação das consultas de referência."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.sql_policy import validate_select


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Reference(StrictModel):
    metric: str
    sql: str
    types: list[Literal["number", "text", "date"]] = Field(min_length=1)
    ordered: bool = False
    interpretation: str

    @model_validator(mode="after")
    def safe_sql(self):
        validate_select(self.sql)
        return self


class Turn(StrictModel):
    question: str = Field(min_length=1, max_length=4000)
    expected: Literal[
        "answer", "clarification_period", "clarification_metric", "clarification_measure"
    ]
    references: list[Reference] = Field(default_factory=list)

    @model_validator(mode="after")
    def references_match_outcome(self):
        if (self.expected == "answer") != bool(self.references):
            raise ValueError("Somente respostas de consulta exigem referências SQL.")
        if len({r.metric for r in self.references}) != len(self.references):
            raise ValueError("Métricas repetidas na mesma resposta de referência.")
        return self


class Case(StrictModel):
    id: str = Field(pattern=r"^[DT]\d{2}$")
    split: Literal["development", "test"]
    category: str
    turns: list[Turn] = Field(min_length=1, max_length=4)


class Dataset(StrictModel):
    version: str
    seed: int
    clients: int
    cases: list[Case]

    @model_validator(mode="after")
    def unique_ids(self):
        if len({case.id for case in self.cases}) != len(self.cases):
            raise ValueError("Identificadores de casos duplicados.")
        return self


def load_dataset(path: Path) -> Dataset:
    return Dataset.model_validate_json(path.read_text(encoding="utf-8"))
