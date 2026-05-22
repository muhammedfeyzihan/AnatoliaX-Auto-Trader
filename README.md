# AnatoliaX Trading System

**BIST (Istanbul Borsasi) icin profesyonel, cok ajanli AI trading sistemi.**

| | |
|---|---|
| **Versiyon** | 3.2 |
| **Tarih** | 2026-05-22 |
| **Ajanlar** | 3 (Sinyal / Risk / Strateji) + Telegram |
| **Test** | 801+ test, %83+ coverage |
| **Lisans** | MIT |

---

## Sistem Ozeti

AnatoliaX, BIST 30/50/100 hisseleri icin gelistirilmis event-driven, cok ajanli bir trading sistemidir.

- **Sinyal Ajan** — Teknik analiz, haber, makro veri birlestirerek aday hisse uretir.
- **Risk Ajan** — Portfoy limitleri, Kelly, R:R, korelasyon, makro rejim kontrolu yapar.
- **Strateji Ajan** — 3/3 onay mekanizmasiyla nihai karari verir.
- **Telegram Bot** — Canli raporlama, sinyal bildirimleri, portfoy ozeti.

**HFT Modulu** (v3.1) — 1-dakika ve 1-saniye momentum yakalama, tick-level backtest, latency tracking.

**Gold Mining Stratejisi** (v3.2) — Kademeli tier sistemi: MS → S1 → M1 → M5 → M15 → H1 → D1. Otomatik tier geçişi, fallback, ve 7 zaman dilimli profesyonel scalping.

**Nautilus Trader Entegrasyonu** (v3.1, opsiyonel) — Event-driven MessageBus, PreTradeRiskEngine, FillModel, InstrumentProvider patternleri.

**Enterprise Modülleri** (v3.2) — BIST regülasyon uyumluluğu, davranışsal finans kontrolleri, BIST özel slippage, gerçekçi maliyet simülasyonu, OOS validasyon, temel analiz filtresi, piyasa mikro yapısı, CVaR ensemble optimizasyonu, online learning, paper/live ayrımı, ileri trade analitikleri, gelişmiş pozisyon ölçekleme.

**Haftalık Strateji Konseyi** (v3.2) — Her cumartesi 3 ajan bir araya gelip geçen haftayı analiz eder: kazanç/zarar, en iyi setup, zaman dilimi, rejim tespiti. Matematiksel hedef çarpanı (1x→2x→4x→8x), 3/3 onay mekanizması, risk ayarlamaları ile yeni haftanın stratejisi belirlenir.

---

## Mimari

```
Veri Kaynaklari (Yahoo, TradingView, Bigpara, KAP)
         |
    FeedAggregator
         |
    +----+----+----+
    |    |    |    |
 Sinyal Risk Makro Haber
    |    |    |    |
    +----+----+----+
         |
    Strateji Ajan (3/3 onay)
         |
    +----+----+
    |         |
 Paper     Canli Emir
 Trading   (Broker API)
    |
 SQLite / PostgreSQL
```

---

## Kritik Kurallar (K1-K196)

- **K91** — TradingView birincil, Bigpara ikincil, biquote yardimci.
- **K92** — "Yalan asla yok." Her fiyat yani kaynak ve zaman damgasi.
- **K94** — Max pozisyon/hisse %2, gunluk max kayip %3, R:R min 1:2.
- **K141** — Piyasa kapali = islem yok. `BISTCalendar` kontrolu zorunlu.
- **K143** — Emir validasyonu zorunlu (`OrderValidator`).
- **K142-K148** — BIST regülasyon uyumluluğu (VBTS, devre kesici, short selling yasak).
- **K149-K154** — Davranışsal finans kontrolleri (FOMO, loss aversion, cooldown).
- **K155-K158** — BIST özel slippage modeli.
- **K159-K162** — OOS validasyon (walk-forward, overfitting tespiti).
- **K163-K166** — Temel analiz filtresi (P/E, P/B, KAP olayları).
- **K167-K170** — Piyasa mikro yapısı (order book, market impact, VWAP).
- **K171-K174** — Ensemble optimizasyonu (CVaR, korelasyon, rejim ağırlıkları).
- **K175-K178** — Online learning ve concept drift.
- **K179-K183** — Paper/live ayrımı ve Execution Quality Score.
- **K184-K188** — İleri trade analitikleri (Calmar, Omega, streak analysis).
- **K189-K192** — Gerçekçi maliyet simülasyonu (BIST, Takasbank, brokerage).
- **K193-K196** — Gelişmiş pozisyon ölçekleme (Kelly, Optimal f, vol targeting).
- **K197-K203** — Haftalık Strateji Konseyi (cumartesi toplantı, hedef çarpanı, 3/3 onay, geçmiş tecrübe birleştirme).

Tum kurallar: `KURALLAR/` dizini.

---

## Kurulum

### Gereksinimler
- Python 3.11+
- Node.js 18+ (opsiyonel)
- PostgreSQL 15+ (opsiyonel, SQLite fallback)
- Docker & Docker Compose (opsiyonel)

### Python
```bash
cd PYTHON
pip install -r requirements.txt
```

### Docker
```bash
docker-compose up -d
```

### Veritabani
```bash
python PYTHON/main.py --init-db
```

---

## Kullanim

### Sinyal Tarama
```bash
python PYTHON/main.py --scan THYAO,GARAN,ASELS
python PYTHON/main.py --scan-all
```

### Backtest
```bash
python PYTHON/main.py --backtest data/THYAO.csv --symbol THYAO
```

### Portfoy Monitörü
```bash
python PYTHON/main.py --monitor
```

### HFT Backtest
```bash
python PYTHON/main.py --hft-backtest data/ticks.csv --hft-strategy m1_momentum
```

### HFT Canli Sinyal (Demo)
```bash
python PYTHON/main.py --hft-live THYAO,GARAN,ASELS
```

### Gold Mining Kademeli Strateji
```bash
python PYTHON/main.py --gold-mining
python PYTHON/main.py --gold-scan THYAO,GARAN,ASELS --gold-tier M1 --gold-capital 50000
```

### Yeni Enterprise Modülleri
```bash
# BIST regülasyon kontrolü
python -c "from PYTHON.risk.bist_regulations import BISTRegulatoryChecker; print(BISTRegulatoryChecker().validate_trade(symbol='THYAO', price=105, reference_price=100, index_level=10000, index_previous_close=10000, orders_today=30, trades_today=10, position_value=100000, cash=25000, side='BUY'))"

# Davranışsal finans kontrolü
python -c "from PYTHON.risk.behavioral_finance import BehavioralFinanceGuard; print(BehavioralFinanceGuard().can_trade({}))"

# Temel analiz filtresi
python -c "from PYTHON.analytics.fundamental_filter import FundamentalFilter, FundamentalData; f=FundamentalFilter(); f.set_sector_benchmark('BANKA', pe=8, pb=1, ev_ebitda=6); print(f.score(FundamentalData('GARAN','BANKA',pe=7,pb=0.9,ev_ebitda=5,net_profit_growth_3y=0.1)))"

# Ensemble CVaR optimizasyonu
python -c "from PYTHON.strategy.ensemble_optimizer import EnsembleOptimizer; import pandas as pd, numpy as np; opt=EnsembleOptimizer(); df=pd.DataFrame({'a':np.random.normal(0.001,0.02,100),'b':np.random.normal(0.001,0.02,100)}); print(opt.cvar_optimize(df))"

# Paper/Live reconciliation
python -c "from PYTHON.execution.paper_live_separator import PaperLiveSeparator; sep=PaperLiveSeparator(); sep.run_paper({'symbol':'THYAO','side':'BUY','size':10,'price':100}); sep.run_live({'symbol':'THYAO','side':'BUY','size':10,'price':100}, filled_price=100.2, latency_ms=50); print(sep.reconcile())"

# OOS Walk-Forward validasyon
python -c "from PYTHON.backtest.oos_validator import OOSValidator; import pandas as pd, numpy as np; val=OOSValidator(); df=pd.DataFrame({'close':100+np.cumsum(np.random.randn(200)*0.5),'high':101+np.cumsum(np.random.randn(200)*0.5),'low':99+np.cumsum(np.random.randn(200)*0.5)}); print(val.regime_split_backtest(df, lambda d: {'sharpe':0.5}))"
```

---

## Test

```bash
cd PYTHON
pytest tests/ -v
pytest tests/ --cov=. --cov-report=html
```

---

## Guvenlik

- **Asla** API key/token kodda yazmayin — `.env` kullanin.
- `risk/secret_manager.py` ile maskeleme ve validasyon.
- gRPC TLS opsiyonel (`GRPC_TLS_CERT`, `GRPC_TLS_KEY`).
- Cache SHA-256 + pickle (ic veri, dis kaynaktan gelmez).

---

## Dosya Yapisi

```
AnatoliaX-Trading-System/
├── LICENSE
├── README.md
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── PYTHON/
│   ├── main.py                    # CLI orchestrator
│   ├── requirements.txt
│   ├── backtest/                  # Vektorize + event-driven backtest + OOS + microstructure
│   ├── paper_trading/             # Paper broker + signal engine
│   ├── hft/                       # HFT modulu (tick-level)
│   ├── data/                      # Fetcher, catalog, instrument provider
│   ├── risk/                      # Position, Account, PreTradeRiskEngine, BIST regs, behavioral, sizing
│   ├── execution/                 # UnifiedExecutionEngine, order types, paper/live separator
│   ├── agents/                    # Orchestrator, Q-learning memory, adaptive learning
│   ├── analytics/                 # Volume anomaly, BB+volume combo, fundamental filter, trade analytics
│   ├── memory/                    # ChromaDB embedding
│   ├── telegram/                  # Reporter bot
│   ├── observability/             # JSON logging, Prometheus metrics
│   ├── anatoliax_grpc/            # gRPC server/client
│   ├── adapters/                  # NautilusAdapter (opsiyonel)
│   ├── common/                    # MessageBus, events, validators
│   └── tests/                     # 792+ pytest
├── SCRIPTS/                       # Node.js motor (legacy/opsiyonel)
├── KURALLAR/                      # K1-K141 kurallar
├── AJANLAR/                       # Ajan kurallari
├── STRATEJILER/                   # Strateji dokumanlari
└── CONFIG/                        # Yapilandirma
```

---

## Katkida Bulunma

1. Fork yapin
2. Feature branch olusturun (`git checkout -b feature/xyz`)
3. Testleri calistirin (`pytest tests/`)
4. Pull Request acin

---

## Sorumluluk Reddi

Bu sistem **egitim ve arastirma** amaclidir.
- Gercek para ile kullanmadan once paper trade yapin.
- Finansal tavsiye degildir.
- Tum risk kullaniciya aittir.

---

**AnatoliaX Trading System**  
*Sadakat. Guven. Kusursuzluk.*
