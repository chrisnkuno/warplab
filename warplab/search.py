import random
import ast
from abc import ABC, abstractmethod
from typing import Any

from .models import CandidateConfig, ProjectConfig

_ALLOWED_BINARY_OPS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
}

_ALLOWED_UNARY_OPS = {
    ast.UAdd: lambda a: +a,
    ast.USub: lambda a: -a,
    ast.Not: lambda a: not a,
}

_ALLOWED_COMPARE_OPS = {
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}


def _eval_constraint(node: ast.AST, context: dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_constraint(node.body, context)
    if isinstance(node, ast.Name):
        if node.id not in context:
            raise ValueError(f"Unknown parameter in constraint: {node.id}")
        return context[node.id]
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BoolOp):
        values = [_eval_constraint(value, context) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValueError(f"Unsupported boolean operator: {type(node.op).__name__}")
    if isinstance(node, ast.UnaryOp):
        op = _ALLOWED_UNARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op(_eval_constraint(node.operand, context))
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINARY_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
        return op(_eval_constraint(node.left, context), _eval_constraint(node.right, context))
    if isinstance(node, ast.Compare):
        left = _eval_constraint(node.left, context)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _ALLOWED_COMPARE_OPS.get(type(op_node))
            if op is None:
                raise ValueError(f"Unsupported comparison operator: {type(op_node).__name__}")
            right = _eval_constraint(comparator, context)
            if not op(left, right):
                return False
            left = right
        return True
    raise ValueError(f"Unsupported constraint expression: {type(node).__name__}")


def is_valid_config(config_data: dict[str, Any], constraints: list[str]) -> bool:
    for constraint in constraints:
        try:
            parsed = ast.parse(constraint, mode="eval")
            if not bool(_eval_constraint(parsed, config_data)):
                return False
        except Exception:
            return False
    return True


def set_search_seed(seed: int | None):
    if seed is not None:
        random.seed(seed)


def _ordered_values(values: list[Any], strategy: str) -> list[Any]:
    if not values:
        return values
    if strategy == "max":
        return sorted(values, reverse=True)
    if strategy == "min":
        return sorted(values)
    if strategy == "middle":
        ordered = sorted(values)
        mid = len(ordered) // 2
        return ordered[mid:] + ordered[:mid]
    return list(values)


def generate_profile_guided_candidates(
    project_config: ProjectConfig,
    profile_metrics: dict[str, Any],
    count: int,
) -> list[CandidateConfig]:
    from .profiler import BottleneckInference

    diagnosis = BottleneckInference(profile_metrics).classify()
    preference_map: dict[str, str] = {}
    if diagnosis == "Latency-bound or Low-Occupancy":
        preference_map["block_size"] = "max"
        preference_map["unroll"] = "middle"
    elif diagnosis == "Memory-bound (DRAM)":
        preference_map["vector_width"] = "max"
        preference_map["block_size"] = "middle"
    elif diagnosis == "Memory-bound (L1/TEX)":
        preference_map["vector_width"] = "max"
    elif diagnosis == "Compute-bound (SM)":
        preference_map["unroll"] = "max"

    candidates = []
    seen = set()
    attempts = 0
    while len(candidates) < count and attempts < count * 10:
        attempts += 1
        config_data = {}
        for param, values in project_config.search_space.items():
            ordered = _ordered_values(values, preference_map.get(param, "random"))
            top_slice = max(1, min(len(ordered), 2))
            sampled_values = ordered[:top_slice] if preference_map.get(param) else ordered
            config_data[param] = random.choice(sampled_values)
        key = tuple(sorted(config_data.items()))
        if key in seen:
            continue
        if is_valid_config(config_data, project_config.constraints):
            candidates.append(CandidateConfig(params=config_data))
            seen.add(key)
    return candidates


def generate_local_refinements(
    base_candidates: list[CandidateConfig],
    project_config: ProjectConfig,
    count: int,
) -> list[CandidateConfig]:
    refinements = []
    seen = {tuple(sorted(candidate.params.items())) for candidate in base_candidates}
    source_candidates = base_candidates or [CandidateConfig(params={})]
    attempts = 0
    while len(refinements) < count and attempts < count * 10:
        attempts += 1
        base = random.choice(source_candidates)
        refined = perturb_config(base, project_config)
        key = tuple(sorted(refined.params.items()))
        if key in seen:
            continue
        refinements.append(refined)
        seen.add(key)
    return refinements

class SearchStrategy(ABC):
    @abstractmethod
    def generate(self, project_config: ProjectConfig, count: int) -> list[CandidateConfig]:
        pass

class RandomSearch(SearchStrategy):
    def generate(self, project_config: ProjectConfig, count: int) -> list[CandidateConfig]:
        candidates = []
        seen = set()
        space = project_config.search_space
        
        attempts = 0
        while len(candidates) < count and attempts < count * 5:
            attempts += 1
            config_data = {}
            for param, values in space.items():
                config_data[param] = random.choice(values)
            
            key = tuple(sorted(config_data.items()))
            if key in seen:
                continue
            if is_valid_config(config_data, project_config.constraints):
                candidates.append(CandidateConfig(params=config_data))
                seen.add(key)
                
        return candidates

class PriorGuidedSearch(SearchStrategy):
    def __init__(self, priors: list[dict[str, Any]]):
        self.priors = priors
        
    def generate(self, project_config: ProjectConfig, count: int) -> list[CandidateConfig]:
        candidates = []
        seen = set()
        for p in self.priors[:count]:
            c = p["config"]
            if "params" in c:
                params = c["params"]
            else:
                params = {k: v for k, v in c.items() if k != "extra"}
                params.update(c.get("extra", {}))
            key = tuple(sorted(params.items()))
            if key in seen:
                continue
            if is_valid_config(params, project_config.constraints):
                candidates.append(CandidateConfig(params=params))
                seen.add(key)
                
        if len(candidates) < count:
            random_search = RandomSearch()
            for candidate in random_search.generate(project_config, count - len(candidates)):
                key = tuple(sorted(candidate.params.items()))
                if key not in seen:
                    candidates.append(candidate)
                    seen.add(key)
            
        return candidates

def perturb_config(config: CandidateConfig, project_config: ProjectConfig) -> CandidateConfig:
    # Local refinement: change one parameter slightly
    new_data = dict(config.params)
    param_to_perturb = random.choice(list(project_config.search_space.keys()))
    possible_values = project_config.search_space[param_to_perturb]
    
    current_val = new_data.get(param_to_perturb)
    if current_val in possible_values:
        idx = possible_values.index(current_val)
        # Shift index by -1 or +1
        new_idx = max(0, min(len(possible_values) - 1, idx + random.choice([-1, 1])))
        new_data[param_to_perturb] = possible_values[new_idx]
    else:
        new_data[param_to_perturb] = random.choice(possible_values)
        
    if is_valid_config(new_data, project_config.constraints):
        return CandidateConfig(params=new_data)
    return config

# Backwards compatibility wrappers
def generate_random_candidates(project_config: ProjectConfig, count: int) -> list[CandidateConfig]:
    return RandomSearch().generate(project_config, count)

def generate_prior_guided_candidates(project_config: ProjectConfig, priors: list[dict[str, Any]], count: int) -> list[CandidateConfig]:
    return PriorGuidedSearch(priors).generate(project_config, count)
