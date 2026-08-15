# La documentazione

Questa cartella **è** la conoscenza dell'assistente. Tutto ciò che sa rispondere sta
qui dentro; tutto ciò che non sta qui dentro viene rimandato all'assistenza umana.

È dato, non codice. Sostituire la documentazione di esempio con quella di un prodotto
reale non richiede di modificare una riga in `src/`: si svuota questa cartella, ci si
mettono i nuovi file nel formato descritto sotto, si rilancia l'indicizzazione.

> Questo `README.md` **non viene indicizzato**: descrive il formato, non il prodotto.
> Il loader lo esclude per nome. Va conservato quando si svuota la cartella.

---

## 1. Formato di un documento

Un documento è un file Markdown con due parti obbligatorie: il front-matter e almeno
una sezione con ancora.

```markdown
---
doc_id: contratti-noleggio
title: Contratti di noleggio
version: "1.0"
---

# Contratti di noleggio

Introduzione al documento. Questo testo **non viene indicizzato**: sta prima della
prima sezione e quindi non ha un'ancora con cui essere citato.

## Cauzione e deposito {#cauzione}

La cauzione viene richiesta alla stipula e trattenuta fino alla riconsegna.

1. Aprire il contratto dalla schermata **Contratti**.
2. Inserire l'importo nel campo **Cauzione**.
3. Confermare con **Salva**.

L'importo minimo è pari al 20% del valore del noleggio.

## Firma del contratto {#firma-contratto}

...
```

### Il front-matter

Delimitato da `---`, in cima al file, prima di qualsiasi altra cosa. Tre campi, tutti
obbligatori e tutti non vuoti:

| Campo | Cos'è | Note |
|---|---|---|
| `doc_id` | Identificatore del documento | Deve coincidere con il nome del file, senza `.md` |
| `title` | Titolo leggibile | Mostrato all'utente accanto alla citazione |
| `version` | Versione del documento | Fra virgolette: `"1.0"`, non `1.0` |

Le virgolette su `version` non sono un vezzo. Senza, YAML legge `1.0` come numero e
`1.10` diventerebbe `1.1`.

### Le sezioni

**Solo i titoli di secondo livello (`##`) sono sezioni**, e ognuno deve portare la
propria ancora fra graffe:

```markdown
## Titolo della sezione {#ancora-della-sezione}
```

Il titolo di primo livello (`#`) è il titolo del documento e non produce una sezione.
I titoli di terzo livello (`###`) e inferiori **restano dentro** la sezione `##` che li
contiene: sono articolazioni del suo contenuto, non unità citabili a sé.

Una sezione senza ancora è un errore e blocca l'indicizzazione. L'ancora **non viene
dedotta dal titolo**: uno slug generato cambierebbe da solo il giorno in cui qualcuno
corregge un refuso nel titolo, e i riferimenti già dati agli utenti punterebbero nel
vuoto senza che nessuno se ne accorga.

---

## 2. Nomi: italiano, minuscolo, senza accenti

Tre valori sono in italiano perché finiscono sotto gli occhi dell'utente finale, dentro
un riferimento della forma `doc_id#ancora` — per esempio `contratti-noleggio#cauzione`:

- il **nome del file**;
- il **`doc_id`** nel front-matter;
- le **ancore** delle sezioni.

Tutti e tre seguono la stessa regola: **kebab-case minuscolo, senza accenti**. Solo
lettere non accentate, cifre e trattini singoli.

| Sì | No | Perché |
|---|---|---|
| `riconsegna-verifica-danni` | `Riconsegna-Verifica-Danni` | Le maiuscole non sono ammesse |
| `perche-serve` | `perché-serve` | Gli accenti non sono ammessi |
| `giorni-buffer` | `giorni buffer` | Gli spazi non sono ammessi |
| `errori-report` | `errori--report` | Trattini doppi non sono ammessi |

Il nome del file **deve** coincidere con il `doc_id`: `contratti-noleggio` ⇒
`contratti-noleggio.md`. È ciò che permette di risalire dal riferimento mostrato
all'utente al file che lo contiene.

### Ancore e `doc_id` sono immutabili

Una volta pubblicati, non si rinominano e non si riusano. Sono il contratto di
citabilità verso l'esterno: qualcuno potrebbe averli in un ticket, in una email, nella
cronologia di una chat.

Se una sezione sparisce, **la sua ancora si ritira**. Non viene riciclata su altro
contenuto: un riferimento che porta alla sezione sbagliata è peggio di uno che non porta
da nessuna parte, perché sembra funzionare.

Due sezioni non possono condividere un'ancora nello stesso documento: renderebbe il
riferimento `doc_id#ancora` ambiguo, e l'indicizzazione si ferma.

---

## 3. Come si scrive una sezione che funziona

Questa parte non è stile: incide direttamente su cosa l'assistente riesce a rispondere.

Il sistema divide i documenti in blocchi e recupera **i singoli blocchi**, non i
documenti. Al modello arrivano poche sezioni isolate, senza quelle intorno, senza il
titolo del capitolo, senza ciò che veniva prima. Una sezione va scritta pensando che
verrà letta da sola.

### Una sezione = una domanda, con risposta completa

Chi la legge isolata deve poter fare l'operazione fino in fondo. Se la procedura ha un
prerequisito, va detto qui, non nella sezione precedente.

### Niente riferimenti che dipendono dall'ordine di lettura

> ❌ «Come descritto sopra, l'importo viene trattenuto…»
> ❌ «Ripetere la procedura vista in precedenza.»
> ✅ «Come descritto in *Cauzione e deposito*, l'importo viene trattenuto…»

"Sopra" non esiste, per chi riceve un blocco isolato. Se serve rimandare, si nomina la
sezione: il modello può citarla, e l'utente può cercarla.

### Titoli formulati come li cercherebbe un utente

Il recupero funziona per similarità fra la domanda e il contenuto. Un titolo che usa le
parole di chi ha il problema viene trovato; un titolo gergale no.

> ❌ `## Gestione anomalie postume {#anomalie-postume}`
> ✅ `## Cosa fare se il mezzo torna danneggiato {#mezzo-danneggiato}`

### Sotto i 1.500 caratteri

Una sezione che sta sotto il limite diventa **un blocco solo**, ed è il caso migliore:
si cita per intero e si legge per intero.

Oltre i 2.000 caratteri (`chunking.max_chars` in `config/settings.yaml`) la sezione viene
divisa. La divisione è fatta con criterio — cade fra i paragrafi, mai a metà riga, e
ripete l'intestazione delle tabelle in ogni parte — ma resta una sezione spezzata: il
modello può ricevere metà procedura e non sapere dell'altra metà.

C'è anche un limite più severo e meno visibile. Il modello di embedding tronca a **512
token**, cioè circa 1.500–2.000 caratteri di italiano, e lo fa in silenzio: la coda di
una sezione troppo lunga semplicemente non entra nell'indice. Meglio due sezioni con due
ancore che una sezione che rischia di perdere il finale.

Se una sezione cresce troppo, quasi sempre sta rispondendo a due domande: si divide in
due, ognuna con la propria ancora.

### Le tabelle di errori stanno in una sezione loro

Sono il contenuto che più facilmente supera i limiti, e sono anche il più citato.
Isolarle in una sezione dedicata (`{#errori-contratti}`, `{#errori-report}`) le rende
citabili con precisione e le tiene fuori dalle procedure.

### Il testo prima della prima sezione viene scartato

L'introduzione fra il titolo `#` e il primo `##` non entra nell'indice: non ha ancora,
quindi non sarebbe citabile. Serve a chi legge il file, non all'assistente. **Nessuna
informazione che serve a rispondere va messa lì.**

### Altre regole pratiche

- **UTF-8**, sempre.
- **Nessuna sezione vuota**: un titolo senza testo sotto è un errore.
- I titoli dentro i blocchi di codice (recintati da ```` ``` ````) non vengono scambiati
  per sezioni: si può documentare una riga di shell che inizia con `##`.
- Il grassetto `**così**` sui nomi di pulsanti, campi e voci di menu viene conservato
  fino alla risposta finale ed è il modo in cui l'assistente distingue un comando dalla
  prosa. Vale la pena usarlo con coerenza.

---

## 4. Sostituire la documentazione

1. **Svuotare questa cartella**, conservando questo `README.md`.

2. **Copiarci i nuovi documenti**, nel formato descritto sopra, con il nome file uguale
   al `doc_id`.

3. **Reindicizzare:**

   ```bash
   python -m assistant.cli ingest
   ```

   L'indicizzazione azzera l'indice prima di riscriverlo, quindi le sezioni sparite non
   restano interrogabili. Se un documento è malformato, l'indicizzazione si ferma
   **prima** di toccare l'indice esistente: si corregge l'errore segnalato e si rilancia,
   senza restare senza servizio nel frattempo.

4. **Verificare:**

   ```bash
   python -m assistant.cli ask "una domanda a cui la nuova documentazione risponde"
   python -m assistant.cli ask "una domanda a cui non risponde"
   ```

   La prima deve produrre passaggi numerati con una citazione; la seconda deve rimandare
   all'assistenza.

### Quando serve cancellare `.chroma/`

Non serve per un normale cambio di documentazione. Serve se si cambia il **modello di
embedding** in `config/settings.yaml`: i vettori nuovi hanno una dimensione diversa e
l'indice esistente non li accetta.

```bash
rm -rf .chroma/          # Windows: rmdir /s /q .chroma
python -m assistant.cli ingest
```

### Ricalibrare la soglia di escalation

`retrieval.similarity_threshold` decide quando l'assistente rinuncia a rispondere, ed è
tarata **sul corpus e sul modello di embedding**, non in astratto. Cambiando la
documentazione, i punteggi si spostano.

La procedura sta nei commenti di `config/settings.yaml`: si misurano circa venti domande
a cui la documentazione risponde e una decina fuori tema, si guarda dove cadono i due
gruppi e se si separano.

Da sapere prima di provarci: **sul corpus di esempio i due gruppi si sovrappongono**, e
nessuna soglia li separa. Il primo cancello è un filtro di costo, non una garanzia di
correttezza — la garanzia è la validazione delle citazioni, che scarta qualsiasi risposta
citi una sezione non recuperata. I dettagli, con i numeri misurati, sono in `CLAUDE.md`.

### Se i documenti non sono Markdown

HTML, PDF, un export da Confluence: l'unica modifica al codice è un nuovo adapter in
`src/assistant/ingestion/` che implementi il protocollo `DocumentLoader`, più una riga di
configurazione. Il resto del progetto non se ne accorge.

---

## 5. Lista di controllo

Prima di reindicizzare, per ogni file:

- [ ] Nome del file in kebab-case minuscolo, senza accenti, uguale al `doc_id`
- [ ] Front-matter con `doc_id`, `title` e `version` fra virgolette
- [ ] Ogni `##` ha la sua ancora `{#ancora}`, in kebab-case senza accenti
- [ ] Nessuna ancora duplicata nel documento
- [ ] Nessuna ancora riciclata da contenuto precedente
- [ ] Nessuna sezione vuota
- [ ] Nessuna sezione sopra i ~1.500 caratteri
- [ ] Nessun «come visto sopra»: i rimandi nominano la sezione
- [ ] Niente informazioni utili prima del primo `##`
- [ ] File salvato in UTF-8
