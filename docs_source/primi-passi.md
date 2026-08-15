---
doc_id: primi-passi
title: Primi passi e concetti base
version: "1.0"
---

# Primi passi e concetti base

Introduzione a Rentaly per chi lo usa per la prima volta: come accedere, come è
organizzata l'interfaccia e quali sono i concetti su cui si basa tutto il resto
del prodotto.

## Che cos'è Rentaly {#cos-e-rentaly}

Rentaly è un software cloud per le aziende che noleggiano attrezzature: ponteggi,
generatori, macchine da cantiere, piattaforme aeree e simili. Si usa dal browser,
senza installare nulla sul computer.

Rentaly copre l'intero percorso di un noleggio: registrazione delle attrezzature a
catalogo, verifica della disponibilità nel calendario, stipula del contratto al
banco, consegna al cliente, riconsegna con verifica dei danni e rendicontazione
finale.

È pensato per tre profili di lavoro che convivono nella stessa azienda: il
personale di **magazzino**, che movimenta fisicamente le attrezzature; gli
**operatori al banco**, che ricevono il cliente e stipulano i noleggi; e
l'**amministrazione**, che segue fatturazione, addebiti e report.

## Accedere a Rentaly {#accedere}

L'accesso a Rentaly avviene dal browser, con l'indirizzo fornito dall'azienda
(nella forma `https://nomeazienda.rentaly.app`). Sono supportati Chrome, Edge,
Firefox e Safari nelle due versioni più recenti.

1. Aprire il browser e digitare l'indirizzo Rentaly della propria azienda.
2. Inserire l'indirizzo email aziendale nel campo **Email**.
3. Inserire la propria password nel campo **Password**.
4. Se l'azienda ha attivato l'autenticazione a due fattori, digitare il codice a
   sei cifre generato dall'app di autenticazione.
5. Fare clic su **Accedi**.

Al primo accesso Rentaly chiede di accettare le condizioni d'uso e di confermare i
propri dati anagrafici. La sessione resta attiva **8 ore** di inattività, dopo le
quali viene richiesto un nuovo accesso.

## La barra di navigazione {#barra-navigazione}

Tutte le aree di Rentaly si raggiungono dalla barra di navigazione in alto, sempre
visibile. Le voci mostrate dipendono dal ruolo dell'utente: chi non ha accesso a
un'area non ne vede la voce di menu.

| Voce | Contenuto |
|---|---|
| **Cruscotto** | Riepilogo della giornata: consegne previste, rientri attesi, mezzi in ritardo |
| **Catalogo** | Elenco delle attrezzature e delle singole unità a magazzino |
| **Calendario** | Disponibilità dei mezzi e prenotazioni nel tempo |
| **Contratti** | Noleggi in corso, chiusi e in preparazione |
| **Riconsegne** | Rientri da verificare e verbali di danno |
| **Report** | Analisi di utilizzo, fatturato e scadenze |
| **Impostazioni** | Utenti, sedi, tariffe e configurazioni aziendali |

A destra della barra si trovano il selettore della sede attiva, il campo di
ricerca globale e il menu del proprio profilo. La ricerca globale accetta il
numero di contratto, il codice di un'unità o il nome di un cliente.

## Mezzo, modello e unità {#mezzo-modello-unita}

Rentaly distingue tre livelli, ed è la distinzione più importante da capire per
usare correttamente il prodotto.

- La **categoria** è il raggruppamento merceologico: *Generatori*, *Ponteggi*,
  *Piattaforme aeree*. Serve a organizzare il catalogo e a filtrare le ricerche.
- Il **modello** è il tipo di attrezzatura con le sue caratteristiche commerciali:
  *Generatore diesel 60 kVA*. Al modello sono associati la scheda tecnica, le foto
  e la tariffa di noleggio.
- L'**unità** è il singolo esemplare fisico presente in magazzino, identificato da
  un codice univoco: *GEN-60-004*. È l'unità, non il modello, che viene
  effettivamente noleggiata, consegnata e riconsegnata.

Un modello può avere una sola unità o cinquanta. Quando un cliente chiede "un
generatore da 60 kVA" sta chiedendo un modello; Rentaly assegna al contratto una
specifica unità disponibile in quelle date.

## Prenotazione, contratto e riconsegna {#prenotazione-contratto-riconsegna}

I tre documenti che scandiscono un noleggio in Rentaly hanno significati distinti
e non vanno confusi.

- La **prenotazione** impegna una o più unità per un intervallo di date. Non è
  vincolante per il cliente e non genera importi da incassare: serve a garantire
  che l'attrezzatura sia disponibile quando servirà.
- Il **contratto di noleggio** è il documento che formalizza il noleggio: riporta
  cliente, unità assegnate, date, tariffe e cauzione. Viene firmato dal cliente al
  momento del ritiro.
- La **riconsegna** registra il rientro fisico dell'attrezzatura e contiene il
  verbale di verifica, cioè l'esito del controllo delle condizioni del mezzo.

Una prenotazione può diventare un contratto, ma non è obbligatorio: al banco è
possibile stipulare un contratto immediato senza prenotazione preesistente.

## Il ciclo di vita di un noleggio {#ciclo-noleggio}

Il percorso tipico di un noleggio in Rentaly attraversa sei momenti. Conoscerli
aiuta a capire in quale schermata cercare un'informazione.

1. **Richiesta**: il cliente chiede la disponibilità di un'attrezzatura per certe
   date.
2. **Prenotazione**: le unità vengono impegnate a calendario per quell'intervallo.
3. **Contratto**: al ritiro si stipula il contratto, si incassa la cauzione e il
   cliente firma.
4. **Consegna**: le unità passano allo stato *A noleggio* e escono dal magazzino.
5. **Riconsegna**: il cliente riporta le attrezzature e il magazzino compila il
   verbale di verifica.
6. **Chiusura**: si conteggiano eventuali danni, ritardi o consumi, si restituisce
   la cauzione e il contratto passa allo stato *Chiuso*.

Ogni passaggio lascia traccia: da un contratto chiuso è sempre possibile risalire
alla prenotazione di origine e al verbale di riconsegna.

## Gli stati di un'unità {#stati-unita}

Ogni unità presente nel catalogo Rentaly si trova sempre in uno stato, che ne
determina la prenotabilità.

| Stato | Significato | Prenotabile |
|---|---|---|
| **Disponibile** | In magazzino, pronta al noleggio | Sì |
| **Prenotata** | Impegnata da una prenotazione per date future | Solo fuori da quelle date |
| **A noleggio** | Consegnata al cliente, fuori dal magazzino | No |
| **In verifica** | Rientrata, in attesa del verbale di controllo | No |
| **In manutenzione** | Ferma per riparazione o revisione | No |
| **Fuori servizio** | Non noleggiabile per decisione dell'azienda | No |
| **Dismessa** | Venduta, rottamata o non più di proprietà | No |

Il passaggio da uno stato all'altro avviene quasi sempre in automatico come
conseguenza di un'operazione (una consegna, una riconsegna). Gli unici stati
impostabili a mano sono *In manutenzione*, *Fuori servizio* e *Dismessa*.

## Sedi e magazzini {#sedi}

Un'azienda che usa Rentaly può avere una sola sede o diversi depositi. Ogni sede
ha un proprio catalogo di unità, un proprio calendario e propri contratti: le
attrezzature di una sede non compaiono nella disponibilità di un'altra.

La sede su cui si sta lavorando è indicata dal selettore in alto a destra nella
barra di navigazione. Tutto ciò che si vede a schermo — disponibilità, contratti,
riconsegne — si riferisce alla sede attiva in quel momento.

Un'attrezzatura può essere spostata da una sede all'altra registrando un
trasferimento; finché il trasferimento non viene confermato in arrivo, l'unità
resta contabilizzata sulla sede di partenza.

## Impostare le proprie preferenze {#preferenze-personali}

Ogni utente Rentaly può adattare alcune impostazioni al proprio modo di lavorare,
senza che ciò influisca sugli altri utenti dell'azienda.

1. Fare clic sul proprio nome in alto a destra e scegliere **Profilo**.
2. Aprire la scheda **Preferenze**.
3. Impostare la **sede predefinita**, cioè quella selezionata automaticamente a
   ogni accesso.
4. Scegliere la **vista iniziale del calendario** tra giornaliera, settimanale e
   mensile.
5. Attivare o disattivare le **notifiche email** per rientri previsti e contratti
   in scadenza.
6. Fare clic su **Salva preferenze**.

Le preferenze sono legate all'account, non al computer: seguono l'utente anche se
accede da un dispositivo diverso.

## Cambiare la propria password {#cambiare-password}

Ogni utente Rentaly può modificare la propria password in autonomia, senza
coinvolgere un amministratore.

1. Aprire il menu del proprio profilo facendo clic sul nome in alto a destra.
2. Selezionare **Profilo**, quindi la scheda **Sicurezza**.
3. Fare clic su **Cambia password**.
4. Digitare la password attuale, poi la nuova password due volte.
5. Fare clic su **Aggiorna password**.

La nuova password deve avere almeno **10 caratteri** e contenere almeno una lettera
maiuscola e una cifra. Rentaly rifiuta le ultime tre password già usate
dall'account. Dopo il cambio, le altre sessioni aperte sullo stesso account
vengono chiuse.

## Cosa Rentaly non gestisce {#limiti-prodotto}

Rentaly copre il ciclo del noleggio, non l'intera gestione aziendale. Le seguenti
attività non sono previste dal prodotto e vanno svolte con strumenti esterni.

- **Contabilità generale e dichiarazioni fiscali**: Rentaly produce gli importi da
  fatturare ed esporta i dati, ma non tiene la prima nota né i registri IVA.
- **Emissione della fattura elettronica**: i dati del contratto si esportano verso
  il gestionale contabile, che emette e trasmette il documento.
- **Gestione del personale**: turni, presenze e paghe non sono contemplati.
- **Manutenzione programmata delle attrezzature**: Rentaly registra che un'unità è
  in manutenzione, ma non pianifica scadenze, tagliandi o revisioni periodiche.
- **Tracciamento GPS dei mezzi** e telemetria di cantiere.
- **Vendita di attrezzature usate**: un'unità venduta si segna come dismessa, ma
  non esiste un flusso di vendita.

Per queste esigenze l'azienda utilizza software dedicati, a cui Rentaly può fornire
i dati tramite esportazione.
