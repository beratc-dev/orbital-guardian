# AETHRA – Orbital Guardian AI

Türk uyduları için TLE/SGP4 tabanlı yakınlaşma taraması yapan, uzay çöpü kataloglarını analiz eden ve hafif bir makine öğrenmesi modeliyle risk sıralaması üreten açık kaynak prototip.

## Ne yapar?
- CelesTrak üzerinden hedef uydu TLE verilerini alır.
- CelesTrak debris gruplarını indirir.
- SGP4 ile gelecek zaman penceresinde yörünge yayılımı yapar.
- Minimum yaklaşma mesafesi, en yakın yaklaşma zamanı ve göreli hızı hesaplar.
- Hafif bir ML risk modeli ile olayları önceliklendirir.
- Sonuçları CSV / JSON olarak dışa aktarır.
- İsteğe bağlı Streamlit paneli ile gösterir.

## Bilimsel not
Bu prototip, kamuya açık TLE/GP verileri ile **risk sıralaması ve yakınlaşma analizi** yapar.
Bunu, "kesin operasyonel çarpışma olasılığı" sistemi gibi sunmayın. Hackathon için doğru konumlandırma:
**yakınlaşma analizi + risk önceliklendirme + operatör karar desteği**.

## Kurulum
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

## Çalıştırma
```bash
python main.py --targets "TURKSAT 5A" "TURKSAT 5B" "GOKTURK-1" --hours 72 --step-minutes 10 --top-k 15
```

## Streamlit paneli
Önce pipeline'ı çalıştır:
```bash
python main.py --targets "TURKSAT 5A" "TURKSAT 5B" "GOKTURK-1"
```

Sonra panel:
```bash
streamlit run app/dashboard.py
```

## Çıktılar
`outputs/` klasörü altında:
- `conjunction_events.csv`
- `conjunction_events.json`
- `summary.txt`

## Önerilen repo yapısı
```text
aethra-orbital-guardian/
  README.md
  LICENSE
  requirements.txt
  main.py
  app/
    dashboard.py
  src/
    orbitguard/
      __init__.py
      data_loader.py
      propagator.py
      conjunction.py
      risk_model.py
      report.py
```

## Veri kaynakları
- CelesTrak GP/TLE API
- Açık debris grupları:
  - COSMOS 1408 Debris
  - FENGYUN 1C Debris
  - IRIDIUM 33 Debris
  - COSMOS 2251 Debris

## Uyarı
CelesTrak'a çok sık istek atmayın. Aynı veriyi birkaç dakika içinde tekrar tekrar çekmek yerine çıktı dosyalarını kullanın.
