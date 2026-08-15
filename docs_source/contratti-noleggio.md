---
doc_id: contratti-noleggio
title: Contratti di noleggio
version: "1.0"
---

# Contratti di noleggio

Come stipulare, modificare e chiudere un contratto di noleggio in Rentaly, dalla
firma del cliente alla restituzione della cauzione.

## Che cos'è un contratto in Rentaly {#cos-e-contratto}

Il contratto di noleggio è il documento che formalizza la consegna di una o più
attrezzature a un cliente. Riporta le unità assegnate con il loro codice, le date
di ritiro e rientro previsto, le tariffe applicate, la cauzione richiesta e le
condizioni generali di noleggio dell'azienda.

A differenza della prenotazione, che si limita a impegnare le unità nel calendario,
il contratto genera importi da incassare e trasferisce la responsabilità
dell'attrezzatura al cliente. Dal momento della consegna, un danno al mezzo è
imputabile a chi ha firmato.

Ogni contratto riceve un numero progressivo annuale nella forma `CN-2024-0312`.
Il numero è definitivo alla creazione e compare su tutti i documenti collegati,
compreso il verbale di riconsegna.

## Gli stati del contratto {#stati-contratto}

Un contratto Rentaly attraversa una sequenza di stati che ne determinano le
operazioni consentite.

| Stato | Significato | Cosa si può fare |
|---|---|---|
| **Bozza** | Creato ma non ancora firmato dal cliente | Modificare tutto, annullare |
| **Firmato** | Il cliente ha firmato, le attrezzature non sono ancora uscite | Registrare la consegna, annullare |
| **In corso** | Attrezzature consegnate e presso il cliente | Prorogare, aggiungere unità, avviare la riconsegna |
| **In riconsegna** | Rientro registrato, verbale non ancora chiuso | Completare la verifica danni |
| **Chiuso** | Tutto rientrato e conteggiato, cauzione gestita | Sola consultazione |
| **Annullato** | Interrotto prima della consegna | Sola consultazione |

Il passaggio *In corso* → *In riconsegna* avviene automaticamente alla
registrazione del rientro. Un contratto in stato *Chiuso* non è più modificabile:
eventuali correzioni richiedono una nota di rettifica gestita
dall'Amministrazione.

## Creare un contratto da una prenotazione {#creare-contratto-da-prenotazione}

È il percorso più frequente: il cliente si presenta al banco per ritirare
un'attrezzatura già prenotata.

1. Cercare il numero della prenotazione nella ricerca globale in alto a destra,
   oppure individuarla nel calendario.
2. Aprire la prenotazione e premere **Trasforma in contratto**.
3. Verificare che cliente, unità assegnate e date corrispondano a quanto pattuito.
4. Controllare le tariffe proposte e applicare eventuali sconti concordati.
5. Indicare l'importo della cauzione e la modalità con cui viene versata.
6. Premere **Crea contratto**.

Il contratto nasce in stato *Bozza* ereditando tutti i dati della prenotazione, che
passa a *Convertita* e non è più modificabile. Se nel frattempo un'unità prenotata
è diventata indisponibile, Rentaly lo segnala e propone un esemplare alternativo
dello stesso modello.

## Creare un contratto immediato al banco {#contratto-immediato}

Quando il cliente si presenta senza prenotazione e l'attrezzatura è disponibile, il
contratto si stipula direttamente.

1. Andare in **Contratti** e premere **Nuovo contratto**.
2. Selezionare il cliente dall'anagrafica oppure registrarlo con **Nuovo cliente**.
3. Impostare la data di ritiro (di norma la giornata corrente) e il rientro
   previsto.
4. Aggiungere le attrezzature cercandole per modello o inquadrando il codice QR
   dell'unità.
5. Rivedere tariffe e cauzione calcolate da Rentaly.
6. Confermare con **Crea contratto**.

Rentaly verifica la disponibilità delle unità nel momento stesso in cui vengono
aggiunte e blocca l'inserimento se l'esemplare risulta già impegnato. Per i clienti
registrati da meno di 30 giorni, il sistema richiede la conferma di un documento
d'identità valido prima di consentire la firma.

## Aggiungere o rimuovere unità da un contratto {#modificare-unita-contratto}

La composizione di un contratto può cambiare finché il contratto non è chiuso: il
cliente può chiedere un'attrezzatura in più o restituirne una in anticipo.

1. Aprire il contratto dall'elenco **Contratti** o dalla ricerca globale.
2. Nella sezione **Attrezzature**, premere **Modifica righe**.
3. Per aggiungere, usare **Aggiungi unità** e selezionare il modello desiderato.
4. Per togliere un'unità non ancora consegnata, premere l'icona di eliminazione
   sulla riga.
5. Salvare con **Aggiorna contratto**.

Le unità aggiunte a un contratto *In corso* vengono conteggiate dalla data di
aggiunta, non da quella di inizio noleggio. Un'unità già consegnata non si rimuove
dal contratto: per restituirla in anticipo si registra una riconsegna parziale, che
ne interrompe il conteggio mantenendo aperto il resto del contratto.

## Cauzione e deposito {#cauzione}

La cauzione è l'importo trattenuto a garanzia dell'attrezzatura, calcolato da
Rentaly come somma delle cauzioni previste per ciascuna unità noleggiata.

Le modalità di versamento accettate sono contanti, bonifico e preautorizzazione su
carta di credito. La modalità si sceglie nella sezione **Cauzione** del contratto
al momento della creazione.

Alla chiusura del contratto, Rentaly calcola l'importo da restituire sottraendo
alla cauzione gli eventuali addebiti per danni, ritardi o carburante mancante. Se
gli addebiti superano la cauzione, la differenza viene riportata come importo da
fatturare al cliente.

La restituzione della cauzione si registra così:

1. Aprire il contratto in stato *Chiuso*.
2. Individuare la sezione **Cauzione** e premere **Registra restituzione**.
3. Indicare l'importo effettivamente restituito e la modalità.
4. Confermare con **Salva**.

Finché la restituzione non è registrata, il contratto compare nell'elenco
**Cauzioni da restituire** del cruscotto.

## Firma del contratto {#firma-contratto}

Il contratto acquista validità con la firma del cliente. Rentaly supporta la firma
grafometrica su tablet e la firma su carta con successivo caricamento della
scansione.

Per la firma su tablet:

1. Aprire il contratto in stato *Bozza* e premere **Raccogli firma**.
2. Passare il tablet al cliente perché legga il riepilogo mostrato a schermo.
3. Far apporre la firma nell'area dedicata con il dito o con il pennino.
4. Premere **Conferma firma**.

Per la firma su carta, premere invece **Stampa per firma**, far firmare la copia
cartacea e caricarne la scansione con **Allega contratto firmato**. In entrambi i
casi il contratto passa allo stato *Firmato*. Una volta firmato, il contratto non
consente più modifiche a tariffe e condizioni: restano possibili solo proroga,
aggiunta di unità e riconsegna.

## Registrare la consegna al cliente {#consegna}

La consegna segna l'uscita fisica delle attrezzature dal magazzino e il passaggio
di responsabilità al cliente.

1. Aprire il contratto in stato *Firmato*.
2. Premere **Registra consegna**.
3. Confermare una per una le unità che escono, inquadrandone il codice QR oppure
   spuntandole nell'elenco.
4. Indicare per ciascuna il livello di carburante e le ore di utilizzo lette sul
   contatore.
5. Allegare le foto dello stato dell'attrezzatura al momento della consegna.
6. Confermare con **Conferma consegna**.

Le unità passano allo stato *A noleggio* e il contratto allo stato *In corso*. Le
foto e i valori registrati in questa fase sono il termine di paragone per la
verifica dei danni al rientro: senza di essi, un eventuale addebito è difficile da
sostenere in caso di contestazione.

## Prorogare un noleggio {#prorogare-noleggio}

Se il cliente ha bisogno dell'attrezzatura più a lungo del previsto, il contratto si
proroga senza doverne stipulare uno nuovo.

1. Aprire il contratto in stato *In corso*.
2. Premere **Proroga** nella barra delle azioni.
3. Indicare la nuova data di rientro previsto.
4. Controllare l'esito della verifica di disponibilità mostrata da Rentaly.
5. Confermare con **Applica proroga**.

Rentaly ricalcola l'importo del noleggio sull'intera durata aggiornata, applicando
se conveniente la tariffa settimanale o mensile al posto di quella giornaliera. Se
una delle unità è già prenotata da un altro cliente nel periodo di proroga, la
proroga viene bloccata e Rentaly indica quale prenotazione la impedisce: occorre
accordarsi con l'altro cliente o proporre un esemplare sostitutivo.

Ogni proroga resta registrata nello storico del contratto con data, utente e nuova
scadenza.

## Chiudere un contratto {#chiudere-contratto}

La chiusura è l'ultimo passo: consolida gli importi e riporta il contratto in sola
consultazione. Può eseguirla il ruolo **Amministrazione** o **Amministratore di
sistema**.

1. Aprire il contratto in stato *In riconsegna*, con il verbale di verifica già
   completato.
2. Controllare il riepilogo economico: giorni di noleggio, addebiti per danni,
   penali di ritardo, carburante.
3. Applicare eventuali abbuoni concordati con il cliente.
4. Verificare l'importo di cauzione da restituire calcolato da Rentaly.
5. Premere **Chiudi contratto** e confermare.

Alla chiusura il contratto diventa non modificabile e i suoi dati entrano nei
report di fatturato. Un contratto non può essere chiuso se anche una sola unità
risulta ancora nello stato *A noleggio*: vanno prima registrate tutte le
riconsegne.

## Annullare un contratto {#annullare-contratto}

Un contratto può essere annullato solo prima della consegna delle attrezzature,
cioè negli stati *Bozza* e *Firmato*.

1. Aprire il contratto interessato.
2. Premere **Annulla contratto** nel menu contestuale in alto a destra.
3. Selezionare il motivo: *Rinuncia del cliente*, *Errore di inserimento*,
   *Attrezzatura non disponibile*, *Altro*.
4. Indicare se la cauzione già incassata va restituita.
5. Confermare l'annullamento.

Le unità tornano immediatamente disponibili a calendario. Il contratto annullato
mantiene il proprio numero, che non viene riassegnato, e resta consultabile con il
filtro **Includi annullati**. Un contratto in stato *In corso* non si annulla: va
gestito con una riconsegna anticipata seguita dalla chiusura.

## Messaggi di errore sui contratti {#errori-contratti}

Errori che Rentaly mostra durante la gestione dei contratti di noleggio.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Contratto non modificabile dopo la firma* | Si stanno cambiando tariffe o condizioni di un contratto già firmato | Annullare il contratto e ristipularlo, oppure gestire la differenza come abbuono alla chiusura |
| *Proroga bloccata: unità già impegnata* | Un altro cliente ha prenotato l'esemplare nel periodo di proroga | Proporre un esemplare sostitutivo o concordare una data di rientro diversa |
| *Documento d'identità non verificato* | Il cliente è registrato da meno di 30 giorni e manca la verifica | Registrare gli estremi del documento nella scheda cliente prima della firma |
| *Impossibile chiudere: unità ancora a noleggio* | Non tutte le attrezzature del contratto risultano rientrate | Registrare le riconsegne mancanti, poi ripetere la chiusura |
| *Cauzione insufficiente rispetto agli addebiti* | Gli importi da addebitare superano la cauzione trattenuta | Chiudere comunque il contratto: la differenza viene riportata come importo da fatturare |
| *Contratto in corso: annullamento non consentito* | Le attrezzature sono già state consegnate al cliente | Registrare una riconsegna anticipata e procedere con la chiusura |
