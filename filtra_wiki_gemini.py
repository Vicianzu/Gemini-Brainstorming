#!/usr/bin/env python3
"""
filtra_wiki_gemini.py — Filtra le entry del brainstorming usando Gemini API (GRATIS)
Requisiti: pip install google-generativeai
Uso: python filtra_wiki_gemini.py

Limiti tier gratuito Gemini Flash:
  - 15 richieste/minuto
  - 1.000.000 token/giorno
  - Completamente gratis
"""

import json
import time
import re
from pathlib import Path
from collections import Counter

# ── CONFIGURAZIONE ────────────────────────────────────────────────────────────

API_KEY     = "AIza..."          # <-- INCOLLA QUI LA TUA GEMINI API KEY
INPUT_FILE  = "entries.json"
OUTPUT_FILE = "entries_filtrate.json"
CHECKPOINT  = "checkpoint.json"

MODEL       = "gemini-1.5-flash"  # tier gratuito
DELAY       = 4.2                 # secondi tra chiamate (max 15/min = 1 ogni 4s)

# ── PROMPT ────────────────────────────────────────────────────────────────────

SYSTEM = """Analizzi sessioni di brainstorming creativo per un romanzo fantascientifico italiano.

Il progetto: "I Fuochi di Sant'Elmo" — ambientato a Malta 2046, superpotenza tecnologica segreta.
Universi esplorati: Malta tech, Agenzia Aurora, Brasile/Rio Negro, fantascienza pura, fisica teorica, satira scientifica.

Valuta se la coppia domanda/risposta contiene materiale utile per una wiki creativa.

UTILE: worldbuilding, sviluppo personaggi, geopolitica narrativa, trame, fisica teorica, riflessioni sul romanzo.
INUTILE: "ok", "si", numeri singoli, richieste tecniche (telefoni, iptv), meme, export chat.

Rispondi SOLO con JSON valido, nient'altro:
{"utile": true/false, "categoria": "personaggi|tecnologia|geopolitica|trama|aurora|brasile|tombino|fisica|livolsi|metanarrativa|scarta", "riassunto": "max 90 caratteri se utile, stringa vuota se inutile"}"""

# ── FILTRO PRELIMINARE PYTHON (gratis, immediato) ─────────────────────────────

def is_trash(q):
    q = q.strip().lower()
    if len(q) < 8:
        return True
    trash = {
        'ok','si','sì','no','bene','vai','boh','avanti','continua','esatto',
        'perfetto','capito','grazie','certo','giusto','procedi','vabbè','vabè',
        '1','2','3','a','b','c','a e b','b e c','1 e 2','2 e 3','1 e 2 e 3',
        'entrambe le cose','si vediamo','si direi','ok capito','si esatto',
        'sì esatto', 'ok grazie', 'dai', 'andiamo', 'vai avanti', 'continua',
    }
    if q in trash:
        return True
    if re.match(r'^[abc123][\s\.\,!]*$', q):
        return True
    # Richieste chiaramente non creative
    noncreative = ['iptv','kodi','xiaomi','pixel 9','superenalotto',
                   'aggiornati alla data','mi trovi un telefono',
                   'quanto costa','che prezzo','come si installa']
    if any(t in q for t in noncreative):
        return True
    return False

# ── CHIAMATA API ──────────────────────────────────────────────────────────────

def valuta(model, entry):
    prompt = f"{SYSTEM}\n\nDOMANDA:\n{entry['query'][:300]}\n\nRISPOSTA GEMINI (preview):\n{entry.get('response','')[:350]}"
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        # Estrai JSON pulito anche se c'è markdown attorno
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'^```\s*',     '', raw)
        raw = re.sub(r'\s*```$',     '', raw)
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        # Rate limit → aspetta e riprova una volta
        if 'quota' in str(e).lower() or '429' in str(e):
            print(f"\n  Rate limit — aspetto 60 secondi...")
            time.sleep(60)
            try:
                response = model.generate_content(prompt)
                raw = response.text.strip()
                match = re.search(r'\{.*?\}', raw, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except:
                pass
        else:
            print(f"\n  Errore: {e}")
    return None

# ── CHECKPOINT ────────────────────────────────────────────────────────────────

def load_checkpoint():
    if Path(CHECKPOINT).exists():
        with open(CHECKPOINT, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed": 0, "results": []}

def save_checkpoint(processed, results):
    with open(CHECKPOINT, 'w', encoding='utf-8') as f:
        json.dump({"processed": processed, "results": results}, f, ensure_ascii=False)

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    # Controlla API key
    if API_KEY.startswith("AIza..."):
        print("=" * 55)
        print("COME OTTENERE LA GEMINI API KEY (gratis):")
        print()
        print("1. Vai su: https://aistudio.google.com/apikey")
        print("2. Clicca 'Create API key'")
        print("3. Copia la chiave (inizia con AIza...)")
        print("4. Incollala nella riga 20 di questo script")
        print("=" * 55)
        return

    try:
        import google.generativeai as genai
    except ImportError:
        print("ERRORE: libreria mancante.")
        print("Esegui: pip install google-generativeai")
        return

    # Inizializza Gemini
    import google.generativeai as genai
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel(MODEL)

    # Carica entries
    if not Path(INPUT_FILE).exists():
        print(f"ERRORE: {INPUT_FILE} non trovato.")
        print("Metti entries.json nella stessa cartella dello script.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)

    # Filtro Python preliminare
    valide = [e for e in entries if not is_trash(e['query'])]

    print(f"Entry totali:       {len(entries)}")
    print(f"Dopo filtro rapido: {len(valide)}")
    print(f"Scartate subito:    {len(entries) - len(valide)}")
    print()

    # Carica checkpoint
    cp = load_checkpoint()
    start = cp["processed"]
    results = cp["results"]

    if start > 0:
        print(f"Riprendo dal checkpoint: {start}/{len(valide)}")

    remaining = len(valide) - start
    minuti = remaining * DELAY / 60

    print(f"Da processare:      {remaining}")
    print(f"Costo:              GRATIS (Gemini Flash tier gratuito)")
    print(f"Tempo stimato:      ~{minuti:.0f} minuti")
    print()

    ok = input("Continuare? (s/n): ").strip().lower()
    if ok != 's':
        print("Annullato.")
        return

    print()
    print("Avvio — Ctrl+C per interrompere (riprende dal checkpoint)")
    print("-" * 60)

    utili = len(results)  # già salvate dal checkpoint
    scartate = start - utili

    try:
        for i, entry in enumerate(valide[start:], start=start):
            pct = (i + 1) / len(valide) * 100

            val = valuta(model, entry)

            if val and val.get('utile') == True:
                results.append({
                    'date':      entry.get('date', ''),
                    'query':     entry['query'],
                    'response':  entry.get('response', '')[:800],
                    'categoria': val.get('categoria', 'varie'),
                    'riassunto': val.get('riassunto', ''),
                })
                utili += 1
                cat = val.get('categoria', '?').ljust(14)
                print(f"[{pct:5.1f}%] ✓ {cat} {entry['query'][:55]}")
            else:
                scartate += 1
                # Mostra progresso anche per le scartate (ogni 15)
                if (i + 1) % 15 == 0:
                    print(f"[{pct:5.1f}%]   ... {utili} utili trovate finora")

            # Checkpoint ogni 50 entry
            if (i + 1) % 50 == 0:
                save_checkpoint(i + 1, results)

            time.sleep(DELAY)

    except KeyboardInterrupt:
        print("\n\nInterrotto — salvo checkpoint...")
        save_checkpoint(i, results)
        print(f"Checkpoint salvato a entry {i}. Riesegui lo script per continuare.")
        return

    # Salva output finale
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Rimuovi checkpoint
    if Path(CHECKPOINT).exists():
        Path(CHECKPOINT).unlink()

    # Report
    print()
    print("=" * 60)
    print(f"COMPLETATO")
    print(f"Entry utili:    {utili}")
    print(f"Entry scartate: {scartate}")
    print(f"Output:         {OUTPUT_FILE}")
    print()
    print("Per categoria:")
    cats = Counter(r['categoria'] for r in results)
    for cat, n in sorted(cats.items(), key=lambda x: -x[1]):
        bar = '█' * (n // 5)
        print(f"  {cat:<18} {n:3d}  {bar}")
    print()
    print("Prossimo passo: manda entries_filtrate.json a Claude")
    print("per ricostruire la wiki con il materiale reale.")

if __name__ == "__main__":
    main()
