"""
main.py — Python Orchestrator
Node.js ana motor ile birlikte calisan Python backtest, analitik ve risk modulu.
"""
import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Modul yollarini ekle
sys.path.insert(0, os.path.dirname(__file__))

from backtest import engine as bt_engine, indicators, signals, slippage, commission
from analytics import volume_anomaly, bb_volume_combo, error_analyzer, agent_scoring
from memory import chroma_store, embedder, query
from risk import database, portfolio_monitor, metrics as risk_metrics, dashboard
from data.instrument_provider import BIST_UNIVERSE
from data.feed_aggregator import FeedAggregator


def init_db():
    """Veritabanini baslatir."""
    database.init_db()
    print("[PYTHON] Veritabani baslatildi.")


def run_backtest(csv_path: str, symbol: str = "THYAO"):
    """CSV dosyasi uzerinde backtest calistirir."""
    df = pd.read_csv(csv_path, parse_dates=["timestamp"], index_col="timestamp")
    df = indicators.apply_all(df)
    df = signals.combined_signal(df)

    eng = bt_engine.BacktestEngine(
        df,
        slippage_model=slippage.SlippageModel(),
        commission_model=commission.CommissionModel(),
        initial_capital=100_000,
    )
    result = eng.run()

    print(f"\n[BACKTEST] {symbol} Sonuc:")
    print(f"  Baslangic Sermayesi: 100,000 TL")
    print(f"  Bitis Sermayesi: {result['final_capital']:.2f} TL")
    print(f"  Toplam Getiri: %{result['total_return']*100:.2f}")
    print(f"  Islem Sayisi: {len(result['trades'])}")

    # Metrikler
    m = risk_metrics.calculate_portfolio_metrics(result["trades"], result["equity"]["equity"])
    print("\n" + dashboard.cli_table(m))

    return result


def run_analytics(csv_path: str):
    """Analitik modullerini calistirir."""
    df = pd.read_csv(csv_path, parse_dates=["timestamp"], index_col="timestamp")

    # Hacim anomalisi
    df = volume_anomaly.detect_volume_anomaly(df)
    anomalies = volume_anomaly.summarize_anomalies(df)
    if not anomalies.empty:
        print(f"\n[HACIM] {len(anomalies)} anomali tespit edildi.")
        print(anomalies.head())

    # BB + Hacim kombinasyonu
    df = bb_volume_combo.detect_bb_volume_combo(df)
    combo = bb_volume_combo.summarize_signals(df)
    if not combo.empty:
        print(f"\n[BB+HACIM] {len(combo)} kombinasyon sinyali tespit edildi.")
        print(combo.head())


def run_monitor():
    """Portfoy monitörünü baslatir."""
    monitor = portfolio_monitor.PortfolioMonitor()
    summary = monitor.get_portfolio_summary()
    print("\n[PORTFOY] Ozet:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


def run_chroma_demo():
    """ChromaDB demo sorgusu calistirir."""
    print("\n[CHROMADB] Demo analiz kaydi...")
    client = chroma_store.get_client()
    collection = chroma_store.get_or_create_collection(client)

    text = embedder.build_analysis_text(
        symbol="THYAO", date="2026-05-18", price=103.0,
        ema9=102.5, ema21=100.0, rsi=62.0, macd_hist=0.5,
        bb_width=0.04, volume_z=2.8, regime="BULL", decision="AL"
    )
    emb = embedder.embed(text)
    chroma_store.add_analysis(collection, "demo_1", "THYAO", text, emb)

    results = query.find_similar_decisions(
        symbol="THYAO", date="2026-05-18", price=103.0,
        ema9=102.5, ema21=100.0, rsi=62.0, macd_hist=0.5,
        bb_width=0.04, volume_z=2.8, regime="BULL", decision="AL"
    )
    print(f"[CHROMADB] {len(results)} benzer analiz bulundu.")


def run_error_demo():
    """Hata analizi demo."""
    analyzer = error_analyzer.ErrorAnalyzer()
    analyzer.log_error(
        symbol="THYAO", agent="B", expected="YUKSEL", actual="DUS",
        market_regime="BEAR", pnl_impact=-1500, root_cause_category="makro",
        description="Makro veri beklentisi yanlis. USD/TRY ani sicrama.",
        missed_signals=["USD/TRY > 38", "VIX > 30"],
    )
    print("\n[HATA] Demo hata kaydi olusturuldu.")
    print(analyzer.analyze_patterns())


def run_scan(symbols: list[str]):
    """Canli sinyal taramasi calistir."""
    from paper_trading.signal_engine import SignalEngine
    engine = SignalEngine(paper_trading=False)  # Sadece sinyal kaydet, emir verme
    results = engine.run_scan(symbols)
    executed = [r for r in results if r.get("executed")]
    print(f"\n[TARAMA] {len(symbols)} sembol tarandi. {len(executed)} sinyal bulundu.")
    return results


def run_hft_backtest(csv_path: str, strategy: str = "m1_momentum", interval: int = 60):
    """HFT tick-level backtest calistir."""
    import pandas as pd
    from hft.backtest.hft_backtest import HFTBacktestEngine
    from hft.config import HFTConfig

    tick_df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    if "price" not in tick_df.columns:
        print("[HFT] CSV 'price' kolonu icermeli.")
        return None

    engine = HFTBacktestEngine(
        tick_df=tick_df,
        strategy=strategy,
        interval_seconds=interval,
        initial_capital=100_000.0,
    )
    result = engine.run()

    print(f"\n[HFT BACKTEST] {strategy} | {len(tick_df)} tick")
    print(f"  Baslangic: 100,000 TL")
    print(f"  Bitis: {result['final_capital']:.2f} TL")
    print(f"  Getiri: %{result['total_return']*100:.2f}")
    print(f"  Islem: {len(result['trades'])}")
    print(f"  Latency: {result['latency_stats']}")
    print(f"  Orders: {result['order_stats']}")
    return result


def run_manipulation_scan(symbols: list[str]):
    """Çoklu zaman diliminde manipülasyon taramasi."""
    from manipulation.multi_tf_detector import MultiTFManipDetector
    from data.feed_aggregator import FeedAggregator
    detector = MultiTFManipDetector()
    feed = FeedAggregator()
    results = []
    for sym in symbols:
        bars = {}
        for interval, period in [("15m", "5d"), ("1h", "15d"), ("1d", "3mo")]:
            try:
                df = feed.fetch(sym, interval=interval, period=period)
                if df is not None and len(df) >= 30:
                    bars[interval] = df
            except Exception:
                continue
        if not bars:
            print(f"[MANIP] {sym} yeterli veri yok.")
            continue
        res = detector.scan(sym, bars=bars)
        status = "MANIP" if res.is_manipulated else "TEMIZ"
        print(f"[MANIP] {sym} | {status} | Skor: {res.threat_score:.0f} | {res.reason}")
        results.append(res)
    return results


def run_agent_trust():
    """Agent trust skorlarini goster."""
    from manipulation.agent_trust_scorer import AgentTrustScorer
    scorer = AgentTrustScorer()
    scores = scorer.get_all_scores()
    print("\n[TRUST] Agent Trust Skorlari:")
    for aid, data in scores.items():
        print(f"  {aid}: {data['trust_score']:.1f} (success={data['win_rate']:.2f}, threats={data['threat_count']})")
    top = scorer.get_top_agents(n=5)
    if top:
        print("\n  Top 5:")
        for t in top:
            print(f"    {t['agent_id']}: {t['trust_score']:.1f}")
    return scores


def run_hft_live(symbols: list[str], strategy: str = "m1_momentum"):
    """HFT canli sinyal uretimi (simulated feed ile demo)."""
    import pandas as pd
    from hft.config import HFTConfig
    from hft.tick_aggregator import TickAggregator
    from hft.signal_generator import generate_signal_from_df
    from hft.risk_filter import RiskFilter
    from hft.position_manager import HFTPositionManager
    from hft.order_manager import HFTOrderManager
    from hft.latency_tracker import LatencyTracker
    from hft.broker_feed import SimulatedBrokerFeed
    from risk.account import Account

    config = HFTConfig(timeframe="1m", symbols=symbols)
    account = Account(initial_cash=100_000.0, max_position_value_pct=1.0)
    pos_mgr = HFTPositionManager(account)
    order_mgr = HFTOrderManager()
    risk = RiskFilter()
    latency = LatencyTracker()
    aggregator = TickAggregator(interval_seconds=60)

    # Simulated feed: fetch last bars from FeedAggregator
    feed = FeedAggregator()
    bars_dict = {}
    for sym in symbols:
        try:
            df = feed.fetch(sym, interval="1m", period="1d")
            if df is not None and len(df) >= 30:
                bars_dict[sym] = df
        except Exception as e:
            print(f"[HFT] {sym} veri hatasi: {e}")

    if not bars_dict:
        print("[HFT] Yeterli veri yok.")
        return []

    signals_found = []
    for sym, df in bars_dict.items():
        sig = generate_signal_from_df(df, strategy=strategy)
        if sig and sig.get("signal", 0) != 0:
            signals_found.append({"symbol": sym, "signal": sig})
            print(f"[HFT] {sym} | signal={sig['signal']} | entry={sig.get('entry', 0):.2f}")

    print(f"\n[HFT LIVE] {len(symbols)} sembol | {len(signals_found)} sinyal")
    return signals_found


def run_gold_mining(symbols: list[str], tier: str | None = None, capital: float = 100_000.0):
    """Gold Mining kademeli stratejisini calistir."""
    from strategy.gold_mining.orchestrator import GoldMiningOrchestrator, GoldMiningState
    from data.feed_aggregator import FeedAggregator

    state = GoldMiningState(current_tier_name=tier or "MS")
    engine = GoldMiningOrchestrator(initial_capital=capital, state=state)
    feed = FeedAggregator()

    def provider(sym, interval):
        try:
            return feed.fetch(sym, interval=interval, period="1d")
        except Exception:
            return None

    print(f"\n[GOLD MINING] Baslangic: {capital:,.0f} TL | Tier: {engine.state.current_tier_name}")
    results = engine.run_scan(symbols, provider)

    executed = [r for r in results if r.get("executed")]
    print(f"[GOLD MINING] {len(symbols)} sembol | {len(executed)} islem acildi")
    for r in executed:
        sig = r.get("signal", {})
        print(f"  {r['symbol']} | {sig.get('side','')} @ {sig.get('entry',0):.2f} | Tier: {r['tier']} | Agents: {r['agents_active']}")

    print(f"[GOLD MINING] Durum: {engine.state.to_dict()}")
    return results


def main():
    parser = argparse.ArgumentParser(description="AnatoliaX Python Modulu")
    parser.add_argument("--init-db", action="store_true", help="Veritabanini baslat")
    parser.add_argument("--backtest", type=str, metavar="CSV", help="Backtest calistir")
    parser.add_argument("--symbol", type=str, default="THYAO", help="Hisse sembolu")
    parser.add_argument("--analytics", type=str, metavar="CSV", help="Analitik calistir")
    parser.add_argument("--monitor", action="store_true", help="Portfoy monitörü")
    parser.add_argument("--chroma-demo", action="store_true", help="ChromaDB demo")
    parser.add_argument("--error-demo", action="store_true", help="Hata analizi demo")
    parser.add_argument("--all-demos", action="store_true", help="Tum demolar")
    parser.add_argument("--scan-all", action="store_true", help="BIST universe tum sembolleri tara")
    parser.add_argument("--scan", type=str, metavar="SYMBOLS", help="Virgulle ayrilmis sembol listesi (ornek: THYAO,GARAN,ASELS)")
    parser.add_argument("--hft-backtest", type=str, metavar="CSV", help="HFT tick-level backtest calistir")
    parser.add_argument("--hft-strategy", type=str, default="m1_momentum", choices=["m1_momentum", "s1_micro_scalp"], help="HFT stratejisi")
    parser.add_argument("--hft-interval", type=int, default=60, help="HFT bar araligi (saniye)")
    parser.add_argument("--hft-live", type=str, metavar="SYMBOLS", help="HFT canli sinyal (virgulle ayrilmis semboller)")
    parser.add_argument("--add-user", type=str, metavar="NAME", help="Yeni kullanici ekle (sifre sorulur)")
    parser.add_argument("--list-users", action="store_true", help="Kullanici listesini goster")

    parser.add_argument("--manipulation-scan", type=str, metavar="SYMBOLS", help="Manipülasyon taramasi (virgulle ayrilmis semboller)")
    parser.add_argument("--agent-trust", action="store_true", help="Agent trust skorlarini goster")

    parser.add_argument("--gold-mining", action="store_true", help="Gold Mining kademeli stratejisini calistir")
    parser.add_argument("--gold-tier", type=str, default=None, choices=["MS", "S1", "M1", "M5", "M15", "H1", "D1"], help="Gold Mining baslangic tier'i (varsayilan: MS)")
    parser.add_argument("--gold-capital", type=float, default=100_000.0, help="Gold Mining baslangic sermayesi")
    parser.add_argument("--gold-scan", type=str, metavar="SYMBOLS", help="Gold Mining sembol listesi (virgulle ayrilmis)")

    args = parser.parse_args()

    if args.add_user:
        from auth.rbac import RBACManager
        from auth.demo_user import add_user_cli
        import getpass
        rbac = RBACManager()
        role = input("Rol (trader/viewer/admin): ").strip() or "trader"
        pw = getpass.getpass("Sifre: ")
        ok = add_user_cli(rbac, args.add_user, role, pw)
        print("[AUTH] Kullanici eklendi." if ok else "[AUTH] Kullanici zaten var.")

    if args.list_users:
        from auth.rbac import RBACManager
        rbac = RBACManager()
        print("Kullanicilar:", rbac.list_users())

    if args.init_db:
        init_db()

    if args.backtest:
        run_backtest(args.backtest, args.symbol)

    if args.analytics:
        run_analytics(args.analytics)

    if args.monitor:
        run_monitor()

    if args.chroma_demo:
        run_chroma_demo()

    if args.error_demo:
        run_error_demo()

    if args.all_demos:
        init_db()
        run_monitor()
        run_chroma_demo()
        run_error_demo()
        print("\n[PYTHON] Tum demolar tamamlandi.")

    if args.scan_all:
        run_scan(BIST_UNIVERSE)

    if args.scan:
        symbols = [s.strip().upper() for s in args.scan.split(",")]
        run_scan(symbols)

    if args.hft_backtest:
        run_hft_backtest(args.hft_backtest, strategy=args.hft_strategy, interval=args.hft_interval)

    if args.hft_live:
        symbols = [s.strip().upper() for s in args.hft_live.split(",")]
        run_hft_live(symbols, strategy=args.hft_strategy)

    if args.manipulation_scan:
        symbols = [s.strip().upper() for s in args.manipulation_scan.split(",")]
        run_manipulation_scan(symbols)

    if args.agent_trust:
        run_agent_trust()

    if args.gold_mining or args.gold_scan:
        symbols = [s.strip().upper() for s in args.gold_scan.split(",")] if args.gold_scan else BIST_UNIVERSE
        run_gold_mining(symbols, tier=args.gold_tier, capital=args.gold_capital)

    if len(sys.argv) == 1:
        parser.print_help()


if __name__ == "__main__":
    main()
