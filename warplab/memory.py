import sqlite3
import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class Memory:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
          id TEXT PRIMARY KEY,
          project_name TEXT NOT NULL,
          parent_id TEXT,
          created_at TEXT NOT NULL,
          status TEXT NOT NULL,
          gpu_name TEXT,
          compute_capability TEXT,
          cuda_version TEXT,
          driver_version TEXT,
          git_commit TEXT,
          objective_metric TEXT,
          objective_direction TEXT
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
          id TEXT PRIMARY KEY,
          run_id TEXT NOT NULL,
          config_json TEXT NOT NULL,
          compile_success INTEGER NOT NULL,
          validate_success INTEGER NOT NULL,
          benchmark_success INTEGER NOT NULL,
          score REAL,
          latency_ms REAL,
          std_ms REAL,
          cv REAL,
          speedup_vs_baseline REAL,
          FOREIGN KEY(run_id) REFERENCES runs(id)
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
          id TEXT PRIMARY KEY,
          candidate_id TEXT NOT NULL,
          metric_json TEXT NOT NULL,
          bottleneck_class TEXT,
          FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS priors (
          id TEXT PRIMARY KEY,
          kernel_signature TEXT NOT NULL,
          gpu_name TEXT NOT NULL,
          config_json TEXT NOT NULL,
          score REAL NOT NULL,
          win_count INTEGER NOT NULL DEFAULT 1,
          last_seen_at TEXT NOT NULL
        )""")
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS artifacts (
          id TEXT PRIMARY KEY,
          candidate_id TEXT NOT NULL,
          artifact_type TEXT NOT NULL,
          path TEXT NOT NULL,
          FOREIGN KEY(candidate_id) REFERENCES candidates(id)
        )""")
        
        conn.commit()
        conn.close()

    def insert_run(self, run_id: str, project_name: str, fingerprint: Dict[str, Any], objective: Dict[str, str]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runs (id, project_name, created_at, status, gpu_name, compute_capability, cuda_version, driver_version, objective_metric, objective_direction) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, project_name, fingerprint["timestamp"], "running", fingerprint["gpu_name"], fingerprint["compute_capability"], fingerprint["cuda_version"], fingerprint["driver_version"], objective["metric"], objective["direction"])
        )
        conn.commit()
        conn.close()

    def insert_candidate(self, candidate_id: str, run_id: str, config_json: str, metrics: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO candidates (id, run_id, config_json, compile_success, validate_success, benchmark_success, score, latency_ms, std_ms, cv, speedup_vs_baseline) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (candidate_id, run_id, config_json, 
             int(metrics["compile_success"]), int(metrics["validate_success"]), int(metrics["benchmark_success"]),
             metrics.get("score"), metrics.get("latency_ms"), metrics.get("std_ms"), metrics.get("cv"), metrics.get("speedup"))
        )
        conn.commit()
        conn.close()

    def get_priors(self, kernel_signature: str, gpu_name: str) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT config_json, score, win_count FROM priors WHERE kernel_signature = ? AND gpu_name = ? ORDER BY score DESC LIMIT 10",
            (kernel_signature, gpu_name)
        )
        rows = cursor.fetchall()
        conn.close()
        return [{"config": json.loads(r[0]), "score": r[1], "win_count": r[2]} for r in rows]

    def update_priors(self, kernel_signature: str, gpu_name: str, config_json: str, score: float):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute(
            "SELECT id, win_count FROM priors WHERE kernel_signature = ? AND gpu_name = ? AND config_json = ?",
            (kernel_signature, gpu_name, config_json)
        )
        row = cursor.fetchone()
        
        now = datetime.now().isoformat()
        if row:
            p_id, win_count = row
            cursor.execute(
                "UPDATE priors SET score = ?, win_count = ?, last_seen_at = ? WHERE id = ?",
                (max(score, 0), win_count + 1, now, p_id)
            )
        else:
            p_id = str(uuid.uuid4())[:8]
            cursor.execute(
                "INSERT INTO priors (id, kernel_signature, gpu_name, config_json, score, win_count, last_seen_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (p_id, kernel_signature, gpu_name, config_json, max(score, 0), 1, now)
            )
        conn.commit()
        conn.close()
