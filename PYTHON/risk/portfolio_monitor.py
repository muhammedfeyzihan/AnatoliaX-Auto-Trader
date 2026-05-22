"""
portfolio_monitor.py — Gercek zamanli portfoy takibi
Alarm: gunluk kayip > %3, tek hisse > %2, korelasyon > 0.80
"""
import pandas as pd
from datetime import datetime, date, timezone
from typing import List, Dict
from .database import get_session
from .models import Trade, DailyStats


class PortfolioMonitor:
    """Canli portfoy risk monitörü."""

    def __init__(self, session=None, capital: float = 100_000.0):
        self.session = session or get_session()
        self.capital = capital
        self.limits = {
            "daily_loss_pct": 0.03,
            "max_position_pct": 0.02,
            "max_correlation": 0.80,
            "max_positions": 5,
        }
        self.alerts = []

    def record_trade(self, symbol: str, side: str, size: float, price: float,
                     commission: float = 0.0, bsmv: float = 0.0,
                     strategy: str = "", agent: str = "") -> Trade:
        """Yeni islem kaydeder."""
        trade = Trade(
            symbol=symbol.upper(),
            side=side.upper(),
            size=size,
            entry_price=price,
            commission=commission,
            bsmv=bsmv,
            strategy=strategy,
            agent=agent,
        )
        self.session.add(trade)
        self.session.commit()
        return trade

    def close_trade(self, trade_id: int, exit_price: float, exit_commission: float = 0.0, reason: str = "") -> Trade:
        """Islemi kapatir."""
        trade = self.session.query(Trade).filter_by(id=trade_id).first()
        if not trade:
            return None
        trade.exit_price = exit_price
        trade.exit_time = datetime.now(timezone.utc)
        trade.status = "CLOSED"
        trade.gross_pnl = (exit_price - trade.entry_price) * trade.size
        trade.commission += exit_commission
        trade.net_pnl = trade.gross_pnl - trade.commission - trade.bsmv
        trade.reason = reason
        self.session.commit()
        return trade

    def get_open_positions(self) -> List[Trade]:
        """Acik pozisyonlari listeler."""
        return self.session.query(Trade).filter_by(status="OPEN").all()

    def get_portfolio_summary(self) -> Dict:
        """Portfoy ozetini dondurur."""
        open_pos = self.get_open_positions()
        today = date.today().isoformat()

        today_trades = self.session.query(Trade).filter(
            Trade.entry_time >= f"{today} 00:00:00"
        ).all()

        daily_pnl = sum(t.net_pnl for t in today_trades if t.net_pnl is not None)
        total_exposure = sum(p.entry_price * p.size for p in open_pos)

        return {
            "open_positions": len(open_pos),
            "total_exposure": total_exposure,
            "daily_pnl": daily_pnl,
            "daily_pnl_pct": daily_pnl / self.capital if self.capital > 0 else None,
            "alerts": self._check_limits(open_pos, daily_pnl),
        }

    def _check_limits(self, open_pos: List[Trade], daily_pnl: float) -> List[str]:
        """Limit kontrolleri, alarm uretir."""
        alerts = []

        # Gunluk kayip limiti
        if daily_pnl < -self.limits["daily_loss_pct"] * self.capital:
            alerts.append(f"DAILY LOSS LIMIT: {daily_pnl:.2f} TL")

        # Tek hisse limiti
        symbols = {}
        for p in open_pos:
            symbols[p.symbol] = symbols.get(p.symbol, 0) + (p.entry_price * p.size)
        for sym, exp in symbols.items():
            if exp > self.limits["max_position_pct"] * self.capital:
                alerts.append(f"POSITION LIMIT: {sym} {exp:.2f} TL")

        # Korelasyon limiti (placeholder — gercek hesaplama icin getiri serisi gerekli)
        if len(symbols) > self.limits["max_positions"]:
            alerts.append(f"MAX POSITIONS: {len(symbols)}/{self.limits['max_positions']}")

        return alerts

    def end_of_day(self, capital: float, regime: str = ""):
        """Gun sonu istatistikleri kaydeder."""
        today = date.today().isoformat()
        stats = self.session.query(DailyStats).filter_by(date=today).first()
        if stats:
            stats.ending_capital = capital
            self.session.commit()
            return stats

        # Hesapla
        trades = self.session.query(Trade).filter(
            Trade.entry_time >= f"{today} 00:00:00"
        ).all()
        wins = [t for t in trades if t.net_pnl and t.net_pnl > 0]
        losses = [t for t in trades if t.net_pnl and t.net_pnl <= 0]

        stats = DailyStats(
            date=today,
            starting_capital=capital,  # gercek deger disaridan verilmeli
            ending_capital=capital,
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            gross_profit=sum(t.net_pnl for t in wins),
            gross_loss=sum(t.net_pnl for t in losses),
            commission_total=sum(t.commission for t in trades),
            regime=regime,
        )
        self.session.add(stats)
        self.session.commit()
        return stats
