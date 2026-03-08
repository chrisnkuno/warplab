from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any

class CandidateConfig(BaseModel):
    block_size: int = 256
    unroll: int = 1
    vector_width: int = 1
    use_shared: bool = False
    
    # Allow for additional dynamic parameters
    extra: Dict[str, Any] = Field(default_factory=dict)

    def to_compile_flags(self) -> str:
        flags = [
            f"-DBLOCK_SIZE={self.block_size}",
            f"-DUNROLL={self.unroll}",
            f"-DVECTOR_WIDTH={self.vector_width}",
            f"-DUSE_SHARED={1 if self.use_shared else 0}"
        ]
        for k, v in self.extra.items():
            if isinstance(v, bool):
                flags.append(f"-D{k.upper()}={1 if v else 0}")
            else:
                flags.append(f"-D{k.upper()}={v}")
        return " ".join(flags)

class ProjectConfig(BaseModel):
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
