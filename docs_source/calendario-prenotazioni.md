---
doc_id: calendario-prenotazioni
title: Calendario e prenotazioni
version: "1.0"
---

# Calendario e prenotazioni

Come consultare la disponibilità delle attrezzature in Rentaly e come impegnare
un'unità per un periodo con una prenotazione.

## Come funziona il calendario {#funzionamento-calendario}

Il calendario di Rentaly mostra, per ogni unità del catalogo, i periodi in cui è
già impegnata e quelli in cui è libera. Ogni riga corrisponde a un'unità fisica,
non a un modello: se in magazzino ci sono quattro generatori da 60 kVA, il
calendario mostra quattro righe distinte.

Un'unità risulta occupata quando esiste una prenotazione confermata o un contratto
attivo che la riguarda, oppure quando è in uno stato non noleggiabile — in
manutenzione, fuori servizio o dismessa. Le fermate tecniche compaiono con una
campitura grigia distinta dalle prenotazioni.

Il calendario riguarda esclusivamente la sede attiva, indicata dal selettore in
alto a destra. Le unità di altri depositi non compaiono, nemmeno se disponibili.

## Le viste del calendario {#viste-calendario}

Rentaly propone tre viste del calendario, selezionabili dai pulsanti in alto a
sinistra della schermata **Calendario**.

| Vista | Copertura | Uso tipico |
|---|---|---|
| **Giorno** | Una giornata, suddivisa per fasce orarie | Organizzare consegne e rientri della giornata |
| **Settimana** | Sette giorni | Vista di lavoro abituale al banco |
| **Mese** | Mese solare | Pianificare noleggi lunghi e valutare la saturazione |

In tutte le viste, il colore della barra indica lo stato: azzurro per una
prenotazione provvisoria, blu per una prenotazione confermata, verde per un
contratto in corso, grigio per una fermata tecnica, rosso per un rientro in
ritardo.

La vista predefinita all'apertura si imposta nelle preferenze del proprio profilo.
Passando il puntatore su una barra compare un riepilogo con cliente, date e numero
di documento.

## Verificare la disponibilità di un mezzo {#verificare-disponibilita}

Prima di promettere un'attrezzatura a un cliente conviene interrogare Rentaly per
date e modello, invece di scorrere il calendario a occhio.

1. Aprire **Calendario** e fare clic su **Verifica disponibilità** in alto a
   destra.
2. Selezionare il modello di attrezzatura richiesto dal cliente.
3. Indicare la data di ritiro e la data di rientro previste.
4. Specificare quante unità servono.
5. Premere **Cerca**.

Rentaly risponde con l'elenco delle unità libere in quell'intervallo e, se non
bastano, con la prima data utile in cui la quantità richiesta sarebbe disponibile.
Il risultato tiene già conto dei giorni di preparazione e rientro configurati per
il modello, quindi rappresenta la disponibilità reale e non teorica.

## Creare una prenotazione {#creare-prenotazione}

La prenotazione impegna una o più unità per un intervallo di date. Possono crearla
gli utenti con ruolo **Banco**, **Magazzino** o **Amministratore di sistema**.

1. Dalla schermata **Calendario**, premere **Nuova prenotazione**.
2. Cercare e selezionare il cliente; se non esiste, crearlo con **Nuovo cliente**.
3. Indicare data e ora di ritiro e data e ora di rientro previsto.
4. Aggiungere i modelli richiesti e, per ciascuno, la quantità.
5. Verificare le unità che Rentaly ha assegnato in automatico; per cambiarle,
   usare **Modifica assegnazione**.
6. Scegliere lo stato iniziale: **Provvisoria** oppure **Confermata**.
7. Salvare con **Crea prenotazione**.

Rentaly assegna di default l'unità con il minor numero di ore di noleggio
accumulate, per distribuire l'usura sul parco mezzi. La prenotazione riceve un
numero progressivo nella forma `PR-2024-0147` e non genera alcun importo da
incassare: i valori economici nascono solo con il contratto.

## Modificare le date di una prenotazione {#modificare-prenotazione}

Le date di una prenotazione Rentaly possono essere spostate finché la prenotazione
non è stata trasformata in contratto.

1. Individuare la prenotazione nel calendario oppure cercarne il numero nella
   ricerca globale.
2. Aprirla e premere **Modifica**.
3. Correggere la data di ritiro, quella di rientro o entrambe.
4. Fare clic su **Verifica disponibilità** per controllare che le unità assegnate
   siano libere anche nel nuovo intervallo.
5. Confermare con **Salva modifiche**.

In alternativa, nella vista settimanale o mensile è possibile trascinare la barra
della prenotazione per spostarla, o trascinarne i bordi per allungarla e
accorciarla. Se nel nuovo intervallo un'unità non è libera, Rentaly propone di
sostituirla con un altro esemplare dello stesso modello.

## Annullare una prenotazione {#annullare-prenotazione}

Una prenotazione non più necessaria va annullata, così da liberare le unità per
altri clienti.

1. Aprire la prenotazione dal calendario o dalla ricerca globale.
2. Premere **Annulla prenotazione** nella barra delle azioni.
3. Selezionare il motivo: *Rinuncia del cliente*, *Spostata su altre date*,
   *Inserimento errato*, *Altro*.
4. Aggiungere una nota se il motivo è *Altro*.
5. Confermare l'annullamento.

Le unità tornano disponibili immediatamente. La prenotazione annullata non viene
eliminata: resta consultabile con il filtro **Includi annullate** e compare nei
report sulle rinunce. Una prenotazione già trasformata in contratto non può essere
annullata da questa schermata; va invece annullato il contratto.

## Sovrapposizioni e conflitti {#conflitti-prenotazione}

Rentaly impedisce che la stessa unità risulti impegnata da due documenti nello
stesso momento. Quando ciò accade, la schermata mostra un avviso di conflitto con
il documento in contrasto.

Il conflitto si presenta tipicamente in tre situazioni: si sposta una prenotazione
su date già occupate; si allunga un contratto in corso invadendo una prenotazione
successiva; si mette un'unità in manutenzione mentre ha impegni futuri.

Tre modi per risolverlo:

1. **Sostituire l'unità**: premere **Trova alternativa** e lasciare che Rentaly
   proponga un altro esemplare libero dello stesso modello.
2. **Spostare l'altro documento**: aprire la prenotazione in conflitto dal
   messaggio di avviso e modificarne le date.
3. **Ridurre l'intervallo**: accorciare le date della prenotazione che si sta
   creando fino a eliminare la sovrapposizione.

Rentaly non consente in nessun caso di forzare una doppia assegnazione, nemmeno
agli amministratori.

## Giorni di preparazione e rientro {#giorni-buffer}

Alcune attrezzature richiedono tempo tra un noleggio e il successivo per pulizia,
rifornimento o controllo. Rentaly gestisce questo tempo con i **giorni di
preparazione** prima del ritiro e i **giorni di rientro** dopo la riconsegna.

I giorni configurati vengono aggiunti automaticamente all'occupazione dell'unità:
un generatore con un giorno di rientro, riconsegnato di venerdì, torna prenotabile
da lunedì. Nel calendario questi giorni compaiono come fascia tratteggiata ai
bordi della barra di prenotazione.

Per configurarli su un modello:

1. Aprire la scheda del modello dal catalogo.
2. Selezionare la scheda **Disponibilità**.
3. Impostare **Giorni di preparazione** e **Giorni di rientro**.
4. Salvare con **Applica**.

I valori possono andare da 0 a 7 giorni. La modifica vale per i noleggi futuri e
non ricalcola le prenotazioni già registrate.

## Prenotazioni provvisorie e scadenza dell'opzione {#opzioni-provvisorie}

Una prenotazione **provvisoria** impegna l'attrezzatura per un cliente che non ha
ancora dato conferma definitiva. Occupa il calendario come una prenotazione
normale, ma ha una data di scadenza oltre la quale decade.

Alla creazione, Rentaly assegna alle prenotazioni provvisorie una validità di **5
giorni lavorativi**, modificabile a mano nel campo **Valida fino al**. Quando la
scadenza è vicina, il responsabile della prenotazione riceve una notifica email il
giorno prima.

Alla scadenza, se nessuno interviene, la prenotazione passa allo stato *Decaduta* e
le unità tornano disponibili. Per confermarla prima della scadenza:

1. Aprire la prenotazione provvisoria dal calendario.
2. Premere **Conferma prenotazione**.
3. Verificare date e unità assegnate.
4. Confermare con **Rendi definitiva**.

Una prenotazione decaduta non si riattiva: va creata nuovamente, verificando che
le unità siano ancora libere.

## Trasferire un'unità a un'altra sede {#trasferimento-sedi}

Quando un'attrezzatura serve in un deposito diverso da quello in cui si trova, il
trasferimento va registrato in Rentaly, altrimenti l'unità continua a comparire
nella disponibilità della sede di partenza.

1. Aprire la scheda dell'unità dal catalogo della sede in cui si trova.
2. Premere **Trasferisci** nella barra delle azioni.
3. Selezionare la sede di destinazione.
4. Indicare la data di partenza e quella di arrivo previsto.
5. Confermare con **Avvia trasferimento**.

Durante il trasferimento l'unità è nello stato *In transito* e non è prenotabile in
nessuna delle due sedi. All'arrivo, un utente della sede di destinazione deve
aprire la scheda e premere **Conferma arrivo**: solo allora l'unità entra nel
catalogo di destinazione e torna disponibile. Un'unità con prenotazioni future
nella sede di partenza non può essere trasferita finché quelle prenotazioni non
vengono annullate o riassegnate.

## Messaggi di errore sul calendario {#errori-calendario}

Errori che Rentaly mostra durante la gestione di calendario e prenotazioni.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Unità non disponibile nell'intervallo richiesto* | Un altro documento impegna già l'esemplare in quelle date | Usare Trova alternativa per assegnare un altro esemplare, o modificare le date |
| *Data di rientro precedente alla data di ritiro* | Le due date sono state invertite | Correggere l'intervallo: il rientro deve essere successivo al ritiro |
| *Nessuna unità disponibile per il modello selezionato* | Tutti gli esemplari sono impegnati o non noleggiabili | Consultare la prima data utile proposta da Rentaly, o verificare le unità in manutenzione |
| *Prenotazione decaduta* | La validità dell'opzione provvisoria è scaduta senza conferma | Creare una nuova prenotazione dopo aver verificato la disponibilità |
| *Trasferimento non consentito: impegni futuri sull'unità* | L'esemplare ha prenotazioni nella sede di partenza | Riassegnare o annullare quelle prenotazioni, poi ripetere il trasferimento |
| *Il cliente ha contratti scaduti non chiusi* | Il cliente ha attrezzature non ancora rientrate oltre la data prevista | Chiudere i contratti in sospeso oppure richiedere l'autorizzazione all'Amministrazione |
