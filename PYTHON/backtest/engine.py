"""
engine.py — Pandas/NumPy tabanli backtest motoru
Deterministik, vektorize, gercekci slippage ve komisyon dahil.
Gelismis stop yonetimi (Trailing, Chandelier, Time-based) entegre.
"""
import pandas as pd
import numpy as np
from typing import Callable, Optional
from . import indicators, signals, slippage, commission, performance


class BacktestEngine:
    """
    Pandas DataFrame uzerinde calisan vektorize backtest motoru.

    Kullanim:
        engine = BacktestEngine(df, signal_func=signals.combined_signal)
        result = engine.run()
    """

    def __init__(
        self,
        df: pd.DataFrame,
        signal_func: Callable = None,
        slippage_model: slippage.SlippageModel = None,
        commission_model: commission.CommissionModel = None,
        initial_capital: float = 100_000.0,
        position_size_pct: float = 0.02,  # %2 portfoy
        sl_pct: float = 0.015,            # %1.5 SL
        tp1_pct: float = 0.01,           # %1 TP1
        tp2_pct: float = 0.02,           # %2 TP2
        tp3_pct: float = 0.03,           # %3 TP3
        max_positions: int = 5,
        daily_loss_limit: float = 0.03,  # %3 gunluk max kayip
        use_advanced_stops: bool = False,
        stop_type: str = "fixed",  # "fixed" | "trailing" | "chandelier" | "time"
        stop_params: dict | None = None,
    ):
        self.df = df.copy()
        self.signal_func = signal_func or signals.combined_signal
        self.slippage = slippage_model or slippage.SlippageModel()
        self.commission = commission_model or commission.CommissionModel()
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.sl_pct = sl_pct
        self.tp1_pct = tp1_pct
        self.tp2_pct = tp2_pct
        self.tp3_pct = tp3_pct
        self.max_positions = max_positions
        self.daily_loss_limit = daily_loss_limit
        self.use_advanced_stops = use_advanced_stops
        self.stop_type = stop_type
        self.stop_params = stop_params or {}

        self.trades = []
        self.equity_curve = []
        self.current_capital = initial_capital
        self.open_positions = []
        self.daily_pnl = 0.0
        self.current_date = None
        self._lesson_notes: list[dict] = []

    def run(self) -> dict:
        """Backtest'i calistirir."""
        self.df = self.signal_func(self.df)

        for i, row in self.df.iterrows():
            self._process_bar(i, row)

        # Acik pozisyonlari kapat
        self._close_all(row)

        trades_df = pd.DataFrame(self.trades)
        equity_df = pd.DataFrame(self.equity_curve, columns=["timestamp", "equity"]).set_index("timestamp")

        metrics = performance.calculate_all_metrics(trades_df, equity_df["equity"])
        lessons = self.generate_lessons()

        return {
            "trades": trades_df,
            "equity": equity_df,
            "metrics": metrics,
            "final_capital": self.current_capital,
            "total_return": (self.current_capital - self.initial_capital) / self.initial_capital,
            "lessons": lessons,
        }

    def _process_bar(self, idx, row):
        # Gun degisimi kontrolu
        date = pd.Timestamp(row.name).date() if isinstance(row.name, pd.Timestamp) else None
        if date and date != self.current_date:
            self.current_date = date
            self.daily_pnl = 0.0

        # Acik pozisyonlari kontrol et (SL / TP)
        self._check_exits(idx, row)

        # Yeni sinyal?
        if row.get("Signal", 0) >= 1 and len(self.open_positions) < self.max_positions:
            self._enter_position(idx, row)

        # Equity kaydet
        self.equity_curve.append((row.name, self.current_capital))

    def _enter_position(self, idx, row):
        price = row["close"]
        size = (self.current_capital * self.position_size_pct) / price

        # Liquidity check
        avg_volume = row.get("volume", size * 100)
        order_value = price * size
        if not self.slippage.check_liquidity(order_value, avg_volume, price):
            return  # Likidite yetersiz

        # Slippage uygula
        entry_price = self.slippage.apply(price, "BUY", order_value, avg_volume)
        comm = self.commission.calculate(entry_price, size)

        pos = {
            "entry_idx": idx,
            "entry_price": entry_price,
            "size": size,
            "entry_comm": comm["total"],
            "tp1_hit": False,
            "tp2_hit": False,
            "tp3_hit": False,
            "stop_type": self.stop_type,
        }

        # Gelişmiş stop entegrasyonu
        if self.use_advanced_stops:
            if self.stop_type == "trailing":
                atr = row.get("ATR", entry_price * 0.03)
                mult = self.stop_params.get("multiplier", 2.0)
                ts = __import__("PYTHON.risk.advanced_stop_manager", fromlist=["TrailingStop"]).TrailingStop(
                    entry=entry_price, atr=atr, multiplier=mult, side="BUY", step_type="atr"
                )
                pos["trailing_stop"] = ts
                pos["sl"] = ts.current_sl
            elif self.stop_type == "chandelier":
                pos["sl"] = entry_price * (1 - self.sl_pct)
            elif self.stop_type == "time":
                max_bars = self.stop_params.get("max_bars", 20)
                ts_exit = __import__("PYTHON.risk.advanced_stop_manager", fromlist=["TimeBasedExit"]).TimeBasedExit(
                    entry_time=pd.Timestamp(row.name) if isinstance(row.name, (pd.Timestamp, str)) else pd.Timestamp.now(),
                    max_bars=max_bars,
                )
                pos["time_exit"] = ts_exit
                pos["sl"] = entry_price * (1 - self.sl_pct)
            else:
                pos["sl"] = entry_price * (1 - self.sl_pct)
        else:
            pos["sl"] = entry_price * (1 - self.sl_pct)

        pos["tp1"] = entry_price * (1 + self.tp1_pct)
        pos["tp2"] = entry_price * (1 + self.tp2_pct)
        pos["tp3"] = entry_price * (1 + self.tp3_pct)

        self.open_positions.append(pos)

    def _check_exits(self, idx, row):
        price = row["close"]
        to_remove = []
        current_time = pd.Timestamp(row.name) if isinstance(row.name, (pd.Timestamp, str)) else pd.Timestamp.now()

        for pos in self.open_positions:
            # Gelişmiş stop güncelleme
            if self.use_advanced_stops and pos.get("trailing_stop"):
                ts = pos["trailing_stop"]
                new_sl = ts.update(price)
                pos["sl"] = new_sl
                if ts.is_triggered():
                    self._exit_position(idx, row, pos, "TRAILING_STOP")
                    to_remove.append(pos)
                    continue

            # Time-based exit
            if self.use_advanced_stops and pos.get("time_exit"):
                te = pos["time_exit"]
                if te.update(current_time):
                    self._exit_position(idx, row, pos, "TIME_EXIT")
                    to_remove.append(pos)
                    continue

            # SL
            if price <= pos["sl"]:
                reason = pos.get("stop_type", "SL")
                self._exit_position(idx, row, pos, reason.upper() if reason != "fixed" else "SL")
                to_remove.append(pos)
                continue

            # TP3 (en yuksek)
            if price >= pos["tp3"] and not pos["tp3_hit"]:
                self._partial_exit(idx, row, pos, 0.20, "TP3")
                pos["tp3_hit"] = True

            # TP2
            if price >= pos["tp2"] and not pos["tp2_hit"]:
                self._partial_exit(idx, row, pos, 0.30, "TP2")
                pos["tp2_hit"] = True

            # TP1
            if price >= pos["tp1"] and not pos["tp1_hit"]:
                self._partial_exit(idx, row, pos, 0.40, "TP1")
                pos["tp1_hit"] = True

            # Break-even trailing (sabit modda da TP1 sonrası SL = entry)
            if pos["tp1_hit"] and price > pos["entry_price"]:
                pos["sl"] = max(pos["sl"], pos["entry_price"])

        for pos in to_remove:
            self.open_positions.remove(pos)

    def _partial_exit(self, idx, row, pos, pct, reason):
        price = row["close"]
        size = pos["size"] * pct
        order_value = price * size
        avg_volume = row.get("volume", size * 100)
        exit_price = self.slippage.apply(price, "SELL", order_value, avg_volume)
        comm = self.commission.calculate(exit_price, size)

        gross_pnl = (exit_price - pos["entry_price"]) * size
        net_pnl = gross_pnl - comm["total"] - (pos["entry_comm"] * pct)
        self.current_capital += net_pnl
        self.daily_pnl += net_pnl

        self.trades.append({
            "entry_idx": pos["entry_idx"],
            "exit_idx": idx,
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "size": size,
            "reason": reason,
            "gross_pnl": gross_pnl,
            "net_pnl": net_pnl,
            "commission": comm["total"] + (pos["entry_comm"] * pct),
        })

    def _exit_position(self, idx, row, pos, reason):
        price = row["close"]
        size = pos["size"]
        order_value = price * size
        avg_volume = row.get("volume", size * 100)
        exit_price = self.slippage.apply(price, "SELL", order_value, avg_volume)
        comm = self.commission.calculate(exit_price, size)

        gross_pnl = (exit_price - pos["entry_price"]) * size
        net_pnl = gross_pnl - comm["total"] - pos["entry_comm"]
        self.current_capital += net_pnl
        self.daily_pnl += net_pnl

        self.trades.append({
            "entry_idx": pos["entry_idx"],
            "exit_idx": idx,
            "entry_price": pos["entry_price"],
            "exit_price": exit_price,
            "size": size,
            "reason": reason,
            "gross_pnl": gross_pnl,
            "net_pnl": net_pnl,
            "commission": comm["total"] + pos["entry_comm"],
        })

    def _close_all(self, row):
        for pos in self.open_positions[:]:
            self._exit_position(len(self.df) - 1, row, pos, "CLOSE")
        self.open_positions = []

    def generate_lessons(self) -> list[dict]:
        """
        Backtest sonuclarindan otomatik ders cikar.
        Returns: [{"pattern": str, "failure_rate": float, "suggestion": str}]
        """
        lessons = []
        if not self.trades:
            return lessons

        df_trades = pd.DataFrame(self.trades)
        if df_trades.empty:
            return lessons

        # SL erken mi tetiklendi? (TP1'e ulasmadan SL)
        sl_trades = df_trades[df_trades["reason"].isin(["SL", "TRAILING_STOP"])]
        if not sl_trades.empty:
            avg_sl_bars = (sl_trades["exit_idx"] - sl_trades["entry_idx"]).mean()
            if avg_sl_bars < 10:
                lessons.append({
                    "pattern": "Erken SL tetiklenmesi",
                    "metric": round(float(avg_sl_bars), 1),
                    "suggestion": f"SL cok dar ({avg_sl_bars:.0f} bar). ATR carpani veya SL mesafesi artirilmali.",
                })

        # TP isabet orani
        tp_trades = df_trades[df_trades["reason"].str.startswith("TP")]
        sl_count = len(sl_trades)
        tp_count = len(tp_trades)
        total_closed = sl_count + tp_count
        if total_closed > 0:
            win_rate = tp_count / total_closed
            if win_rate < 0.45:
                lessons.append({
                    "pattern": "Dusuk win rate",
                    "metric": round(win_rate * 100, 1),
                    "suggestion": f"Win rate dusuk (%{win_rate*100:.0f}). Sinyal esigi artirilmali veya trend filtre eklenmeli.",
                })
            elif win_rate > 0.65:
                lessons.append({
                    "pattern": "Yuksek win rate",
                    "metric": round(win_rate * 100, 1),
                    "suggestion": f"Win rate iyi (%{win_rate*100:.0f}). Pozisyon buyuklugu artirilabilir.",
                })

        # Komisyon etkisi
        total_comm = df_trades["commission"].sum()
        total_pnl = df_trades["net_pnl"].sum()
        if total_pnl != 0 and abs(total_comm / total_pnl) > 0.2:
            lessons.append({
                "pattern": "Yuksek komisyon etkisi",
                "metric": round(abs(total_comm / total_pnl) * 100, 1),
                "suggestion": "Komisyon PnL'nin %20'sinden fazla. Islem sayisi azaltilmali veya daha az slipajli kaynak kullanilmali.",
            })

        # Time exit analizi
        time_exits = df_trades[df_trades["reason"] == "TIME_EXIT"]
        if len(time_exits) > 3:
            avg_pnl = time_exits["net_pnl"].mean()
            if avg_pnl < 0:
                lessons.append({
                    "pattern": "Time exit zararli",
                    "metric": round(float(avg_pnl), 2),
                    "suggestion": "Zaman asimi kapanislari ortalama zararli. Max bar sayisi artirilmali veya trend gucu filtresi eklenmeli.",
                })

        self._lesson_notes = lessons
        return lessons
