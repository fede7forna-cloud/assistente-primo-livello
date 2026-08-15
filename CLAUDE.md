# Assistente di Primo Livello — RAG su documentazione

Chatbot di assistenza di primo livello per un prodotto software. Risponde alle domande
degli utenti **esclusivamente** sulla base di una documentazione indicizzata (RAG).
Quando la risposta non è nella documentazione, non inventa: lo dichiara e rimanda
all'assistenza umana.

Stato: demo tecnica. La documentazione attualmente inclusa descrive un software fittizio
ed è pensata per essere sostituita.

---

## 1. Requisiti funzionali

Sono i vincoli di prodotto. Ogni modifica al codice deve preservarli.

| # | Requisito | Dove è garantito |
|---|---|---|
| RF-1 | Le risposte operative sono in **passaggi numerati** | schema di output strutturato + system prompt |
| RF-2 | Ogni risposta **cita la sezione** di documentazione da cui proviene | ogni `Chunk` porta con sé `doc_id` + `section_title` + `anchor`; le citazioni sono validate contro i chunk realmente recuperati |
| RF-3 | **Human in the loop**: se la risposta non è nella documentazione, l'assistente lo dice e rimanda all'assistenza umana | doppio cancello: soglia di similarità sul retrieval + campo `outcome` nella risposta strutturata del modello |
| RF-4 | **Mai inventare**: nessuna risposta basata su conoscenza pregressa del modello | system prompt restrittivo + validazione delle citazioni: una citazione a una sezione non recuperata invalida la risposta |

### Esiti possibili di una richiesta

L'assistente restituisce sempre uno di tre esiti espliciti (`Outcome`), non una stringa libera:

- `ANSWER_FOUND` — passaggi numerati + almeno una citazione valida
- `NOT_IN_DOCUMENTATION` — messaggio di escalation all'assistenza umana, zero passaggi inventati
- `AMBIGUOUS_QUESTION` — richiesta di chiarimento (evita escalation inutili)

### Dove passa la linea fra chiarimento ed escalation

La distinzione fra `AMBIGUOUS_QUESTION` e `NOT_IN_DOCUMENTATION` non è sfumata, ed è
deliberata:

> **Oggetto mancante ⇒ chiarimento. Argomento mancante ⇒ escalation.**

Una domanda che nomina un'azione documentata ma non su cosa vada applicata ("come lo
annullo?") ha un argomento, e le sue alternative sono elencabili a partire dagli estratti:
si chiede un chiarimento. Una domanda che non nomina né oggetto né area ("non funziona",
"aiuto") non ha un argomento su cui verificare se la documentazione lo copra: si rimanda
all'assistenza.

Il vincolo che la produce è nel system prompt, nella definizione di `ambiguous_question`:
il chiarimento **vale solo se gli estratti coprono comunque l'argomento della domanda**.
Senza quel vincolo `ambiguous_question` diventa la scusa per non escalare mai — ogni
domanda scomoda si trasforma in una richiesta di chiarimento e l'assistenza umana non
viene mai coinvolta, che è RF-3 disattivato in silenzio.

Il prezzo di quel vincolo è che le domande completamente vuote finiscono in escalation
invece che in chiarimento. È accettato consapevolmente: **non introdurre regole ad hoc
per singoli casi come "non funziona"**, perché ognuna riapre il buco che il vincolo
chiude.

### Misurazione (dopo la correzione del prompt)

Quattro domande sull'indice reale, prima e dopo aver riscritto la sezione
`COME SCEGLIERE L'ESITO`:

| domanda | prima | dopo |
|---|---|---|
| `"non funziona"` | `not_in_documentation` | `not_in_documentation` |
| `"come lo annullo?"` | `not_in_documentation` | **`ambiguous_question`** |
| `"Devo annullare qualcosa, ma non so se una prenotazione o un contratto"` | `not_in_documentation` | **`ambiguous_question`** |
| `"Come esporto?"` | `answer_found` | `answer_found` |

Prima della correzione `AMBIGUOUS_QUESTION` era **irraggiungibile**: tre istruzioni del
prompt spingevano verso `not_in_documentation` e una sola, più stretta, permetteva il
chiarimento. `Answer.ambiguous()`, `CLARIFICATION_MESSAGE` e il ramo corrispondente della
CLI non venivano mai esercitati fuori dai test.

`"non funziona"` è stato verificato stabile su 4 esecuzioni consecutive, non è varianza di
campionamento. Controlli di non regressione superati: `"ricetta della carbonara"` e
`"aiuto"` restano `not_in_documentation`.

Chi modifica il system prompt deve ripetere questa misurazione: la sezione degli esiti è
l'unico punto del progetto dove un requisito funzionale dipende da come un modello
interpreta del testo, e una riformulazione innocua può disattivare un esito senza che
nessun test fallisca.

---

## 2. Vincolo architetturale principale

> La documentazione deve poter essere sostituita con quella di un software reale
> **senza modificare il resto del progetto**.

Conseguenze non negoziabili:

1. **La documentazione è dato, non codice.** Vive in `docs_source/`, fuori dal package
   Python. Sostituirla significa svuotare quella cartella, metterci i file nuovi e rilanciare
   l'ingestione. Zero modifiche a `src/`.
2. **Nessun riferimento a contenuti specifici nel codice.** Niente nomi di funzionalità
   inventate, niente `if "export_csv" in question`, niente elenchi hardcoded di sezioni.
   Il codice conosce *documenti, sezioni e chunk*, non il prodotto che descrivono.
3. **Ports & adapters.** Ogni dipendenza esterna sta dietro un `Protocol` in
   `domain/ports.py`. Cambiare formato dei documenti, embedder, vector store o provider LLM
   significa scrivere un nuovo adapter, non toccare la logica.
4. **Il formato dei documenti è un adapter.** Oggi Markdown con front-matter. Domani HTML,
   PDF o un export Confluence: si aggiunge un loader, il resto non si accorge di niente.

---

## 3. Stack

| Ambito | Scelta | Motivo |
|---|---|---|
| Linguaggio | Python 3.11+ | richiesto |
| LLM | OpenRouter, API OpenAI-compatibile, via SDK `openai` | un solo client per qualsiasi modello OpenRouter |
| Modello | `nvidia/nemotron-3-ultra-550b-a55b:free` | configurabile, mai hardcoded |
| Embeddings | `sentence-transformers` (locale) | il modello viene scaricato da HuggingFace al primo uso e poi resta in cache locale: dopo quel download l'indicizzazione e le interrogazioni calcolano gli embedding in locale, senza rete e senza costi per chiamata |
| Vector store | ChromaDB persistente | persistenza su file, nessun server da avviare |
| API | FastAPI + Uvicorn | endpoint REST leggibile e auto-documentato |
| CLI | Typer | demo eseguibile in un comando |
| Validazione | Pydantic v2 | schema di risposta e config validati a runtime |
| Test | pytest | unit + integration |

### Configurazione e segreti

- `.env` — **solo segreti** (`OPENROUTER_API_KEY`). Mai committato, presente in `.gitignore`.
- `.env.example` — template committato, senza valori reali.
- `config/settings.yaml` — parametri non segreti e versionati: `model`, `base_url`, `top_k`,
  `similarity_threshold`, dimensione dei chunk, nome del modello di embedding, percorsi.
- `src/assistant/config.py` — carica entrambi in un oggetto Pydantic `Settings`, e fallisce
  all'avvio con un messaggio chiaro se manca una chiave obbligatoria.

**Regola: nessuna chiave, URL o nome modello scritto in un file `.py`.** Tutto passa da `Settings`.

### Credenziali: chiedere sempre prima di usarle

> **Regola: non usare mai una credenziale memorizzata sulla macchina senza averlo chiesto
> prima, nemmeno quando serve a ottenere esattamente il risultato richiesto.**

Vale per il token GitHub in Git Credential Manager, per `OPENROUTER_API_KEY` in `.env`, per
le chiavi in variabili d'ambiente e per qualsiasi altro segreto raggiungibile dal progetto.

Il motivo non è il singolo comando, ma l'ampiezza di ciò che quella credenziale autorizza:
un token GitHub che imposta la descrizione di un repository può anche cancellarlo, renderlo
privato, riscriverne la cronologia, leggere i repository privati e agire su ogni
organizzazione a cui l'utente appartiene. Chi autorizza il risultato non sta autorizzando
lo strumento.

Il permesso di usare una credenziale per un'operazione non si estende alla successiva:
va richiesto ogni volta, dicendo **quale** credenziale, **per quale chiamata** e **con quale
effetto**.

Se una credenziale non è disponibile o il permesso non arriva, l'alternativa corretta è
descrivere all'utente i passaggi manuali, non aggirare l'ostacolo.

*Origine della regola: durante la pubblicazione del repository, descrizione e topic sono
stati impostati recuperando il token GitHub da Git Credential Manager senza chiederlo
prima. Il risultato era quello richiesto, il modo no.*

---

## 4. Struttura delle cartelle

```
assistente-primo-livello/
├── CLAUDE.md
├── README.md                     # come far girare la demo in 3 comandi (in italiano)
├── pyproject.toml
├── .env.example
├── .gitignore                    # include .env, .chroma/, __pycache__/
│
├── config/
│   └── settings.yaml             # parametri non segreti, versionati
│
├── docs_source/                  # ⇦ LA DOCUMENTAZIONE. Sostituibile in blocco.
│   ├── README.md                 # formato atteso dei documenti + come sostituirli
│   ├── primi-passi.md            # front-matter YAML: doc_id, title, version
│   ├── catalogo-mezzi.md         # nome file in italiano, identico al doc_id
│   └── ...                       # una pagina per area del prodotto
│
├── src/assistant/
│   ├── config.py                 # Settings (Pydantic): .env + settings.yaml
│   │
│   ├── domain/                   # cuore: nessuna dipendenza da librerie esterne
│   │   ├── models.py             # Document, Section, Chunk, Citation, Answer, Outcome
│   │   └── ports.py              # Protocol: DocumentLoader, Embedder,
│   │                             #   VectorStore, LLMClient
│   │
│   ├── ingestion/                # documentazione → chunk indicizzati
│   │   ├── markdown_loader.py    # adapter: file .md → Document/Section
│   │   ├── chunker.py            # chunking per sezione, preserva i metadati di citazione
│   │   └── pipeline.py           # orchestrazione: load → chunk → embed → store
│   │
│   ├── retrieval/
│   │   ├── local_embedder.py     # adapter: sentence-transformers
│   │   ├── chroma_store.py       # adapter: ChromaDB persistente
│   │   └── retriever.py          # top-k + soglia → primo cancello di RF-3
│   │
│   ├── generation/
│   │   ├── openrouter_client.py  # adapter: SDK openai su base_url OpenRouter
│   │   ├── prompts.py            # system prompt (testo in italiano): passaggi numerati,
│   │   │                         #   cita sempre, non inventare mai
│   │   └── citation_validator.py # secondo cancello RF-3/RF-4: verifica le citazioni
│   │
│   ├── service.py                # AssistantService: unico punto d'ingresso applicativo,
│   │                             #   usato identicamente da CLI e API
│   ├── factory.py                # radice di composizione: l'unico modulo che nomina
│   │                             #   gli adapter concreti. CLI e API partono da qui
│   ├── cli.py                    # Typer: `ingest`, `ask`, `serve`
│   └── api/
│       ├── app.py                # FastAPI: POST /chat, GET /health
│       └── schemas.py            # request/response Pydantic (≠ modelli di dominio)
│
├── scripts/
│   └── ingest.py                 # entrypoint indicizzazione (richiama la pipeline)
│
└── tests/
    ├── unit/                     # chunker, citation validator, soglia, parsing config
    ├── integration/              # pipeline end-to-end con adapter fake, zero rete
    └── fixtures/
        └── sample_docs/          # mini-documentazione di test, indipendente da docs_source/
```

### Perché questa struttura

- **`domain/` non importa nulla di esterno.** È leggibile in cinque minuti e dice cosa fa il
  sistema. È il primo file che il valutatore dovrebbe aprire.
- **Un adapter per riga della tabella dello stack.** Sostituire ChromaDB con FAISS = un file
  nuovo in `retrieval/`, una riga in `config`. Nessun'altra modifica.
- **`service.py` è l'unico orchestratore.** CLI e API sono gusci sottili sopra lo stesso
  oggetto: nessuna logica duplicata, e la logica è testabile senza avviare un server.
- **`docs_source/` è fuori da `src/`.** Rende visivamente ovvio che la documentazione non è
  parte del programma.
- **Le fixture di test non dipendono da `docs_source/`.** Sostituire la documentazione non
  rompe la suite di test.

---

## 5. Flusso

**Indicizzazione** (una tantum, o a ogni cambio di documentazione):

```
docs_source/*.md
  → DocumentLoader  → Document[]  (doc_id, title, sections)
  → Chunker         → Chunk[]     (ognuno porta section_title + anchor)
  → Embedder        → vettori
  → VectorStore     → .chroma/ (persistente)
```

**Interrogazione** (per ogni domanda):

```
question
  → Embedder    → vettore
  → VectorStore → top-k chunk con score
  → GATE 1: best score < similarity_threshold?  → Outcome.NOT_IN_DOCUMENTATION
            (nessuna chiamata LLM: niente costo, niente allucinazione possibile)
  → LLMClient (system prompt + solo i chunk recuperati come contesto)
  → risposta strutturata: { outcome, steps[], citations[], message }
  → GATE 2: citazione a una sezione non presente nei chunk recuperati?
            → risposta scartata → Outcome.NOT_IN_DOCUMENTATION
  → Answer
```

I due cancelli sono deliberatamente ridondanti: il primo evita spesa e allucinazioni a monte,
il secondo intercetta il caso in cui il modello inventi comunque una fonte plausibile.

### Quanto vale il cancello 1 — misurato

18 domande valutate sull'indice reale prodotto da `docs_source/` (90 blocchi, modello
`intfloat/multilingual-e5-small`): 10 a cui la documentazione risponde, 8 deliberatamente
fuori tema. Per ciascuna è stato preso il punteggio del chunk migliore.

| | punteggio |
|---|---|
| minimo tra le 10 domande **in tema** | **0,8526** — *"Come metto un'unità fuori servizio?"* |
| massimo tra le 8 domande **fuori tema** | **0,8707** — *"Come integro Rentaly con SAP via API REST?"* |
| `similarity_threshold` configurata | 0,80 |

**I due gruppi si sovrappongono: nessun valore di soglia li separa.** Il caso peggiore è
strutturale e non risolvibile tarando: una domanda lessicalmente in tema su una funzionalità
non documentata produce un embedding simile a quello di una domanda legittima, perché è
precisamente ciò che un embedding misura.

Conseguenza da tenere presente in ogni modifica futura:

> **Il cancello 1 è un filtro di costo, non una garanzia di correttezza.**
> A 0,80 blocca 3 delle 8 domande fuori tema senza spendere un token, e lascia passare le
> altre 5. La garanzia contro le risposte inventate è il **cancello 2** — la validazione
> delle citazioni in `generation/citation_validator.py` — insieme all'esito
> `not_in_documentation` che il modello dichiara da sé.

Alzare la soglia comprerebbe qualche rifiuto a costo zero in più e inizierebbe a respingere
domande legittime (il minimo in tema è 0,8526, sotto il massimo fuori tema). Non
trasformerebbe il primo cancello in una garanzia. Chi indebolisse il cancello 2 pensando
che il primo faccia da rete si troverebbe senza nessuna delle due.

La misurazione va ripetuta a ogni sostituzione della documentazione: i valori sopra valgono
per questo corpus e per questo modello di embedding.

---

## 6. Convenzioni di codice

- **Lingua.** Identificatori (classi, funzioni, variabili, moduli, cartelle, chiavi di
  configurazione) **in inglese**. L'italiano compare solo nei testi rivolti all'utente finale:
  system prompt in `prompts.py`, messaggi di escalation, output della CLI, README, contenuto
  di `docs_source/`. I commenti e le docstring seguono l'inglese del codice.
- **Eccezione: tutto ciò che compone il riferimento citabile è in italiano.** Il riferimento
  mostrato all'utente ha la forma `doc_id#ancora` (es. `contratti-noleggio#cauzione`) e finisce
  in un link cliccabile: è quindi testo rivolto all'utente finale, non un identificatore di
  codice. Sono in italiano, kebab-case minuscolo, senza accenti:
  - le **ancore** delle sezioni (`{#creare-utente}`), coerenti con il titolo della sezione;
  - il **`doc_id`** nel front-matter;
  - il **nome del file** in `docs_source/`, che deve coincidere con il `doc_id`
    (`contratti-noleggio` ⇒ `contratti-noleggio.md`).

  Questi valori sono **immutabili**: non si rinominano e non si riusano, perché sono il
  contratto di citabilità verso l'esterno. Se una sezione sparisce, la sua ancora si ritira e
  non viene riciclata su altro contenuto. I *nomi dei campi* che li contengono
  (`Chunk.anchor`, `Document.doc_id`) restano invece in inglese, come ogni altro identificatore
  di codice: la regola riguarda i valori, non lo schema.
- Type hints ovunque; `Protocol` per le interfacce, non ereditarietà.
- Dati immutabili: modelli Pydantic/dataclass frozen, funzioni che restituiscono nuovi oggetti.
- Funzioni sotto le 50 righe, file sotto le 400. Se un file cresce, si estrae un modulo.
- Errori gestiti esplicitamente ai confini (I/O, rete, parsing). Mai un `except` silenzioso.
- Nessun `print` nella logica: logging strutturato; l'output utente vive in `cli.py` e `api/`.
- Docstring sul *perché*, non sul *cosa*. Il nome della funzione dice cosa fa.

---

## 7. Comandi

```bash
# setup
cp .env.example .env          # poi inserire OPENROUTER_API_KEY

# Windows / macchina senza GPU: installare prima torch dall'indice CPU.
# Altrimenti sentence-transformers tira la build CUDA (~2.5 GB inutili).
pip install torch --index-url https://download.pytorch.org/whl/cpu

pip install -e ".[dev]"

# indicizzare la documentazione presente in docs_source/
python -m assistant.cli ingest

# fare una domanda da terminale
python -m assistant.cli ask "Come esporto un report?"

# avviare l'API
python -m assistant.cli serve      # → http://localhost:8000/docs

# test
pytest
```

---

## 8. Sostituire la documentazione (procedura)

1. Svuotare `docs_source/` (conservando il suo `README.md`).
2. Copiarci i nuovi documenti nel formato descritto in `docs_source/README.md`
   (Markdown con front-matter: `doc_id`, `title`, `version`), assegnando a ogni file un nome
   in italiano kebab-case identico al proprio `doc_id`.
3. Eliminare l'indice esistente: `rm -rf .chroma/`.
4. `python -m assistant.cli ingest`.

Se i nuovi documenti **non** sono Markdown, l'unica modifica al codice è un nuovo adapter in
`ingestion/` che implementi `DocumentLoader`, più una riga di configurazione. Nient'altro nel
progetto cambia: è esattamente la proprietà che questa architettura esiste per garantire.
