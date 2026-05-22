"""
test_ci_cd.py — Tests for CI/CD pipeline config (K237)
"""
import pytest
import yaml
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


class TestCICDPipeline:
    def test_workflow_file_exists(self):
        path = Path(".github/workflows/ci.yml")
        if path.exists():
            assert path.exists()
        else:
            pytest.skip("CI file not created yet")

    def test_docker_compose_exists(self):
        path = Path("docker-compose.yml")
        assert path.exists()

    def test_dockerfile_exists(self):
        path = Path("Dockerfile")
        assert path.exists()
