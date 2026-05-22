"""
AnatoliaX Signal Engine (Paper Trading)
Canli veri uzerinden sinyal uretimi + risk kontrolu + sanal emir.

Kullanim:
    from PYTHON.paper_trading.signal_engine import SignalEngine
    engine = SignalEngine()
    engine.run_scan(symbols=["THYAO", "GARAN", "ASELS"])

Calisma Akisi:
    1. Canli veri cek (FeedAggregator)
    2. Indikator hesapla
    3. Sinyal skoru uret
    4. Risk kontrolu (portfoy limitleri)
    5. PaperBroker ile sanal emir ver
    6. Sinyali kaydet (PaperSignal)
    7. Telegram bildirim gonder (opsiyonel)
"""

import os
import sys
from pathlib import Path
_module_dir = Path(__file__).resolve().parent
while _module_dir.name != "PYTHON" and _module_dir.parent != _module_dir:
    _module_dir = _module_dir.parent
if _module_dir.name == "PYTHON":
    sys.path.insert(0, str(_module_dir.parent))

from datetime import datetime

import pandas as pd

from PYTHON.data.feed_aggregator import FeedAggregator
from PYTHON.data.market_calendar import BISTCalendar
from PYTHON.data.macro_fetcher import MacroFetcher
from PYTHON.data.news_fetcher import NewsFetcher
from PYTHON.backtest.indicators import apply_all
from PYTHON.backtest.signals import combined_signal
from PYTHON.paper_trading.paper_broker import PaperBroker
from PYTHON.risk.database import get_session
from PYTHON.paper_trading.models import PaperSignal
from PYTHON.manipulation.multi_tf_detector import MultiTFManipDetector
from PYTHON.manipulation.agent_trust_scorer import AgentTrustScorer
from PYTHON.manipulation.consensus_engine import ByzantineConsensus


class SignalEngine:
    """
    Canli sinyal uretim motoru.
    Paper trading aktifse sanal emir verir.
    Aktif degilse sadece sinyal kaydeder (forward test modu).
    """

    def __init__(
        self,
        paper_trading: bool | None = None,
        signal_threshold: float = 70.0,
        max_positions: int = 5,
        max_risk_pct: float = 10.0,
        enable_manipulation_check: bool = True,
    ):
        self.paper_trading = paper_trading if paper_trading is not None else (
            os.getenv("AX_PAPER_TRADING", "false").lower() == "true"
        )
        self.signal_threshold = signal_threshold
        self.max_positions = max_positions
        self.max_risk_pct = max_risk_pct
        self.feed = FeedAggregator()
        self.broker = PaperBroker(
            max_positions=max_positions,
            max_risk_pct=max_risk_pct,
        )
        self.calendar = BISTCalendar()
        self.macro_fetcher = MacroFetcher()
        self.news_fetcher = NewsFetcher()
        self._macro_cache: dict | None = None
        self._macro_cache_time: datetime | None = None
        self._news_cache: pd.DataFrame | None = None
        self._news_cache_time: datetime | None = None
        # Sinyal Ajanı — Kimi/Bulut AI entegrasyonu
        from PYTHON.ai.cloud_client import SignalAgentAI
        self.ai_signal = SignalAgentAI()
        # Manipülasyon tespiti
        self.enable_manipulation_check = enable_manipulation_check
        self.manip_detector = MultiTFManipDetector()
        self.trust_scorer = AgentTrustScorer()
        self.consensus = ByzantineConsensus()

    def _check_market_open(self) -> tuple[bool, str]:
        """Piyasa acik mi kontrol et. Tatil/haftasonu bilgisi dondur."""
        if self.calendar.is_holiday():
            return False, self.calendar.get_reason()
        if not self.calendar.is_market_open():
            return False, "BIST su an kapali (09:30-18:00 acik)"
        return True, "Piyasa acik"

    def _check_manipulation(self, symbol: str):
        """Çoklu zaman diliminde manipülasyon tespiti."""
        try:
            bars = {}
            for interval, period in [("15m", "5d"), ("1h", "15d"), ("1d", "3mo")]:
                try:
                    df = self.feed.fetch(symbol, interval=interval, period=period)
                    if df is not None and len(df) >= 30:
                        bars[interval] = df
                except Exception:
                    continue
            if not bars:
                return None
            return self.manip_detector.scan(symbol, bars=bars)
        except Exception:
            return None

    def _calculate_kelly(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """Kelly Criterion: f* = (bp - q) / b"""
        if avg_loss <= 0:
            return 0.0
        b = avg_win / avg_loss
        p = win_rate
        q = 1 - p
        f = (b * p - q) / b
        return max(-1.0, min(1.0, f))

    def _calculate_r_r(self, entry: float, sl: float, tp: float) -> float:
        """Risk/Reward orani."""
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        if risk <= 0:
            return 0.0
        return reward / risk

    def _get_macro_regime(self) -> dict:
        """Makro verileri cache ile cek, rejim skoru dondur."""
        now = datetime.now()
        if self._macro_cache is not None and self._macro_cache_time is not None:
            if (now - self._macro_cache_time).total_seconds() < 300:
                return self._macro_cache
        try:
            self._macro_cache = self.macro_fetcher.get_regime_score()
            self._macro_cache_time = now
        except Exception:
            self._macro_cache = {"regime": "NEUTRAL", "score": 1, "factors": {}}
            self._macro_cache_time = now
        return self._macro_cache

    def _get_news_sentiment(self) -> float:
        """Haber duygu analizi: -1 (negatif) ile +1 (pozitif) arasi skor."""
        now = datetime.now()
        if self._news_cache is not None and self._news_cache_time is not None:
            if (now - self._news_cache_time).total_seconds() < 300:
                df = self._news_cache
            else:
                df = None
        else:
            df = None

        if df is None:
            try:
                df = self.news_fetcher.fetch_all()
                self._news_cache = df
                self._news_cache_time = now
            except Exception:
                return 0.0

        if df.empty:
            return 0.0

        sentiments = df.get("sentiment", pd.Series([], dtype=str))
        pos = (sentiments == "positive").sum()
        neg = (sentiments == "negative").sum()
        total = len(sentiments)
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def analyze_symbol(self, symbol: str, interval: str = "1d", period: str = "3mo") -> dict | None:
        """
        Tek bir sembol icin teknik analiz + sinyal skoru.
        Returns: sinyal dict veya None (yeterli veri yoksa)
        """
        try:
            df = self.feed.fetch(symbol, interval=interval, period=period)
        except Exception as e:
            print(f"SINYAL: {symbol} veri cekilemedi: {e}")
            return None

        if len(df) < 50:
            print(f"SINYAL: {symbol} yetersiz veri ({len(df)} satir)")
            return None

        # Indikatorler
        df = apply_all(df)
        df = combined_signal(df)

        last = df.iloc[-1]
        score = last.get("SIGNAL_SCORE", 0)
        signal = last.get("Signal", 0)

        if score < self.signal_threshold or signal < 2:
            return None  # Yeterince guclu sinyal yok

        # SL / TP hesapla
        entry = last["close"]
        atr = last.get("ATR", entry * 0.03)
        sl = entry - (atr * 2)
        tp1 = entry + (atr * 3)
        tp2 = entry + (atr * 4)

        r_r = self._calculate_r_r(entry, sl, tp1)
        if r_r < 2.0:
            return None  # Kural D-3: R:R min 1:2

        # Kelly (varsayimsal)
        kelly = self._calculate_kelly(win_rate=0.6, avg_win=0.04, avg_loss=0.02)
        if kelly <= 0:
            return None  # Kelly <= 0 ise RED

        # MiroFish composite momentum score (0-100)
        rsi = last.get("RSI", 50)
        macd_hist = last.get("MACD_Hist", 0)
        bb_position = (entry - last.get("BB_Lower", entry)) / (last.get("BB_Upper", entry) - last.get("BB_Lower", entry) + 1e-9)
        mirofish = min(100, max(0, (rsi * 0.4) + (50 + macd_hist * 10) * 0.3 + (bb_position * 50) * 0.3))

        # AutoValidator: Canli fiyat dogrulamasi (K91)
        from PYTHON.data.auto_validator import AutoValidator
        validator = AutoValidator()
        validation = validator.validate_symbol(
            symbol=symbol,
            expected_price=entry,
            expected_sl=sl,
            expected_tp=tp1,
        )
        if not validation["valid"]:
            print(f"SINYAL: {symbol} dogrulama RED -> {validation['reason']}")
            return None

        # Makro rejim ve haber sentiment entegrasyonu
        macro = self._get_macro_regime()
        regime = macro.get("regime", "NEUTRAL")
        news_sentiment = self._get_news_sentiment()

        # Ayi piyasasi veya cok negatif haberler: skor dusur
        if regime == "BEAR":
            score -= 10.0
        elif regime == "NEUTRAL" and macro.get("score", 1) <= 1:
            score -= 5.0

        if news_sentiment < -0.5:
            score -= 8.0
            print(f"SINYAL: {symbol} negatif haber sentiment ({news_sentiment:.2f}), skor dusuruldu")
        elif news_sentiment < -0.2:
            score -= 4.0

        if score < self.signal_threshold:
            print(f"SINYAL: {symbol} makro/haber nedeniyle esik altina dustu ({score:.0f} < {self.signal_threshold})")
            return None

        # Manipülasyon tespiti (çoklu zaman dilimi)
        if self.enable_manipulation_check:
            manip_result = self._check_manipulation(symbol)
            if manip_result and manip_result.is_manipulated:
                score -= manip_result.threat_score * 0.5
                print(f"SINYAL: {symbol} manipülasyon tespit edildi ({manip_result.reason}), skor dusuruldu ({score:.0f})")
                if score < self.signal_threshold:
                    return None

        signal_dict = {
            "symbol": symbol,
            "score": score,
            "entry": entry,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2,
            "r_r": r_r,
            "kelly": kelly,
            "mirofish": mirofish,
            "atr": atr,
            "regime": regime,
            "macro_score": macro.get("score"),
            "news_sentiment": round(news_sentiment, 3),
            "timestamp": datetime.now(),
        }
        # Gemma AI yorumu (Sinyal Ajanı)
        ai_commentary = self.ai_signal.analyze_commentary(symbol, signal_dict)
        signal_dict["ai_commentary"] = ai_commentary
        return signal_dict

    def execute_signal(self, signal: dict) -> dict:
        """
        Sinyali isle: Paper trade ac veya sadece kaydet.
        Returns: islem sonucu dict
        """
        result = {
            "symbol": signal["symbol"],
            "signal_score": signal["score"],
            "executed": False,
            "reason": "",
            "trade_id": None,
        }

        # BIST acik mi kontrolu (K141)
        is_open, reason = self._check_market_open()
        if not is_open:
            result["reason"] = reason
            return result

        # Risk kontrolu: Max pozisyon
        open_pos = len(self.broker.get_open_positions())
        if open_pos >= self.max_positions:
            result["reason"] = "Max pozisyon limiti"
            return result

        # Risk kontrolu: Gunluk kayip
        daily_pnl = self.broker.get_daily_pnl()
        initial = self.broker.initial_capital
        if daily_pnl < -initial * (self.max_risk_pct / 100):
            result["reason"] = f"Gunluk risk limiti asildi ({daily_pnl:.2f} TL)"
            return result

        # Paper trade ac
        if self.paper_trading:
            # Pozisyon buyuklugu: Kelly bazli ama max %2
            kelly_pct = min(signal["kelly"] * 100, 2.0)
            size = (initial * (kelly_pct / 100)) / signal["entry"]
            size = int(size)

            if size <= 0:
                result["reason"] = "Pozisyon buyuklugu sifir"
                return result

            # K143: Emir validasyonu zorunlu
            from PYTHON.execution.order_validator import OrderValidator
            order_validator = OrderValidator(max_size=1_000_000.0)
            validation = order_validator.validate({
                "symbol": signal["symbol"],
                "side": "BUY",
                "size": size,
                "price": signal["entry"],
                "sl": signal["sl"],
                "tp": signal["tp1"],
            })
            if not validation["valid"]:
                result["reason"] = f"OrderValidator RED: {'; '.join(validation['errors'])}"
                return result

            trade = self.broker.place_order(
                symbol=signal["symbol"],
                side="BUY",
                size=size,
                price=signal["entry"],
                sl=signal["sl"],
                tp1=signal["tp1"],
                tp2=signal["tp2"],
                strategy="SIGNAL_ENGINE",
                agent="B",
            )

            if trade:
                result["executed"] = True
                result["trade_id"] = trade.id
                result["size"] = size
                result["entry"] = signal["entry"]
                result["reason"] = "Paper trade acildi"
            else:
                result["reason"] = "Paper broker emir RED"
        else:
            result["reason"] = "Paper trading PASIF - sinyal kaydedildi"

        # Sinyali kaydet (PaperSignal)
        session = get_session()
        ps = PaperSignal(
            symbol=signal["symbol"],
            signal_time=signal["timestamp"],
            strategy="SIGNAL_ENGINE",
            entry_price=signal["entry"],
            sl_price=signal["sl"],
            tp1_price=signal["tp1"],
            tp2_price=signal["tp2"],
            r_r=signal["r_r"],
            kelly=signal["kelly"],
            mirofish=signal["mirofish"],
            signal_score=signal["score"],
            regime=signal["regime"],
            macro_score=signal.get("macro_score"),
            news_sentiment=signal.get("news_sentiment"),
            outcome="FILLED" if result["executed"] else "PENDING",
            notes=result["reason"],
        )
        session.add(ps)
        session.commit()
        session.close()

        return result

    def run_scan(self, symbols: list[str]) -> list[dict]:
        """
        Birden fazla sembolu tara ve sinyal uret.
        Tatil/haftasonu/piyasa kapali ise bilgi ver ve cik.
        Returns: sinyal sonuclari listesi
        """
        is_open, reason = self._check_market_open()
        if not is_open:
            print(f"SINYAL: {reason}")
            return [{"market_closed": True, "reason": reason}]

        results = []
        for sym in symbols:
            signal = self.analyze_symbol(sym)
            if signal:
                result = self.execute_signal(signal)
                results.append(result)
                print(
                    f"SINYAL: {sym} | Skor: {signal['score']:.0f} | "
                    f"R:R: {signal['r_r']:.2f} | Kelly: {signal['kelly']:.3f} | "
                    f"Durum: {result['reason']}"
                )
        return results


if __name__ == "__main__":
    from PYTHON.risk.database import init_db
    init_db()
    engine = SignalEngine(paper_trading=True)
    results = engine.run_scan(["THYAO", "GARAN", "ASELS"])
    print(f"Toplam sinyal: {len([r for r in results if r['executed']])} islem acildi")
