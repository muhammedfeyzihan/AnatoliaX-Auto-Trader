# AnatoliaX Trading System

**BIST (Istanbul Borsasi) icin profesyonel, cok ajanli AI trading sistemi.**

| | |
|---|---|
| **Versiyon** | 3.2 |
| **Tarih** | 2026-05-22 |
| **Ajanlar** | 3 (Sinyal / Risk / Strateji) + Telegram |
| **Test** | 648+ test, %80+ coverage |
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

## Kritik Kurallar (K1-K141)

- **K91** — TradingView birincil, Bigpara ikincil, biquote yardimci.
- **K92** — "Yalan asla yok." Her fiyat yani kaynak ve zaman damgasi.
- **K94** — Max pozisyon/hisse %2, gunluk max kayip %3, R:R min 1:2.
- **K141** — Piyasa kapali = islem yok. `BISTCalendar` kontrolu zorunlu.
- **K143** — Emir validasyonu zorunlu (`OrderValidator`).

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
│   ├── backtest/                  # Vektorize + event-driven backtest
│   ├── paper_trading/             # Paper broker + signal engine
│   ├── hft/                       # HFT modulu (tick-level)
│   ├── data/                      # Fetcher, catalog, instrument provider
│   ├── risk/                      # Position, Account, PreTradeRiskEngine
│   ├── execution/                 # UnifiedExecutionEngine, order types
│   ├── agents/                    # Orchestrator, Q-learning memory
│   ├── analytics/               # Volume anomaly, BB+volume combo
│   ├── memory/                    # ChromaDB embedding
│   ├── telegram/                  # Reporter bot
│   ├── observability/             # JSON logging, Prometheus metrics
│   ├── anatoliax_grpc/            # gRPC server/client
│   ├── adapters/                  # NautilusAdapter (opsiyonel)
│   ├── common/                    # MessageBus, events, validators
│   └── tests/                     # 551+ pytest
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
