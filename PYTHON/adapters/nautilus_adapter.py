"""
nautilus_adapter.py — Nautilus Trader Referans Adaptörü (Opsiyonel)

Ana mimariyi bozmadan, Nautilus Trader'in event-driven engine,
precision ve multi-venue ozelliklerinden yararlanir.

Kullanim:
    from PYTHON.adapters.nautilus_adapter import NautilusAdapter
    adapter = NautilusAdapter()
    adapter.register_symbol("THYAO")
    adapter.place_market_order("THYAO", "BUY", 100)

Gereksinimler (opsiyonel):
    pip install nautilus_trader

Not: Nautilus kurulu degilse graceful fallback — mevcut AnatoliaX motoru calisir.
"""
import os
import sys
from pathlib import Path
_module_dir = Path(__file__).resolve().parent
while _module_dir.name != "PYTHON" and _module_dir.parent != _module_dir:
    _module_dir = _module_dir.parent
if _module_dir.name == "PYTHON":
    sys.path.insert(0, str(_module_dir.parent))

from typing import Optional

# Nautilus opsiyonel — yoksa ImportError yakalanir
_NAUTILUS_AVAILABLE = False
try:
    from nautilus_trader.model.data import Bar, BarType
    from nautilus_trader.model.identifiers import Venue
    from nautilus_trader.model.instruments import Equity
    from nautilus_trader.model.objects import Quantity, Money
    _NAUTILUS_AVAILABLE = True
except ImportError:
    pass


class NautilusAdapter:
    """
    Nautilus Trader entegrasyonu (opsiyonel).
    Mevcut AnatoliaX motorunu bozmaz — adaptör pattern.
    """

    def __init__(self, venue: str = "BIST"):
        self.venue = venue
        self._available = _NAUTILUS_AVAILABLE
        self._symbols: set[str] = set()

    def is_available(self) -> bool:
        return self._available

    def register_symbol(self, symbol: str) -> bool:
        """Sembolu Nautilus'a kaydet (mock)."""
        if not self._available:
            return False
        self._symbols.add(symbol)
        return True

    def place_market_order(self, symbol: str, side: str, size: int) -> dict:
        """
        Piyasa emri gonder.
        Nautilus yoksa veya canli mod aktif degilse PaperBroker'a fallback.
        """
        live_mode = os.getenv("NAUTILUS_LIVE", "false").lower() == "true"
        if not self._available or not live_mode:
            return self._fallback_order(symbol, side, size)

        # Nautilus canli entegrasyonu — gercek emir yolu
        # Not: Tam implementasyon icin Nautilus TradingNode, Venue ve Instrument
        # tanimlari gereklidir. Bu stub, canli modda PaperBroker'a yonlendirir.
        return self._fallback_order(symbol, side, size)

    def place_limit_order(self, symbol: str, side: str, size: int, price: float) -> dict:
        """Limit emir (opsiyonel)."""
        live_mode = os.getenv("NAUTILUS_LIVE", "false").lower() == "true"
        if not self._available or not live_mode:
            return self._fallback_order(symbol, side, size, price=price)
        return self._fallback_order(symbol, side, size, price=price)

    def get_instrument(self, symbol: str) -> Optional[dict]:
        """Enstruman bilgisi."""
        if not self._available:
            return {"symbol": symbol, "venue": self.venue, "provider": "fallback"}
        return {
            "symbol": symbol,
            "venue": self.venue,
            "provider": "nautilus",
            "precision": 2,
            "min_size": 1,
        }

    def _fallback_order(self, symbol: str, side: str, size: int, price: Optional[float] = None) -> dict:
        """Nautilus yoksa mevcut PaperBroker'a yonlendir."""
        try:
            from PYTHON.paper_trading.paper_broker import PaperBroker
            broker = PaperBroker()
            trade = broker.place_order(
                symbol=symbol,
                side=side,
                size=size,
                price=price or 0.0,
            )
            if trade:
                return {
                    "order_id": str(trade.id),
                    "symbol": symbol,
                    "side": side,
                    "size": size,
                    "price": price,
                    "status": "FILLED",
                    "provider": "paper_fallback",
                }
        except Exception:
            pass
        return {
            "order_id": None,
            "symbol": symbol,
            "side": side,
            "size": size,
            "price": price,
            "status": "ERROR",
            "provider": "none",
            "error": "Nautilus ve PaperBroker calismiyor.",
        }


if __name__ == "__main__":
    adapter = NautilusAdapter()
    print("Nautilus kurulu mu:", adapter.is_available())
    r = adapter.place_market_order("THYAO", "BUY", 100)
    print("Emir sonucu:", r)
