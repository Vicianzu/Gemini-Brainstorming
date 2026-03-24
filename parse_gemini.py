#!/usr/bin/env python3
"""
parse_gemini.py

Reads LeMieAttività.html (Google Takeout export of Gemini activity),
extracts all conversations, groups them by topic, and generates:
  - topics/<TopicName>.md  (one file per topic)
  - INDEX.md               (index of all topics and conversations)
"""

import os
import re
import sys
import unicodedata
from collections import defaultdict, Counter

from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Stop words to ignore when extracting topic keywords
# ---------------------------------------------------------------------------
STOP_WORDS = {
    # Italian – articles, prepositions, conjunctions
    "di", "il", "la", "lo", "le", "gli", "un", "una", "uno", "i",
    "del", "della", "dello", "dei", "delle", "degli", "dell",
    "dal", "dalla", "dallo", "dai", "dalle", "dagli",
    "nel", "nella", "nello", "nei", "nelle", "negli",
    "sul", "sulla", "sullo", "sui", "sulle", "sugli",
    "al", "alla", "allo", "ai", "alle", "agli",
    "col", "coi", "con", "tra", "fra", "per", "da", "su", "in", "a", "e", "o",
    "ma", "ed", "ne", "ci", "si",
    # Italian – pronouns
    "io", "tu", "lui", "lei", "noi", "voi", "loro",
    "mi", "ti", "lo", "la", "li", "le", "ci", "vi",
    "me", "te", "se", "mio", "mia", "miei", "mie",
    "tuo", "tua", "tuoi", "tue", "suo", "sua", "suoi", "sue",
    "nostro", "nostra", "nostri", "nostre",
    "vostro", "vostra", "vostri", "vostre",
    "questo", "questa", "questi", "queste", "quel", "quella", "quelli", "quelle",
    "quello", "chi", "che", "cui", "quale", "quali",
    # Italian – common verbs / auxiliaries / gerunds
    "ho", "ha", "hai", "abbiamo", "avete", "hanno",
    "sono", "sei", "sta", "siamo", "siete", "essere", "avere",
    "era", "erano", "stato", "stata", "stati", "state",
    "fare", "fatto", "fatta", "faccio", "fai", "fa", "facciamo",
    "posso", "puoi", "puo", "può", "possiamo", "possono",
    "devo", "devi", "deve", "dobbiamo", "dovete", "devono",
    "vuoi", "vuole", "voglio", "vogliamo", "vogliono", "vorrei",
    "viene", "vieni", "vengo", "vediamo", "vedo", "vedi", "vede", "vedere",
    "dico", "dici", "dice", "diciamo", "dite", "dicono", "dire",
    "so", "sai", "sa", "sappiamo", "sapete", "sanno",
    "sto", "stai", "stiamo", "stanno", "stare",
    "vai", "va", "andiamo", "andate", "vanno", "andare",
    "metti", "mette", "mettiamo", "genera", "genero",
    "bisogna", "occorre", "serve", "sembrano",
    "analizza", "analizzare", "analizziamo",
    "capire", "capisce", "capisco",
    "succede", "succedere", "successo",
    "immagino", "immagina", "immaginare", "immaginato",
    "vado", "prendo", "prendere", "preso", "prende",
    "fanno", "farsi", "farlo", "far",
    "viene", "venire", "venuto",
    "sarebbe", "sarebbero",
    "arriva", "arrivano", "arrivare",
    "inizia", "iniziano", "iniziare",
    "lascia", "lasciano", "lasciare",
    "manda", "mandano", "mandare",
    "passa", "passano", "passare",
    "decide", "decidono", "decidere",
    "diventa", "diventano", "diventare",
    "chiama", "chiamano", "chiamare",
    "chiede", "chiedono", "chiedere",
    "torniamo", "tornare", "torna",
    "pensano", "pensare", "pensa",
    "parlare", "parla", "parlano",
    "sembra", "sembrano", "sembrare",
    "funziona", "funzionano", "funzionare",
    # Italian – common adverbs / adjectives / conjunctions
    "non", "se", "come", "cosa", "quando", "dove", "perche", "perché",
    "perchè", "mentre", "oppure", "allora", "poi", "già", "qui",
    "li", "qua", "dopo", "prima", "sempre", "mai", "ogni",
    "ancora", "anche", "tutto", "tutti", "tutte", "molto", "più", "meno",
    "cosi", "così", "però", "quindi", "dunque",
    "ecco", "ok", "beh", "bene", "male", "no", "si", "sì",
    "solo", "sola", "soli", "sole", "stesso", "stessa", "stessi", "stesse",
    "altro", "altra", "altri", "altre",
    "nuovo", "nuova", "nuovi", "nuove",
    "grande", "piccolo", "vecchio", "lungo", "breve", "meglio",
    "tutta", "nulla", "niente", "nessuno", "nessuna", "nessun",
    "adesso", "ora", "subito", "presto", "tardi",
    "anni", "anno", "mese", "mesi", "giorno", "giorni",
    "due", "tre", "quattro", "cinque", "dieci",
    "qualcosa", "qualcuno", "ognuno",
    "mondo", "parte", "volta", "momento", "tipo", "roba",
    "senza", "durante", "attraverso", "comunque", "fuori", "sotto",
    "credo", "penso", "direi", "capito", "immagine", "aspetta",
    "scenario", "domanda", "giro", "vero", "basta",
    "fammi", "dimmi", "dai", "poniamo",
    "faccio", "vuole", "gente",
    "cazzo", "quanto", "sto", "sia",
    "ecc", "eccetera", "potrebbe", "magari",
    "tanti", "tante", "molta", "troppo",
    "messa", "nostra", "avanti",
    "alcune", "alcuni", "detto", "cose", "punto",
    "proprio", "vari", "varie", "uomo", "mano", "genere",
    "fine", "senso", "modo", "forma",
    "insomma", "praticamente", "ovviamente", "semplicemente",
    "ormai", "intanto", "frattanto", "comunque",
    "insieme", "intorno", "verso", "fino",
    "pure", "bah", "mmmm", "mmm", "vabbè",
    # English
    "the", "how", "what", "why", "when", "where", "which", "who", "whom",
    "that", "this", "these", "those", "with", "for", "from", "have", "has",
    "had", "not", "can", "will", "would", "could", "should", "may", "might",
    "shall", "do", "does", "did", "be", "is", "are", "was", "were", "been",
    "being", "get", "got", "make", "made", "use", "used", "like", "just",
    "also", "more", "some", "any", "all", "one", "two", "an", "a", "of",
    "in", "to", "and", "or", "but", "if", "as", "at", "by", "it", "its",
    "on", "up", "out", "so", "no", "my", "your", "our", "their", "her",
    "his", "we", "you", "he", "she", "they", "me", "him", "us", "them",
    "about", "into", "over", "after", "than", "then", "there",
    "very", "well", "much", "many", "new", "old", "own", "other",
    "let", "now", "here", "just", "ok", "yes",
}


def slugify(text: str) -> str:
    """Convert a string to a safe filename (no special chars)."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s]+", "_", text.strip())
    return text[:80] or "Varie"


def extract_keywords(title: str) -> set:
    """Extract significant keywords from a conversation title."""
    words = re.findall(r"\b[a-zA-ZàáâãäåæçèéêëìíîïðñòóôõöùúûüýÿÀ-Ö]+\b", title.lower())
    return {w for w in words if w not in STOP_WORDS and len(w) > 2}


def parse_html(html_path: str) -> list:
    """
    Parse the Google Takeout HTML file and return a list of conversation dicts:
        {
            "title":     str,   # user question (used as title)
            "timestamp": str,
            "messages":  [{"role": "user"|"model", "text": str}]
        }
    """
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    conversations = []

    outer_cells = soup.find_all(
        "div", class_=lambda c: c and "outer-cell" in c
    )

    for cell in outer_cells:
        # The main content cell contains "Hai chiesto: <question><br/>timestamp<br/><response>"
        content_cell = cell.find(
            "div",
            class_=lambda c: c and "content-cell" in c and "body-1" in c,
        )
        if content_cell is None:
            continue

        # The raw text starts with "Hai chiesto:\xa0<question>"
        raw_text = content_cell.get_text(separator="\n")
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]

        if not lines:
            continue

        # Extract user question: first line should start with "Hai chiesto:"
        title = ""
        timestamp = ""
        question_text = ""

        first_line = lines[0]
        if first_line.lower().startswith("hai chiesto"):
            # Remove "Hai chiesto:" prefix (with possible nbsp)
            question_text = re.sub(
                r"^hai chiesto\s*[:\xa0\u00a0]?\s*",
                "",
                first_line,
                flags=re.IGNORECASE,
            ).strip()
            title = question_text
            # Second line is often the timestamp
            if len(lines) > 1 and re.search(r"\d{4}", lines[1]):
                timestamp = lines[1]
        else:
            # Fallback: use first line as title
            title = first_line
            if len(lines) > 1 and re.search(r"\d{4}", lines[1]):
                timestamp = lines[1]

        if not title:
            title = "Conversazione senza titolo"

        # Extract Gemini response: all <p> tags inside the content cell
        response_parts = []
        for tag in content_cell.find_all(["p", "ol", "ul", "li", "h1", "h2", "h3", "h4"]):
            text = tag.get_text(separator=" ", strip=True)
            if text:
                response_parts.append(text)

        response_text = "\n\n".join(response_parts) if response_parts else ""

        messages = []
        if question_text:
            messages.append({"role": "user", "text": question_text})
        if response_text:
            messages.append({"role": "model", "text": response_text})

        conversations.append(
            {
                "title": title,
                "timestamp": timestamp,
                "messages": messages,
            }
        )

    return conversations


def group_by_topic(conversations: list, min_freq: int = 10,
                   min_topic_size: int = 5) -> dict:
    """
    Group conversations by topic.

    Strategy (direct keyword assignment):
    1. Count how many titles contain each keyword.
    2. Keep *qualifying* keywords that appear in at least ``min_freq`` titles
       (default 10) – this gives meaningful topic names without one-off clusters.
    3. For each conversation, pick the **most frequent** qualifying keyword
       from its title as the topic label.  Using the most-frequent keyword
       ensures conversations land in the broadest relevant bucket, producing
       a manageable number of topics rather than hundreds of micro-topics.
    4. Conversations with no qualifying keyword → "Varie".
    5. Topics with fewer than ``min_topic_size`` conversations (default 5) are
       merged into "Varie".

    Returns a dict: { topic_name: [conv, ...] }
    """
    # Count keyword occurrences across all titles
    kw_counts: Counter = Counter()
    kw_list = [extract_keywords(c["title"]) for c in conversations]
    for kws in kw_list:
        for kw in kws:
            kw_counts[kw] += 1

    # Qualifying keywords: appear in at least min_freq titles
    qualifying = {kw for kw, cnt in kw_counts.items() if cnt >= min_freq}

    topics: dict = defaultdict(list)
    for conv, kws in zip(conversations, kw_list):
        candidates = kws & qualifying
        if candidates:
            # Pick the most frequent keyword → broadest relevant bucket
            best_kw = max(candidates, key=lambda k: kw_counts[k])
            topic_name = best_kw.capitalize()
        else:
            topic_name = "Varie"
        topics[topic_name].append(conv)

    # Merge small topics into "Varie"
    final: dict = defaultdict(list)
    for topic_name, convs in topics.items():
        if len(convs) < min_topic_size and topic_name != "Varie":
            final["Varie"].extend(convs)
        else:
            final[topic_name].extend(convs)

    return dict(final)


def conversation_to_markdown(conv: dict) -> str:
    """Render a single conversation as a Markdown section."""
    lines = []
    lines.append(f"## {conv['title']}")
    if conv["timestamp"]:
        lines.append(f"*{conv['timestamp']}*")
    lines.append("")
    for msg in conv["messages"]:
        if msg["role"] == "user":
            lines.append(f"**Utente:** {msg['text']}")
        else:
            lines.append(f"**Gemini:** {msg['text']}")
        lines.append("")
    return "\n".join(lines)


def write_topic_file(topic_name: str, convs: list, topics_dir: str) -> str:
    """Write a topic Markdown file and return the filename."""
    filename = slugify(topic_name) + ".md"
    filepath = os.path.join(topics_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Topic: {topic_name}\n\n")
        for conv in convs:
            f.write(conversation_to_markdown(conv))
            f.write("\n\n---\n\n")

    return filename


def write_index(topics: dict, index_path: str, topics_dir_name: str) -> None:
    """Write INDEX.md with links to all topic files."""
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Indice delle Conversazioni Gemini\n\n")
        for topic_name in sorted(topics.keys()):
            convs = topics[topic_name]
            filename = slugify(topic_name) + ".md"
            f.write(f"## [{topic_name}]({topics_dir_name}/{filename})\n\n")
            for conv in convs:
                ts = f" — *{conv['timestamp']}*" if conv["timestamp"] else ""
                f.write(f"- {conv['title']}{ts}\n")
            f.write("\n")


def main(html_path: str | None = None) -> None:
    if html_path is None:
        if len(sys.argv) > 1:
            html_path = sys.argv[1]
        else:
            # Default: same directory as this script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            html_path = os.path.join(script_dir, "LeMieAttività.html")

    if not os.path.exists(html_path):
        print(f"Error: file not found: {html_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {html_path} …")
    conversations = parse_html(html_path)
    print(f"  → {len(conversations)} conversations found")

    print("Grouping by topic …")
    topics = group_by_topic(conversations)
    print(f"  → {len(topics)} topics identified")

    # Create output directories relative to the HTML file location
    base_dir = os.path.dirname(os.path.abspath(html_path))
    topics_dir = os.path.join(base_dir, "topics")
    os.makedirs(topics_dir, exist_ok=True)

    print("Writing topic files …")
    # Remove any stale topic files from previous runs
    for old_file in os.listdir(topics_dir):
        if old_file.endswith(".md"):
            os.remove(os.path.join(topics_dir, old_file))
    for topic_name, convs in sorted(topics.items()):
        filename = write_topic_file(topic_name, convs, topics_dir)
        print(f"  topics/{filename}  ({len(convs)} conversations)")

    index_path = os.path.join(base_dir, "INDEX.md")
    write_index(topics, index_path, "topics")
    print(f"Written {index_path}")
    print("Done.")


if __name__ == "__main__":
    main()
