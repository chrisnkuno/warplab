import random
from typing import List, Dict, Any
from .models import CandidateConfig, ProjectConfig

def generate_random_candidates(project_config: ProjectConfig, count: int) -> List[CandidateConfig]:
    candidates = []
    space = project_config.search_space
    
    attempts = 0
    while len(candidates) < count and attempts < count * 5:
        attempts += 1
        config_data = {}
        for param, values in space.items():
            config_data[param] = random.choice(values)
        
        if is_valid_config(config_data, project_config.constraints):
            candidates.append(CandidateConfig(**config_data))
            
    return candidates

def is_valid_config(config_data: Dict[str, Any], constraints: List[str]) -> bool:
    for constraint in constraints:
        try:
            if not eval(constraint, {"__builtins__": None}, config_data):
                return False
        except Exception:
            continue
    return True

def perturb_config(config: CandidateConfig, project_config: ProjectConfig) -> CandidateConfig:
    # Local refinement: change one parameter slightly
    new_data = config.dict()
    param_to_perturb = random.choice(list(project_config.search_space.keys()))
    possible_values = project_config.search_space[param_to_perturb]
    
    current_val = new_data[param_to_perturb]
    if current_val in possible_values:
        idx = possible_values.index(current_val)
        # Shift index by -1 or +1
        new_idx = max(0, min(len(possible_values) - 1, idx + random.choice([-1, 1])))
        new_data[param_to_perturb] = possible_values[new_idx]
    else:
        new_data[param_to_perturb] = random.choice(possible_values)
        
    if is_valid_config(new_data, project_config.constraints):
        return CandidateConfig(**new_data)
    return config

def generate_prior_guided_candidates(project_config: ProjectConfig, priors: List[Dict[str, Any]], count: int) -> List[CandidateConfig]:
    candidates = []
    # Seed with top priors
    for p in priors[:count]:
        candidates.append(CandidateConfig(**p["config"]))
        
    # Fill remaining with random
    if len(candidates) < count:
        candidates.extend(generate_random_candidates(project_config, count - len(candidates)))
        
    return candidates
