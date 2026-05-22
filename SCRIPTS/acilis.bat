@echo off
chcp 65001 >nul
echo [%date% %time%] ============================ >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
echo [%date% %time%] AnatoliaX ACILIS ANALIZI (09:30) >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
echo [%date% %time%] Strateji: K68-R Ultra Erken Tespit >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
echo [%date% %time%] Hedef: Acilistan itibaren ilk 5 dk'da %6+ firsat >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
echo [%date% %time%] ============================ >> "C:\Users\feyzi\.openclaw\scripts\cron.log"

REM Gateway kontrol
curl -s http://127.0.0.1:18789/health >nul
if %errorlevel% neq 0 (
    echo [%date% %time%] Gateway kapali, baslatiliyor... >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
    start /min "" "C:\Users\feyzi\AppData\Roaming\npm\openclaw.cmd" gateway run --force
    timeout /t 8 /nobreak >nul
)

REM Browser kontrol
curl -s http://127.0.0.1:18800/json/version >nul
if %errorlevel% neq 0 (
    echo [%date% %time%] Browser kapali, baslatiliyor... >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
    start /min "" "C:\Users\feyzi\AppData\Roaming\npm\openclaw.cmd" browser --browser-profile openclaw start
    timeout /t 8 /nobreak >nul
)

echo [%date% %time%] === CANLI VERI: Bigpara (Acilis) === >> "C:\Users\feyzi\.openclaw\scripts\cron.log"

echo [%date% %time%] === AJAN B - ACILIS MOMENTUM (K68-R) === >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
"C:\Users\feyzi\AppData\Roaming\npm\openclaw.cmd" agent --agent agent2 --message "09:30 ACILIS ANALIZI - Bigpara canli borsadan BIST 100 icinde acilistan itibaren EN GUCLU momentum tasiyan hisseleri bul. Kriterler: 1) Acilis gap-up %0.1-1 arasi, 2) Ilk 1dk hacim gunluk ortalamanin uzerinde, 3) Sektorden en az 3 hisse pozitif, 4) Guclu yesil mum fitil yok. PS (Potansiyel Skoru) hesapla. SADECE PS yuksek olanlari listele. Hisse | Fiyat | Gap | PS | Hacim. Kisa rapor. Telegram'a gonder." >> "C:\Users\feyzi\.openclaw\scripts\cron.log" 2>&1
timeout /t 30 /nobreak >nul

echo [%date% %time%] === AJAN D - BREAKEVEN / POZISYON KONTROL === >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
"C:\Users\feyzi\AppData\Roaming\npm\openclaw.cmd" agent --agent agent4 --message "09:30 ACILIS RISK KONTROLU - Acik pozisyonlar icin: Eger +%5 kar varsa SL=Entry (breakeven) cek. Eger +%8 kar varsa SL=Entry+%3 cek. Kelly hesapla. Pozisyon durumlari nedir? Kisa rapor." >> "C:\Users\feyzi\.openclaw\scripts\cron.log" 2>&1
timeout /t 30 /nobreak >nul

echo [%date% %time%] === AJAN A - ACILIS KARARI === >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
"C:\Users\feyzi\AppData\Roaming\npm\openclaw.cmd" agent --agent main --message "09:30 ACILIS KARARI - B ve D raporlarini birlestir. SADECE K68-R kriterine uyan ve risk uygun olan hisseleri listele. AL / IZLE / PASS. Rapor: Hisse | PS | Entry | SL | TP | Guven. Telegram 8141424379'a gonder." >> "C:\Users\feyzi\.openclaw\scripts\cron.log" 2>&1

echo [%date% %time%] === ACILIS ANALIZI TAMAMLANDI === >> "C:\Users\feyzi\.openclaw\scripts\cron.log"
