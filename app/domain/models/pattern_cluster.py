from dataclasses import dataclass, field


@dataclass(frozen=True)
class PatternCluster:
    pattern_id: str
    pattern: str
    count: int
    examples: list[str] = field(default_factory=list)
