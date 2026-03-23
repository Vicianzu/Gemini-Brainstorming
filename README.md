# Gemini Brainstorming — Wiki Creativa

Strumenti per estrarre, filtrare e organizzare il brainstorming creativo dalle chat Gemini.

## Il Progetto

Questo repository contiene tools per trasformare le conversazioni Gemini esportate in una **wiki strutturata** per il romanzo *"I Fuochi di Sant'Elmo"* — techno-thriller ambientato a Malta nel 2046.

---

## Workflow Completo

### Step 1 — Esporta le chat da Google Takeout

1. Vai su [takeout.google.com](https://takeout.google.com)
2. Deseleziona tutto, poi seleziona solo **"Le mie attività" → "App Gemini"**
3. Esporta in formato HTML
4. Salva il file come `LeMieAttività.html` nella cartella del progetto

---

### Step 2 — Estrai le conversazioni dall'HTML

```bash
pip install -r requirements.txt
python parse_gemini.py
```

**Output:** Cartella `topics/` con file `.md` per argomento + `INDEX.md`

---

### Step 3 — Filtra con Gemini API (gratis)

Lo script `filtra_wiki_gemini.py` usa Gemini Flash (tier gratuito) per classificare automaticamente ogni coppia domanda/risposta e scartare il rumore.

#### Ottieni la API Key (gratis)

1. Vai su [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Clicca **"Create API key"**
3. Copia la chiave (inizia con `AIza...`)
4. Incollala nella riga 20 di `filtra_wiki_gemini.py`

#### Formato input richiesto

Lo script legge un file `entries.json` con questa struttura:

```json
[
  {
    "date": "2026-02-19",
    "query": "Testo del messaggio utente",
    "response": "Testo della risposta Gemini"
  }
]
```

Puoi generare questo file da `parse_gemini.py` oppure crearlo manualmente.

#### Esegui il filtro

```bash
python filtra_wiki_gemini.py
```

**Output:** `entries_filtrate.json` con solo le entry utili, classificate per categoria:

| Categoria | Descrizione |
|-----------|-------------|
| `personaggi` | Sviluppo dei personaggi |
| `tecnologia` | Tecnologia maltese, carbonio K8, fusione |
| `geopolitica` | Relazioni internazionali, CIA, Turchia, Israele |
| `trama` | Sviluppo della trama e capitoli |
| `aurora` | Agenzia Aurora e operazioni |
| `brasile` | Arco narrativo Brasile/Rio Negro |
| `tombino` | Universo alternativo "tombino" |
| `fisica` | Fisica teorica e worldbuilding scientifico |
| `livolsi` | Personaggio Livolsi e archi correlati |
| `metanarrativa` | Riflessioni sul romanzo stesso |

#### Limiti tier gratuito Gemini Flash

- ✅ 15 richieste/minuto
- ✅ 1.000.000 token/giorno
- ✅ **Completamente gratis**
- ⏱ ~4 secondi tra una chiamata e l'altra (gestito automaticamente)
- 💾 Checkpoint automatico ogni 50 entry (riprende se interrotto)

---

### Step 4 — Costruisci la Wiki

Invia `entries_filtrate.json` a un LLM (Claude, GPT-4, Gemini) per ricostruire la wiki con il materiale reale organizzato per categoria.

---

## Struttura del Repository

```
├── LeMieAttività.html          # Export HTML da Google Takeout
├── parse_gemini.py             # Step 2: estrae conversazioni → Markdown
├── filtra_wiki_gemini.py       # Step 3: filtra con Gemini API
├── requirements.txt            # Dipendenze Python
├── entries.json                # (generato) input per il filtro
├── entries_filtrate.json       # (generato) output del filtro
├── INDEX.md                    # (generato) indice dei topic
└── topics/                     # (generato) file Markdown per topic
    ├── Malta_Tecnologia.md
    ├── Personaggi.md
    └── ...
```

---

## Installazione

```bash
pip install -r requirements.txt
```