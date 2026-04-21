from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ChartAxis:
    label: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportChart:
    chart_id: str
    title: str
    category: str
    chart_type: str
    series: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""
    required: bool = False
    tags: list[str] = field(default_factory=list)
    x_axis: ChartAxis = field(default_factory=lambda: ChartAxis(label="Time"))
    y_axis: ChartAxis = field(default_factory=lambda: ChartAxis(label="Value"))
    payload: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["x_axis"] = self.x_axis.to_dict()
        payload["y_axis"] = self.y_axis.to_dict()
        return payload


@dataclass(frozen=True)
class ReportTable:
    table_id: str
    title: str
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisBlock:
    block_id: str
    title: str
    body: str
    severity: str = "info"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReportDocument:
    report_version: str
    experiment_summary: dict[str, Any]
    algorithm_summary: dict[str, Any]
    evaluation_summary: dict[str, Any]
    charts: list[ReportChart] = field(default_factory=list)
    tables: list[ReportTable] = field(default_factory=list)
    analysis_blocks: list[AnalysisBlock] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    summary_cards: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_version": self.report_version,
            "experiment_summary": self.experiment_summary,
            "algorithm_summary": self.algorithm_summary,
            "evaluation_summary": self.evaluation_summary,
            "charts": [chart.to_dict() for chart in self.charts],
            "tables": [table.to_dict() for table in self.tables],
            "analysis_blocks": [block.to_dict() for block in self.analysis_blocks],
            "artifacts": self.artifacts,
            "diagnostics": self.diagnostics,
            "summary_cards": self.summary_cards,
        }
