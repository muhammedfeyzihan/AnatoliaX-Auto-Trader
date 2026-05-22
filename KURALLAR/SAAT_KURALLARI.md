# ANATOLIAX SAAT BAZLI CALISMA KURALLARI
# Tum Ajanlar Icin Ortak Saat Gorevleri
# Versiyon: 3.0 | 20 Mayis 2026
# Yeni Yapi: 3 Ajan (Sinyal, Risk, Strateji) + Telegram

## GENEL PRENSIP
- Her saat dilimi belirli bir ajana (veya ajan grubuna) atanmistir.
- Ajanlar sadece kendi saat araliklarinda aktif olur.
- Gecikme olursa bir sonraki ajan devreye girer.

---

## ⏰ 07:00 - UYANIS / HAZIRLIK (Strateji Ajan - Hafiza/Lider)

**Gorev:** Gunu baslat, sistem kontrolu, kural hatirlama

| # | Gorev | Sorumlu | Detay |
|---|-------|---------|-------|
| 1 | Gateway kontrol | Strateji | 18789 portu acik mi? |
| 2 | Browser kontrol | Strateji | Chrome CDP 18800 acik mi? |
| 3 | Telegram bot kontrol | Strateji | @Anatoliax_bot aktif mi? |
| 4 | Gunluk memory dosyasi ac | Strateji | `memory/YYYY-MM-DD.md` olustur |
| 5 | Kural hatirlama | Strateji | Konseye K1-K141 hatirlat (ozet) |
| 6 | Dun raporlari yukle | Strateji | Win rate, performans takibi |

**Cikti:** Gunluk memory dosyasi hazir, sistem OK.

---

## ⏰ 07:30 - SAGLIK KONTROLU (K133 - Health Check)

**Katilim:** Strateji + Monitor modulu
**Hedef:** Tum modullerin durumunu kontrol et

### Akis:
```
07:30 ---- Health check calistir
         |-- Config yuklendi mi?
         |-- Risk engine calisiyor mu?
         |-- Broker bagli mi?
         |-- Data adapterlari OK mu?
         |-- Disk/RAM yeterli mi?
07:32 ---- Sonuc raporla
         |-- OK: Tum moduller calisiyor
         |-- WARN: X modul yavas
         |-- FAIL: X modul kapali -> ALERT
```

**Kural:** 3+ FAIL varsa Telegram'a alert gonder.

---

## ⏰ 09:30 - SCALPING ACILIS (Strateji - Intraday)

**Katilim:** Strateji + Sinyal (Strateji lider)
**Hedef:** 2-3 hisse, %1-2 gap momentum

### Akis:
```
09:30 ---- Acilis momentum taramasi
         |-- Strateji: Tum BIST 100, 15M gap analizi
         |-- Sinyal: 1M/5M teknik onay
         |-- Risk: Dar SL/TP risk kontrolu
09:35 ---- Karar (2dk icinde)
09:36 ---- Islem ac (varsa)
09:45 ---- Sonuc kontrolu
```

**Rapor Format:**
```
⚡ SCALPING ACILIS - 09:30
Hisse: THYAO | Setup: Gap Momentum
Entry: 150.0 | SL: 149.2 | TP1: 151.5 | TP2: 153.0
Sure: Max 15dk | Hacim: 3x
Karar: AL / PASS
```

---

## ⏰ 10:00 - SCALPING SABAH BREAKOUT (Strateji)

**Katilim:** Strateji + Sinyal
**Hedef:** 2-3 hisse, direnc kirilimi

### Akis:
```
10:00 ---- Breakout scan (15M)
10:05 ---- Setup tespit
10:07 ---- Karar
10:10 ---- Islem ac (varsa)
10:30 ---- Sonuc kontrolu
```

---

## ⏰ 11:00 - SCALPING POZISYON KONTROLU (Strateji + Risk)

**Katilim:** Strateji + Risk
**Hedef:** Aktif scalping pozisyonlarinin SL/TP guncelleme

### Akis:
```
11:00 ---- Aktif pozisyonlari kontrol et
         |-- SL tetiklendi mi?
         |-- TP1/TP2 gecildi mi?
         |-- Trailing stop guncelle
11:05 ---- Yeni setup varsa degerlendir
```

---

## ⏰ 14:00 - SCALPING OGLE REVERSAL (Strateji)

**Katilim:** Strateji + Sinyal
**Hedef:** 2 hisse, ogleden sonra donus/squeeze

### Akis:
```
14:00 ---- Reversal/squeeze scan (15M)
14:05 ---- Setup tespit
14:07 ---- Karar
14:10 ---- Islem ac (varsa)
14:30 ---- Sonuc kontrolu
```

---

## ⏰ 15:00 - SCALPING SON DALGA (Strateji)

**Katilim:** Strateji + Sinyal + Risk
**Hedef:** 2 hisse, EOD momentum

### Akis:
```
15:00 ---- EOD momentum scan (15M)
15:05 ---- Setup tespit
15:07 ---- Karar
15:10 ---- Islem ac (varsa)
15:30 ---- Pozisyonlari kapat (gece tasima YOK)
```

**Kural:** 15:30'dan sonra YENI scalping pozisyonu ACMA.

---

## ⏰ 16:30 - PERFORMANS METRIKLERI (K114-K121) + SCALPING RAPORU (Strateji + Risk)

**Katilim:** Strateji + Risk
**Hedef:** Gunluk scalping raporu + GELISMIS performans metrikleri (zorunlu)

### Akis:
```
16:30 ---- Scalping raporu derle (Strateji)
         |-- Toplam islem sayisi
         |-- Basarili/basarisiz
         |-- Net kar/zarar
         |-- Win rate
         |-- Profit factor
16:32 ---- GELISMIS METRIKLERI HESAPLA (Risk - K114-K121)
         |-- K114: Sharpe Ratio (Esik: > 1.0)
         |-- K115: Sortino Ratio (Esik: > 1.5)
         |-- K116: Max Drawdown (Esik: < %20)
         |-- K117: Expectancy (Esik: > 0)
         |-- K118: Profit Factor (Esik: > 1.5)
         |-- K119: Monte Carlo (10,000 sim, %95 CI pozitif)
         |-- K120: Walk-Forward (In/Out fark < %10)
         |-- K121: Dashboard (6/8 = ONAY, <6/8 = RED)
16:35 ---- Telegram'a gonder
```

**Scalping Rapor Format:**
```
⚡ SCALPING GUN SONU - 16:30
Islem Sayisi: 8
Basarili: 5 | Basarisiz: 3
Brut Kar: %8.5 | Brut Zarar: %2.4
Komisyon: %2.4
Net Getiri: %3.7
Win Rate: %62.5
Profit Factor: 3.54
Durum: ✅ Hedefe ulasildi / ❌ Hedefe ulasilmadi
Yarin: [Plan]
```

**Performans Metrikleri Raporu (K114-K121):**
```
📊 GUNLUK PERFORMANS METRIKLERI - 16:30
| Metrik            | Deger  | Minimum | Durum |
|-------------------|--------|---------|-------|
| Sharpe Ratio      | X.XX   | > 1.0   | ✅/❌ |
| Sortino Ratio     | X.XX   | > 1.5   | ✅/❌ |
| Max Drawdown      | %XX    | < %20   | ✅/❌ |
| Win Rate          | %XX    | > %55   | ✅/❌ |
| Profit Factor     | X.XX   | > 1.5   | ✅/❌ |
| Expectancy        | +%X.X  | > 0     | ✅/❌ |
| Monte Carlo %95   | [A%,B%]| Pozitif | ✅/❌ |
| Walk-Forward Fark | %X     | < %10   | ✅/❌ |

GENEL: X/8 ONAY -> [ONAY / SINIRLI / RED]
```

**Kural:** 6/8 metrik saglanmiyorsa scalping stratejisi DURDURULUR ve gozden gecirilir.
**Kaynak:** TradingView verisi ile hesaplanir (K91-K92).

---

## ⏰ 08:30 - SABAH STRATEJISI (Konsey Toplantisi)

**Katilim:** Sinyal, Risk (Strateji lider)
**Hedef:** 10 hisse, %6+ potansiyel

### Akis:
```
08:30 ---- Strateji uyandirir
         |-- Sinyal: Tum BIST 100 teknik tarama + haber/KAP + manipulasyon (K93 - sinir yok) -> 15 aday
         |-- Risk: Makro durum + risk analizi + matematiksel dogrulama (BIST, Dolar, ABD vadeliler, R:R, Kelly, VaR)
09:15 ---- Konsey oylamasi (3/3 onay)
09:20 ---- Strateji raporu derler
09:25 ---- Rapor Telegram'a gonderilir (8141424379)
```

**Rapor Format:**
```
SABAH STRATEJISI - 08:30
Piyasa Rejimi: [BULL/BEAR/SIDEWAYS]
Onaylanan: [5-8 hisse]
- Hisse | Entry | SL | TP | R:R | Guven | Strateji
```

---

## ⏰ 09:30 - ACILIS ANALIZI (K68-R - Ultra Erken Tespit)

**Katilim:** Sinyal (Lider), Risk
**Hedef:** Aclistan itibaren ilk 5 dakikada %6+ potansiyel yakalama

### Akis:
```
09:30 ---- Acilis verileri alinir
09:31 ---- Ilk 1dk hacim kontrolu (Sinyal)
09:32 ---- Sektör endeksi kontrol (Sinyal)
09:33 ---- PS skoru hesapla (Sinyal)
09:34 ---- Kelly pozisyon boyutu (Risk)
09:35 ---- KARAR: AL / IZLE / PASS
```

**K68-R Kriterleri (Tip A - Ultra Erken):**
- Gap-up: %0.1-1
- Hacim: Ilk 1dk > gunluk ortalama
- Sektör: En az 3 hisse ayni sektorde pozitif
- Mum: Guclu yesil mum, fitil yok

**Cikti:** Telegram'a anlik uyari (eger firsat varsa)

---

## ⏰ 10:00 - KONSEY TOPLANTISI (Strateji Lider)

**Katilim:** Sinyal, Risk, Strateji
**Hedef:** Sabah taramasi sonuclarini kesinlestir

### Akis:
- Her ajan 2dk rapor sunar
- Tartisma: 10dk
- Oylama: 3/3 onay veya RED
- Strateji listeyi kesinlestirir

**Cikti:** Kesin AL listesi (max 5 hisse)

---

## ⏰ 12:00 - OGLE GUNCELLEMESI

**Katilim:** Sinyal (Haber), Risk, Strateji (Hafiza)
**Hedef:** Acik pozisyonlari kontrol et, haberleri takip et

### Akis:
```
12:00 ---- KAP duyurulari kontrol (Sinyal)
12:05 ---- Acik pozisyon SL/TP kontrol (Risk)
12:10 ---- Hedef vs Gerceklesen karsilastirma (Strateji)
12:15 ---- Gerekirse pozisyon guncelleme onerisi
```

**Cikti:** Ogle raporu (Telegram)

---

## ⏰ 14:00 - BREAKEVEN KONTROLU (K71 - Kar Koruma)

**Katilim:** Sinyal (Teknik), Risk
**Hedef:** Acik pozisyonlarda kar koruma, SL cekme

### Kurallar:
```
Eger pozisyon +%5 kar'da:
  -> SL = Entry seviyesine (breakeven) cek
  -> %25 pozisyonu kapat (TP1)

Eger pozisyon +%8 kar'da:
  -> SL = Entry + %3 cek
  -> %25 daha kapat (TP2)

Eger pozisyon +%10 kar'da:
  -> SL = Entry + %5 cek
  -> %25 daha kapat (TP3)

Eger pozisyon +%12+ kar'da:
  -> Trailing stop aktif (EMA9 takip)
  -> Kalan %25'i tut
```

**Cikti:** SL guncelleme listesi

---

## ⏰ 15:00 - TRAILING STOP GUNCELLEME

**Katilim:** Sinyal (Teknik)
**Hedef:** TP1 gecilmis pozisyonlarda trailing stop

### Kural:
- Her +%2 kazanc -> SL %1 yukari cek
- EMA9 altinda kapanis -> CIK
- Gun sonuna kadar en az 2 kez kontrol

---

## ⏰ 16:30 - KAPANIS ONCESI KARAR

**Katilim:** Risk, Strateji (Hafiza)
**Hedef:** Gunluk portfoy durumu

### Kontrol:
- Toplam portfoy riski <%10 mu?
- Gunluk kayip <%3 mu?
- Yarinki gece pozisyonu icin aday var mi?

---

## ⏰ 17:30 - OVERNIGHT ANALIZI (K72 - Gece Swing)

**Katilim:** Sinyal, Risk (Gece konseyi)
**Hedef:** %6+ gap-up olasiligi en yuksek 3 hisse

### Akis:
```
17:30 ---- Sinyal: Tum BIST 100 (K93 - sinir yok) gun sonu momentum taramasi + KAP kapanis oncesi haber + gun sonu manipulasyon tespiti
17:32 ---- Risk: Overnight risk analizi (gap-down olasiligi) + Gap-up olasiligi matematiksel hesaplama + ABD vadeliler + global gece durumu
17:35 ---- Strateji: SADECE %70+ olasilikli hisseleri listele
```

**Cikti:** Gece pozisyon listesi (max 3 hisse, max %6 portfoy)

---

## ⏰ 17:30 - KAPANIS RAPORU

**Katilim:** Strateji (Lider/Hafiza)
**Hedef:** Gun sonu degerlendirme

### Rapor Icerigi:
```
KAPANIS RAPORU - 17:30
BIST 100: [Deger] | Degisim: [%]
Hacim: [Deger] | Ortalama: [%]

Acik Pozisyonlar:
- Hisse | Entry | Anlik | K/Z | Durum

Kapali Pozisyonlar:
- Hisse | K/Z | Strateji

Yarin Plan:
- Gece pozisyon: [Evet/Hayir]
- Beklenen acilis: [Yukari/Yan/Dusuk]

Gunun Dersi:
- [Ne ogrenildi]
```

**Cikti:** Telegram raporu + Memory dosyasi guncelleme

---

## 📋 SAAT BAZLI AJAN GOREV TABLOSU

| Saat | Gorev | Birincil Ajan | Yardimci Ajanlar |
|------|-------|---------------|------------------|
| 07:00 | Uyanis / Sistem kontrolu | Strateji | - |
| 08:30 | Sabah tarama | Sinyal, Risk | Strateji |
| 09:15 | Konsey oylamasi | Strateji | Sinyal, Risk |
| 09:30 | Acilis analizi (K68-R) | Sinyal | Risk |
| 10:00 | Konsey toplantisi | Strateji | Sinyal, Risk |
| 12:00 | Ogle guncelleme | Sinyal | Risk, Strateji |
| 14:00 | Breakeven kontrol (K71) | Risk | Sinyal |
| 15:00 | Trailing stop | Sinyal | Risk |
| 16:30 | Performans Metrikleri (K114-K141) + Scalping Rapor | Risk | Strateji |
| 17:30 | Overnight analizi (K72) | Sinyal, Risk | Strateji |
| 17:30 | Kapanis raporu | Strateji | - |

---

## ⚠️ ZAMANLAMA KRITIK KURALLARI

1. **09:30-09:35:** K68-R icin kritik. 5 dakikada karar ver.
2. **17:30-17:35:** Gece pozisyonu icin kritik. Kapanistan once bitir.
3. **14:00 Breakeven:** Her gun duzenli kontrol. Asla atla.
4. **Rapor gecikmesi:** Max 5 dk. Gecikirse ozet ver.

---

## 🔄 HAFTASONU PROGRAMI

| Gun | Saat | Gorev |
|-----|------|-------|
| **Cumartesi** | **10:00-12:00** | **HAFTALIK STRATEJI KONSEYI (K197-K203)** |
| Cumartesi | 14:00 | Strateji optimizasyonu (detayli backtest) |
| Pazar | 10:00 | Gelecek hafta plani |
| Pazar | 14:00 | Kural guncelleme (AGENTS.md) |

---

## ⏰ Cumartesi — HAFTALIK STRATEJI KONSEYI (K197-K203)

**Katilim:** Sinyal + Risk + Strateji (3 ajan zorunlu)
**Hedef:** Gecen haftayi analiz edip yeni haftanin stratejisini belirlemek

### Konsey Akisi:
```
10:00 ---- Sinyal Ajan raporu
         |-- Gecen hafta en iyi/worst setup
         |-- En karli zaman dilimi (M5/M15/H1/D1)
         |-- Win rate, toplam islem sayisi
10:15 ---- Risk Ajan raporu
         |-- Max drawdown, volatilite
         |-- Piyasa rejimi (bull/bear/sideways)
         |-- Behavioral metrikler (FOMO, loss aversion)
         |-- Consecutive loss sayisi
10:30 ---- Strateji Ajan raporu
         |-- Gecmis haftalarin analizi (4+ hafta)
         |-- Hedef carpani belirleme (1x -> 2x -> 4x -> 8x)
         |-- Birincil strateji secimi
         |-- Zaman dilimi onerisi
10:45 ---- 3/3 Onay Oylamasi
         |-- Sinyal: Win rate >= %40 ? APPROVE : REJECT
         |-- Risk: Max DD <= %5 ve vol < %30 ? APPROVE : REJECT
         |-- Strateji: Daima APPROVE
         |-- 1 RED = Onceki haftanin stratejisi korunur, carpani 0.5x
11:00 ---- Nihai Karar (CouncilDecision)
         |-- Hedef Carpani: [1x / 2x / 4x / 8x]
         |-- Birincil Strateji: [trend_following / mean_reversion / scalping]
         |-- Zaman Dilimleri: [M5 / M15 / H1 / D1]
         |-- Pozisyon Olcegi: [1.0x / 0.75x / 0.5x]
         |-- Risk Ayarlamalari
11:15 ---- Telegram raporu gonder
```

### Konsey Ciktilari:
- `CouncilDecision` JSON arsivlenir.
- Telegram'da markdown raporu yayinlanir.
- Yeni hafta Pazartesi 07:00'de yeni strateji aktif olur.

### Matematiksel Hedef Carpani:
| Onceki Hafta | Yeni Carpani | Aciklama |
|---|---|---|
| Net PnL > 0 | Carpani x2 | Kazaninca agresifles |
| Net PnL < 0 | Carpani /2 | Zararda korun |
| Net PnL = 0 | Sabit | Degismez |
| Ust sinir | 8.0 | Asla gecilmez |
| Alt sinir | 0.25 | Asla dusmez |

### Risk Ayarlamalari (K202):
- Max DD < %2  → Pozisyon 1.0x
- %2 <= DD < %5 → Pozisyon 0.75x
- DD >= %5       → Pozisyon 0.5x
- Kelly fraction: 0.25 sabit

**Kural:** Konsey toplanmazsa → Onceki strateji korunur, hedef carpani 0.5x (ultra-korumali mod).
**Kural:** 4 haftadan az gecmis varsa → Hedef carpani 1.0x sabit, strateji "balanced".

---

*Saat bazli kurallar tum ajanlar icin zorunludur.*
*Ihlal eden ajan raporu RED sayilir.*
