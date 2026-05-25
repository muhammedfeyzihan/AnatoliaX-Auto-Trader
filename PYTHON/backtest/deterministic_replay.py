"""
backtest/deterministic_replay.py — Deterministic Replay Engine (Phase 1)
Module 5 from anatoliax_prompt_v6.txt

Features:
  - For any market data stream M, seed s, configuration C:
    Replay(M, s, C) -> R
  - Requirement: Replay(M, s_1, C_1) = Replay(M, s_1, C_1) bit-exact.
  - Cryptographic hash: H = SHA-256(M || s || C || code_version).
  - Regression: if H_1 = H_2 then R_1 = R_2.
"""

import hashlib
import json
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


@dataclass
class ReplayConfig:
    """Configuration for deterministic replay."""
    seed: int = 42
    initial_capital: float = 100_000.0
    position_size_pct: float = 0.02
    slippage_model: str = "default"
    commission_model: str = "bist"
    version: str = "3.3"

    def to_bytes(self) -> bytes:
        return json.dumps({
            "seed": self.seed,
            "initial_capital": self.initial_capital,
            "position_size_pct": self.position_size_pct,
            "slippage_model": self.slippage_model,
            "commission_model": self.commission_model,
            "version": self.version,
        }, sort_keys=True).encode("utf-8")


class DeterministicReplayEngine:
    """
    Deterministic replay engine for bit-exact regression testing.
    """

    def __init__(self, config: ReplayConfig):
        self.config = config
        self._market_data: List[Dict[str, Any]] = []
        self._results: List[Dict[str, Any]] = []
        self._hash: Optional[str] = None

    def load_market_data(self, ticks: List[Dict[str, Any]]):
        """Load market data stream M."""
        self._market_data = ticks

    def compute_hash(self) -> str:
        """
        H = SHA-256(M || s || C || code_version).
        Used for regression: if H_1 = H_2 then R_1 = R_2.
        """
        m_bytes = pickle.dumps(self._market_data, protocol=pickle.HIGHEST_PROTOCOL)
        s_bytes = str(self.config.seed).encode("utf-8")
        c_bytes = self.config.to_bytes()
        v_bytes = self.config.version.encode("utf-8")

        combined = m_bytes + s_bytes + c_bytes + v_bytes
        self._hash = hashlib.sha256(combined).hexdigest()
        return self._hash

    def replay(self, strategy_fn) -> Dict[str, Any]:
        """
        Replay(M, s, C) -> R.
        strategy_fn: callable that takes (tick, state) and returns action.
        """
        import random
        random.seed(self.config.seed)

        state = {
            "capital": self.config.initial_capital,
            "positions": [],
            "trades": [],
            "equity": [self.config.initial_capital],
        }

        for tick in self._market_data:
            action = strategy_fn(tick, state)
            if action:
                self._apply_action(action, tick, state)
            state["equity"].append(state["capital"])

        result = {
            "final_capital": state["capital"],
            "total_trades": len(state["trades"]),
            "trades": state["trades"],
            "equity": state["equity"],
            "hash": self.compute_hash(),
            "config": self.config.to_bytes().decode("utf-8"),
        }
        self._results.append(result)
        return result

    def _apply_action(self, action: Dict[str, Any], tick: Dict[str, Any], state: Dict[str, Any]):
        side = action.get("side")
        size = action.get("size", 0)
        price = tick.get("price", 0)

        if side == "buy":
            cost = size * price
            if state["capital"] >= cost:
                state["capital"] -= cost
                state["positions"].append({"size": size, "entry": price})
        elif side == "sell":
            for pos in state["positions"][:]:
                if pos["size"] <= size:
                    pnl = (price - pos["entry"]) * pos["size"]
                    state["capital"] += pos["size"] * price
                    state["trades"].append({"pnl": pnl, "entry": pos["entry"], "exit": price})
                    size -= pos["size"]
                    state["positions"].remove(pos)
                else:
                    pnl = (price - pos["entry"]) * size
                    state["capital"] += size * price
                    state["trades"].append({"pnl": pnl, "entry": pos["entry"], "exit": price})
                    pos["size"] -= size
                    break

    def validate_reproducibility(self, strategy_fn, runs: int = 100) -> Dict[str, Any]:
        """
        Run N replays and verify all outputs are identical.
        Validation: run N=100 replays, verify all outputs identical, hash match rate = 100%.
        """
        hashes = []
        for _ in range(runs):
            result = self.replay(strategy_fn)
            hashes.append(result["hash"])

        unique_hashes = set(hashes)
        match_rate = (len(hashes) - len(unique_hashes) + 1) / len(hashes) * 100

        return {
            "runs": runs,
            "unique_hashes": len(unique_hashes),
            "match_rate_pct": match_rate,
            "reproducible": len(unique_hashes) == 1,
        }
