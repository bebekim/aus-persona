"""Config-driven Dagster jobs for running dbt transformations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dagster import Definitions, graph, op


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DBT_JOBS_CONFIG = REPO_ROOT / "configs" / "orchestration" / "dbt_jobs.yml"


@dataclass(frozen=True)
class DbtJobConfig:
    name: str
    description: str
    command: str
    selector: str
    executable: str
    project_dir: Path
    profiles_dir: Path

    def argv(self) -> list[str]:
        return [
            self.executable,
            self.command,
            "--profiles-dir",
            str(self.profiles_dir),
            "--project-dir",
            str(self.project_dir),
            "--select",
            self.selector,
        ]


def load_dbt_job_configs(path: Path = DEFAULT_DBT_JOBS_CONFIG) -> list[DbtJobConfig]:
    raw = yaml.safe_load(path.read_text()) or {}
    dbt = raw.get("dbt") or {}
    jobs = dbt.get("jobs") or {}
    executable = dbt.get("executable", "dbt")
    project_dir = resolve_repo_path(dbt.get("project_dir", "dbt/aus_personas"))
    profiles_dir = resolve_repo_path(dbt.get("profiles_dir", "dbt/aus_personas"))

    configs: list[DbtJobConfig] = []
    for name, job in jobs.items():
        configs.append(
            DbtJobConfig(
                name=name,
                description=job.get("description", ""),
                command=job.get("command", "run"),
                selector=job["selector"],
                executable=executable,
                project_dir=project_dir,
                profiles_dir=profiles_dir,
            )
        )
    return configs


def resolve_repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO_ROOT / path


def run_dbt_job(config: DbtJobConfig) -> None:
    completed = subprocess.run(
        config.argv(),
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr)
    if completed.returncode != 0:
        raise RuntimeError(
            f"dbt {config.command} failed for selector {config.selector!r} "
            f"with exit code {completed.returncode}"
        )


def build_dbt_definitions(
    config_path: Path = DEFAULT_DBT_JOBS_CONFIG,
) -> Definitions:
    job_configs = load_dbt_job_configs(config_path)
    jobs = [build_dbt_job(config) for config in job_configs]
    return Definitions(jobs=jobs)


def build_dbt_job(config: DbtJobConfig) -> Any:
    @op(
        name=f"run_dbt_{config.name}",
        description=config.description,
        tags={
            "dbt/command": config.command,
            "dbt/selector": config.selector,
        },
    )
    def run_dbt_op() -> None:
        run_dbt_job(config)

    @graph(name=f"dbt_{config.name}", description=config.description)
    def dbt_graph() -> None:
        run_dbt_op()

    return dbt_graph.to_job(name=f"dbt_{config.name}_job")
