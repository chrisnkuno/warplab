import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .models import CandidateConfig, ProjectConfig

def is_valid_config(config_data: Dict[str, Any], constraints: List[str]) -> bool:
    for constraint in constraints:
        try:
            if not eval(constraint, {"__builtins__": None}, config_data):
                return False
        except Exception:
            continue
    return True

class SearchStrategy(ABC):
    @abstractmethod
    def generate(self, project_config: ProjectConfig, count: int) -> List[CandidateConfig]:
        pass

class RandomSearch(SearchStrategy):
    def generate(self, project_config: ProjectConfig, count: int) -> List[CandidateConfig]:
        candidates = []
        space = project_config.search_space
        
        attempts = 0
        while len(candidates) < count and attempts < count * 5:
            attempts += 1
            config_data = {}
            for param, values in space.items():
                config_data[param] = random.choice(values)
            
            if is_valid_config(config_data, project_config.constraints):
                candidates.append(CandidateConfig(params=config_data))
                
        return candidates

class PriorGuidedSearch(SearchStrategy):
    def __init__(self, priors: List[Dict[str, Any]]):
        self.priors = priors
        
    def generate(self, project_config: ProjectConfig, count: int) -> List[CandidateConfig]:
        candidates = []
        for p in self.priors[:count]:
            c = p["config"]
            if "params" in c:
                candidates.append(CandidateConfig(params=c["params"]))
            else:
                params = {k: v for k, v in c.items() if k != "extra"}
                params.update(c.get("extra", {}))
                candidates.append(CandidateConfig(params=params))
                
        if len(candidates) < count:
            random_search = RandomSearch()
            candidates.extend(random_search.generate(project_config, count - len(candidates)))
            
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
def generate_random_candidates(project_config: ProjectConfig, count: int) -> List[CandidateConfig]:
    return RandomSearch().generate(project_config, count)

def generate_prior_guided_candidates(project_config: ProjectConfig, priors: List[Dict[str, Any]], count: int) -> List[CandidateConfig]:
    return PriorGuidedSearch(priors).generate(project_config, count)
