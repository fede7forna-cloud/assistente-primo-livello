# Assistente di Primo Livello

Chatbot di assistenza di primo livello per un prodotto software. Risponde alle domande
degli utenti **esclusivamente** sulla base di una documentazione indicizzata (RAG).
Quando la risposta non è nella documentazione, non inventa: lo dichiara e rimanda
all'assistenza umana.

Ogni risposta operativa arriva in passaggi numerati e cita la sezione di documentazione
da cui proviene, nella forma `documento#ancora`. Le citazioni sono verificate contro i
chunk realmente recuperati: se il modello cita una sezione che non gli è stata passata,
la risposta viene scartata e sostituita da un'escalation.

> Stato: demo tecnica. La documentazione inclusa in `docs_source/` descrive un software
> fittizio ed è pensata per essere sostituita in blocco, senza toccare il codice.
> Procedura in [CLAUDE.md, §8](CLAUDE.md).

## Come funziona

L'assistente restituisce sempre uno di tre esiti espliciti:

| Esito | Significato |
|---|---|
| `ANSWER_FOUND` | Passaggi numerati + almeno una citazione valida |
| `NOT_IN_DOCUMENTATION` | Escalation all'assistenza umana, zero passaggi inventati |
| `AMBIGUOUS_QUESTION` | Richiesta di chiarimento, per evitare escalation inutili |

Il percorso di una domanda passa da due cancelli deliberatamente ridondanti:

1. **Prima del modello** — se il chunk più simile sta sotto la soglia di similarità,
   si escala senza nemmeno chiamare l'LLM: nessun costo, nessuna allucinazione possibile.
2. **Dopo il modello** — se una citazione punta a una sezione non recuperata, la risposta
   viene invalidata.

I parametri (modello, `top_k`, soglia, dimensione dei chunk, percorsi) stanno in
[`config/settings.yaml`](config/settings.yaml), versionato. In `.env` finiscono solo i
segreti.

### Quanto vale davvero il primo cancello

Misurato, non stimato. 18 domande sull'indice reale costruito da `docs_source/`
(90 blocchi, modello `intfloat/multilingual-e5-small`): 10 a cui la documentazione
risponde, 8 deliberatamente fuori tema.

| | punteggio |
|---|---|
| minimo tra le domande **in tema** | **0,8526** — *"Come metto un'unità fuori servizio?"* |
| massimo tra le domande **fuori tema** | **0,8707** — *"Come integro Rentaly con SAP via API REST?"* |
| soglia configurata | 0,80 |

**I due gruppi si sovrappongono: nessuna soglia li separa.** Il caso peggiore è
strutturale, non un problema di taratura — una domanda lessicalmente in tema su una
funzionalità non documentata assomiglia a una domanda vera, perché è esattamente ciò
che un embedding misura.

Da cui la conseguenza, detta senza giri di parole: **il primo cancello è un filtro di
costo, non una garanzia di correttezza.** A 0,80 blocca 3 delle 8 domande fuori tema
prima di spendere un token, e lascia passare le altre. Ciò che impedisce a quelle di
ricevere una risposta inventata è **il secondo cancello** — la validazione delle
citazioni — insieme all'esito `not_in_documentation` che il modello stesso dichiara.
Alzare la soglia comprerebbe qualche rifiuto gratuito in più e comincerebbe a
respingere domande legittime: non trasformerebbe il primo cancello in una garanzia.

È il motivo per cui i due cancelli sono ridondanti invece che alternativi.

## Requisiti

- Python **3.11 – 3.13** (3.14 escluso: le wheel di PyTorch non ci sono ancora)
- Una API key OpenRouter — [openrouter.ai/keys](https://openrouter.ai/keys)
- ~2 GB di disco per PyTorch e il modello di embedding

Nessun database e nessun server esterno da avviare: l'indice ChromaDB è un file locale.

## Installazione

### 1. Ambiente virtuale

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux
```

### 2. PyTorch — su Windows e su macchine senza GPU, prima del resto

`sentence-transformers` dipende da PyTorch. Se PyTorch non è già installato, `pip`
scarica la build CUDA predefinita: circa 2,5 GB inutili su una macchina senza GPU
NVIDIA. Installare prima la build CPU evita il download:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Con una GPU NVIDIA da usare davvero, saltare questo passaggio: il comando successivo
installerà la build predefinita.

### 3. Il progetto

```bash
pip install -e ".[dev]"
```

### 4. La chiave API

```bash
cp .env.example .env          # su Windows: copy .env.example .env
```

Aprire `.env` e inserire il valore di `OPENROUTER_API_KEY`. Senza quella chiave
l'applicazione si rifiuta di partire, con un messaggio esplicito. `.env` è in
`.gitignore` e non va committato.

## Uso

### Indicizzare la documentazione

Una tantum, e a ogni modifica dei file in `docs_source/`:

```bash
python -m assistant.cli ingest
```

Legge i Markdown in `docs_source/`, li divide in chunk per sezione preservando i
metadati di citazione, ne calcola gli embedding e li salva in `.chroma/`.

**Al primo avvio scarica il modello di embedding da HuggingFace** (~470 MB per
`intfloat/multilingual-e5-small`). Da lì in poi resta in cache locale: le indicizzazioni
successive e tutte le interrogazioni calcolano gli embedding in locale, senza rete.

Per reindicizzare da zero dopo aver sostituito i documenti, eliminare prima l'indice
esistente:

```bash
rm -rf .chroma/                          # Windows: rmdir /s /q .chroma
python -m assistant.cli ingest
```

### Fare una domanda

```bash
python -m assistant.cli ask "Come esporto un report?"
```

Stampa l'esito, i passaggi numerati e le sezioni citate. Su una domanda fuori
documentazione stampa invece il messaggio di escalation all'assistenza umana.

### Avviare l'API

```bash
python -m assistant.cli serve
```

`POST /chat` per le domande, `GET /health` per il controllo di stato.
Documentazione interattiva su <http://localhost:8000/docs>.

CLI e API sono due gusci sottili sopra lo stesso `AssistantService`: stessa logica,
stessi esiti.

## Test

```bash
pytest
```

Gli unit test coprono chunker, validatore delle citazioni, soglia di similarità e
parsing della configurazione. Gli integration test girano sulla pipeline completa con
adapter finti, senza rete e senza chiamate al modello. Le fixture usano una
mini-documentazione propria, indipendente da `docs_source/`: sostituire la
documentazione reale non rompe la suite.

## Struttura

```
config/settings.yaml     parametri non segreti, versionati
docs_source/             LA DOCUMENTAZIONE — sostituibile in blocco
src/assistant/
  domain/                modelli e Protocol, zero dipendenze esterne
  ingestion/             documentazione → chunk indicizzati
  retrieval/             embedder, vector store, soglia
  generation/            client LLM, prompt, validatore citazioni
  service.py             unico orchestratore, usato da CLI e API
tests/
```

Ogni dipendenza esterna sta dietro un `Protocol` in `domain/ports.py`. Cambiare formato
dei documenti, embedder, vector store o provider LLM significa scrivere un nuovo adapter,
non toccare la logica.
