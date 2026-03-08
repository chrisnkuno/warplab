import yaml
from pathlib import Path
from .models import ProjectConfig

def load_project_config(project_path: Path) -> ProjectConfig:
    config_file = project_path / "project.yaml"
    if not config_file.exists():
        raise FileNotFoundError(f"Project config not found at {config_file}")
    
    with open(config_file, "r") as f:
        data = yaml.safe_load(f)
    
    return ProjectConfig(**data)
