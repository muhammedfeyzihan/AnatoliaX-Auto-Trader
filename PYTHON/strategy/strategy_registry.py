"""
strategy_registry.py — Dynamic strategy loading/unloading.
K224: StrategyRegistry.
"""
import importlib
import os
import inspect
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StrategyMeta:
    name: str = ""
    version: str = "1.0"
    description: str = ""
    author: str = ""
    timeframes: List[str] = field(default_factory=list)
    params: Dict[str, Any] = field(default_factory=dict)
    module_path: str = ""
    loaded_at: Optional[datetime] = None
    instance: Optional[Any] = None


class StrategyRegistry:
    """
    Dinamik strateji kayit defteri. Stratejileri runtime'da yukle/kaldir.
    """

    def __init__(self, strategy_dir: Optional[str] = None):
        self._strategies: Dict[str, StrategyMeta] = {}
        self._strategy_dir = strategy_dir or os.path.join(os.path.dirname(__file__))

    def register(self, meta: StrategyMeta, instance: Any = None):
        """Manuel kayit."""
        meta.loaded_at = datetime.now(timezone.utc)
        if instance:
            meta.instance = instance
        self._strategies[meta.name] = meta

    def load_from_path(self, module_path: str, class_name: Optional[str] = None) -> StrategyMeta:
        """Dosya yolundan strateji yukle."""
        spec = importlib.util.spec_from_file_location("dynamic_strategy", module_path)
        if not spec or not spec.loader:
            raise ImportError(f"Modul yuklenemedi: {module_path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Auto-discover strategy class
        candidates = [name for name, obj in inspect.getmembers(mod) if inspect.isclass(obj) and "Strategy" in name]
        cls_name = class_name or (candidates[0] if candidates else None)
        if not cls_name:
            raise ValueError(f"Strateji sinifi bulunamadi: {module_path}")

        cls = getattr(mod, cls_name)
        instance = cls() if not inspect.signature(cls).parameters else cls()
        meta = StrategyMeta(
            name=getattr(instance, "NAME", cls_name),
            version=getattr(instance, "VERSION", "1.0"),
            description=getattr(instance, "DESCRIPTION", ""),
            timeframes=getattr(instance, "TIMEFRAMES", []),
            params=getattr(instance, "DEFAULT_PARAMS", {}),
            module_path=module_path,
            instance=instance,
        )
        self._strategies[meta.name] = meta
        return meta

    def load_from_module(self, module_name: str, class_name: str) -> StrategyMeta:
        """Mevcut PYTHON paketinden yukle."""
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        instance = cls()
        meta = StrategyMeta(
            name=getattr(instance, "NAME", class_name),
            version=getattr(instance, "VERSION", "1.0"),
            description=getattr(instance, "DESCRIPTION", ""),
            timeframes=getattr(instance, "TIMEFRAMES", []),
            params=getattr(instance, "DEFAULT_PARAMS", {}),
            module_path=module_name,
            instance=instance,
        )
        self._strategies[meta.name] = meta
        return meta

    def unload(self, name: str) -> bool:
        if name in self._strategies:
            del self._strategies[name]
            return True
        return False

    def get(self, name: str) -> Optional[StrategyMeta]:
        return self._strategies.get(name)

    def list_strategies(self) -> List[str]:
        return list(self._strategies.keys())

    def get_all(self) -> Dict[str, StrategyMeta]:
        return self._strategies.copy()

    def run_strategy(self, name: str, data: Any, params: Optional[Dict] = None) -> Any:
        meta = self._strategies.get(name)
        if not meta or not meta.instance:
            raise ValueError(f"Strateji bulunamadi: {name}")
        run_method = getattr(meta.instance, "run", None) or getattr(meta.instance, "execute", None)
        if not run_method:
            raise ValueError(f"Stratejide run/execute metodu yok: {name}")
        return run_method(data, params or {})

    def reset(self):
        self._strategies.clear()
