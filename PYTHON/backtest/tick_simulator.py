"""
backtest/tick_simulator.py — Tick-Level Market Simulator (Phase 1)
Module 6 from anatoliax_prompt_v6.txt

Features:
  - Latency: L ~ LogNormal(mu, sigma)
  - Spread widening: S_stress = S_normal * (1 + beta * |dP|/sigma_P)
  - Slippage: slip = alpha1*(size/Q) + alpha2*sigma + alpha3*S
  - Queue depth decay: Q(t) = Q0 * exp(-lambda*t) + noise
  - Liquidity collapse trigger
  - Validation: |simulated_fill - live_fill| < epsilon for 95% of trades
"""

import math
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Dict


@dataclass
class TickSimulatorConfig:
    mu_latency: float = 0.0
    sigma_latency: float = 0.5
    beta_stress: float = 2.0
    alpha1: float = 0.5
    alpha2: float = 0.3
    alpha3: float = 0.2
    lambda_decay: float = 0.1
    noise_std: float = 0.05
    collapse_depth_threshold: float = 0.3
    collapse_imbalance_threshold: float = -0.7


class TickLevelMarketSimulator:
    """
    Realistic tick-level simulator with latency, slippage, spread widening, queue decay.
    """

    def __init__(self, config: TickSimulatorConfig = None):
        self.config = config or TickSimulatorConfig()
        self._validation_samples: List[Dict] = []

    def sample_latency(self) -> float:
        """L ~ LogNormal(mu, sigma)."""
        return random.lognormvariate(self.config.mu_latency, self.config.sigma_latency)

    def spread_stress(self, normal_spread: float, price_change: float, price_volatility: float) -> float:
        """S_stress = S_normal * (1 + beta * |dP|/sigma_P)."""
        if price_volatility == 0:
            return normal_spread
        return normal_spread * (1 + self.config.beta_stress * abs(price_change) / price_volatility)

    def slippage(self, order_size: float, queue_depth: float, volatility: float, spread: float) -> float:
        """slip = alpha1*(size/Q) + alpha2*sigma + alpha3*S."""
        c = self.config
        return c.alpha1 * (order_size / (queue_depth + 1e-9)) + c.alpha2 * volatility + c.alpha3 * spread

    def queue_depth_decay(self, q0: float, t: float) -> float:
        """Q(t) = Q0 * exp(-lambda*t) + noise."""
        decay = q0 * math.exp(-self.config.lambda_decay * t)
        noise = random.gauss(0, self.config.noise_std * q0)
        return max(0.0, decay + noise)

    def liquidity_collapse_trigger(self, depth: float, dQ_dt: float, imbalance: float) -> bool:
        """Trigger when dQ/dt < -threshold and IMB < -0.7."""
        return dQ_dt < -self.config.collapse_depth_threshold and imbalance < self.config.collapse_imbalance_threshold

    def simulate_fill(
        self,
        arrival_price: float,
        order_size: float,
        queue_depth: float,
        volatility: float,
        spread: float,
    ) -> Dict:
        latency = self.sample_latency()
        slip = self.slippage(order_size, queue_depth, volatility, spread)
        fill_price = arrival_price + (slip if random.random() > 0.5 else -slip)
        return {
            "fill_price": fill_price,
            "latency_ms": latency * 1000,
            "slippage": slip,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def validate(self, simulated_fill: float, live_fill: float, spread: float, epsilon_ratio: float = 0.1) -> bool:
        """|simulated_fill - live_fill| < epsilon * spread."""
        return abs(simulated_fill - live_fill) < epsilon_ratio * spread

    def record_validation(self, simulated: float, live: float, spread: float):
        self._validation_samples.append({
            "simulated": simulated,
            "live": live,
            "spread": spread,
            "valid": self.validate(simulated, live, spread),
        })

    def get_validation_stats(self) -> Dict:
        if not self._validation_samples:
            return {}
        valid_count = sum(1 for s in self._validation_samples if s["valid"])
        total = len(self._validation_samples)
        return {
            "total_samples": total,
            "valid_count": valid_count,
            "valid_pct": valid_count / total * 100,
            "mean_error": statistics.mean(abs(s["simulated"] - s["live"]) for s in self._validation_samples),
        }
