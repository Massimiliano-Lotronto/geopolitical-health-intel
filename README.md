# 🌍 Geopolitical Health Intelligence Dashboard

**Dashboard di intelligence geopolitica sanitaria** per monitorare digital health, AI in healthcare, regolamentazione, neurodegenerative e LMIC in tempo reale.

**Stack:** Python 3.11+ · PostgreSQL (Supabase free) · Streamlit (free) · GitHub Actions (free)

---

## 🚀 Quick Start (30 minuti)

### 1. Clona e configura ambiente
```bash
git clone https://github.com/YOUR_USER/geopolitical-health-intel.git
cd geopolitical-health-intel
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Configura database (Supabase - gratuito)
1. Vai su [supabase.com](https://supabase.com) → "Start your project" (gratis)
2. Crea un nuovo progetto (scegli regione EU per latenza)
3. Vai in **Settings → Database → Connection string → URI**
4. Copia la stringa e inseriscila nel file `.env`

### 3. Configura variabili ambiente
```bash
cp .env.template .env
# Modifica .env con i tuoi valori:
# - DATABASE_URL (da Supabase)
# - NCBI_API_KEY (opzionale ma consigliato: registrati su ncbi.nlm.nih.gov)
# - SMTP_* (per email alerts, opzionale)
```

### 4. Inizializza database
```bash
python main.py --init-db
```
Questo crea tutte le tabelle e popola fonti + keyword dal YAML.

### 5. Esegui prima raccolta dati
```bash
python main.py --skip-alerts
```

### 6. Lancia la dashboard
```bash
streamlit run dashboard/app.py
```
Apri http://localhost:8501

---

## 📂 Struttura Progetto

```
geopolitical-health-intel/
├── config/
│   ├── settings.py          # Configurazione centrale
│   ├── sources.yaml          # Catalogo fonti (22 fonti)
│   └── keywords.yaml         # Dizionario 5 livelli (120+ keyword)
├── db/
│   ├── models.py             # Modelli SQLAlchemy (11 tabelle)
│   └── init_db.py            # Inizializzazione + seed
├── collectors/
│   ├── base.py               # Classe base (fetch→parse→dedup→store)
│   ├── pubmed_collector.py   # PubMed / NCBI E-utilities
│   ├── clinicaltrials_collector.py  # ClinicalTrials.gov API v2
│   ├── bundestag_collector.py  # Bundestag DIP API
│   ├── gba_collector.py      # G-BA decisioni (RSS + scraping)
│   └── rss_collector.py      # Generico RSS (FDA, WHO, BMG, IQWiG)
├── processors/
│   ├── tagger.py             # NLP keyword matching + flags
│   └── scorer.py             # Scoring (relevance, novelty, impact, strategic)
├── alerts/
│   └── alert_engine.py       # Email alerts
├── dashboard/
│   └── app.py                # Streamlit dashboard (8 pagine)
├── .github/workflows/
│   └── pipeline.yml          # GitHub Actions (ogni 12h)
├── .streamlit/
│   └── config.toml           # Streamlit theme
├── main.py                   # Orchestratore pipeline
├── requirements.txt
├── .env.template
└── README.md
```

---

## 🗓️ Tempistica di Realizzo

### Fase 1: Setup (Giorni 1-2) ✅ PRONTO
- [x] Struttura progetto
- [x] Schema database (11 tabelle)
- [x] Configurazione fonti e keyword
- [ ] **TU:** Crea account Supabase → copia DATABASE_URL nel .env
- [ ] **TU:** Crea API key NCBI (opzionale) → copia nel .env

### Fase 2: Test Collectors (Giorni 3-5)
- [ ] Esegui `python main.py --init-db`
- [ ] Esegui `python main.py --collectors-only` e verifica dati nel DB
- [ ] Controlla logs in `pipeline.log`
- [ ] Risolvi eventuali errori su fonti specifiche

### Fase 3: Dashboard (Giorni 5-7)
- [ ] Lancia `streamlit run dashboard/app.py`
- [ ] Verifica tutte le 8 pagine
- [ ] Customizza filtri e layout se necessario

### Fase 4: Automazione (Giorni 7-10)
- [ ] Push su GitHub (repository privato)
- [ ] Configura Secrets in GitHub → Settings → Secrets
- [ ] Attiva GitHub Actions per pipeline ogni 12h
- [ ] Deploy dashboard su Streamlit Community Cloud (gratuito)

### Fase 5: Ottimizzazione (Giorni 10-14)
- [ ] Aggiungi keyword mancanti in keywords.yaml
- [ ] Calibra soglie scoring
- [ ] Configura email alerts
- [ ] Test completo end-to-end

**Tempo totale stimato: 10-14 giorni lavorativi** (2-3h/giorno)

---

## 🌐 Deploy Gratuito

### Database: Supabase (free tier)
- 500 MB storage, sufficiente per ~2 anni di dati
- PostgreSQL 15+ con API REST inclusa
- Dashboard admin per monitoraggio

### Dashboard: Streamlit Community Cloud (gratuito)
1. Push il progetto su GitHub (repository pubblico o privato)
2. Vai su [share.streamlit.io](https://share.streamlit.io)
3. Connetti il repository
4. Seleziona `dashboard/app.py` come main file
5. Aggiungi i secrets (DATABASE_URL, etc.) nella sezione Secrets

### Scheduler: GitHub Actions (gratuito)
- 2000 minuti/mese per repository privati
- Ogni esecuzione ~5-10 minuti
- 2 esecuzioni/giorno = ~300 min/mese (ben sotto il limite)

**Costo totale: €0/mese** per MVP

---

## 🔧 Comandi Utili

```bash
# Inizializza database
python main.py --init-db

# Esegui pipeline completa
python main.py

# Solo collectors (no tagging/scoring)
python main.py --collectors-only

# Pipeline senza email alerts
python main.py --skip-alerts

# Lancia dashboard locale
streamlit run dashboard/app.py

# Verifica struttura DB
python -c "from db.models import *; print([t for t in Base.metadata.tables])"
```

---

## 📊 Fonti Monitorate

| # | Fonte | Tipo | Metodo | Frequenza |
|---|-------|------|--------|-----------|
| 1 | PubMed | Scientific | API | 24h |
| 2 | ClinicalTrials.gov | Scientific | API | 24h |
| 3 | Bundestag DIP | Parliamentary | API | 12h |
| 4 | G-BA | HTA/Reimbursement | RSS | 6h |
| 5 | BfArM DiGA | Regulatory | FHIR API | 168h |
| 6 | FDA DHCOE | Regulatory | RSS | 12h |
| 7 | EC AI Act | Regulatory | RSS | 12h |
| 8 | EC EHDS | Regulatory | RSS | 12h |
| 9 | WHO Digital Health | Policy | RSS | 24h |
| 10 | BMG Germany | Policy | RSS | 24h |
| 11 | IQWiG | HTA | RSS | 168h |
| 12 | NMPA China | Regulatory | Scraping | 24h |
| 13 | Israel Innovation | Trends | Scraping | 168h |
| 14 | GSMA/ITU | Telecom | Dataset | 720h |
| 15 | Google Trends | Market | pytrends | 24h |

---

## 📝 Note

- Il progetto è progettato per essere **incrementale**: puoi partire con 3-4 fonti e aggiungerne altre nel tempo
- Lo scoring è calibrabile: modifica i pesi in `config/settings.py` e `processors/scorer.py`
- Le keyword sono in `config/keywords.yaml`: aggiungine liberamente
- I collector seguono tutti lo stesso pattern (BaseCollector): per aggiungere una nuova fonte, crea un nuovo file e implementa `fetch()` e `parse()`
