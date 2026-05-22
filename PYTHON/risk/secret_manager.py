"""
secret_manager.py — Secret Management (K137)
Token, sifre, API key'ler asla kodda degil.
.env dosyasi + os.environ + runtime override.
"""
import os
from pathlib import Path
from typing import List, Optional


class SecretManager:
    """
    Ortam degiskenlerini ve .env dosyasini yonetir.
    process.env > .env > default onceligi.
    """

    def __init__(self, env_path: str = ".env"):
        self._secrets = {}
        self._load_env_file(env_path)
        self._load_os_environ()

    def _load_env_file(self, env_path: str):
        path = Path(env_path)
        if not path.exists():
            return
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key not in self._secrets:
                    self._secrets[key] = value

    def _load_os_environ(self):
        for key, value in os.environ.items():
            self._secrets[key] = value

    def get(self, key: str, fallback: Optional[str] = None) -> str:
        val = self._secrets.get(key)
        if val is None or val == "":
            if fallback is not None:
                return fallback
            raise KeyError(f"Secret {key} bulunamadi")
        return val

    def get_safe(self, key: str, fallback: Optional[str] = None) -> Optional[str]:
        try:
            return self.get(key, fallback)
        except KeyError:
            return fallback

    def set(self, key: str, value: str):
        self._secrets[key] = value
        os.environ[key] = value

    def has(self, key: str) -> bool:
        val = self._secrets.get(key)
        return val is not None and val != ""

    def mask(self, key: str) -> str:
        val = self._secrets.get(key)
        if not val:
            return "***"
        if len(val) <= 8:
            return "***"
        return val[:3] + "..." + val[-3:]

    def validate(self, required_keys: List[str]) -> List[str]:
        missing = [k for k in required_keys if not self.has(k)]
        return missing
