from typing import Any, Dict, List

from pydantic import BaseModel, Field

class CandidateConfig(BaseModel):
    params: Dict[str, Any] = Field(default_factory=dict)

    def to_compile_flags(self) -> str:
        flags = []
        for k, v in self.params.items():
            if isinstance(v, bool):
                flags.append(f"-D{k.upper()}={1 if v else 0}")
            else:
                flags.append(f"-D{k.upper()}={v}")
        return " ".join(flags)

class ProjectConfig(BaseModel):
    version: int = 1
    name: str
    description: str
    build: Dict[str, str]
    run: Dict[str, str]
    input: Dict[str, Any]
    objective: Dict[str, str]
    search_space: Dict[str, List[Any]]
    constraints: List[str] = Field(default_factory=list)
    validation: Dict[str, float]
    budget: Dict[str, int]
