---
doc_id: catalogo-mezzi
title: Catalogo mezzi
version: "1.0"
---

# Catalogo mezzi

Come registrare e mantenere aggiornato l'elenco delle attrezzature in Rentaly:
categorie, modelli, singole unità, tariffe e stato del parco mezzi.

## Come è organizzato il catalogo {#organizzazione-catalogo}

Il catalogo di Rentaly è organizzato su tre livelli: **categoria**, **modello** e
**unità**. La categoria raggruppa merceologicamente (*Generatori*), il modello
descrive il tipo di attrezzatura con le sue caratteristiche commerciali
(*Generatore diesel 60 kVA*), l'unità è il singolo esemplare fisico presente in
magazzino (*GEN-60-004*).

La distinzione conta perché tariffe, schede tecniche e foto vivono sul **modello**,
mentre disponibilità, stato e storico manutenzioni vivono sull'**unità**. Cambiare
la tariffa di un modello la cambia per tutti i suoi esemplari; mettere in
manutenzione un'unità non tocca le altre.

Il catalogo è specifico della sede: un'unità registrata nel deposito di Brescia
non compare nel catalogo del deposito di Verona finché non viene trasferita.

## Cercare un mezzo nel catalogo {#cercare-mezzo}

La schermata **Catalogo** elenca modelli e unità della sede attiva e permette di
restringere l'elenco in più modi.

1. Aprire **Catalogo** dalla barra di navigazione in alto.
2. Digitare nel campo di ricerca il nome del modello o il codice dell'unità.
3. Restringere con i filtri laterali: categoria, stato dell'unità, fascia di
   tariffa giornaliera.
4. Usare l'interruttore **Mostra per unità / Mostra per modello** per passare
   dall'elenco degli esemplari a quello dei tipi di attrezzatura.
5. Fare clic su una riga per aprire la scheda corrispondente.

La ricerca ignora maiuscole, accenti e trattini: digitare `gen60`, `GEN-60` o
`Gen 60` produce lo stesso risultato. Per cercare un'unità presente in un'altra
sede, cambiare prima la sede attiva con il selettore in alto a destra.

## Creare una categoria {#creare-categoria}

Le categorie servono a raggruppare i modelli e a filtrare il catalogo. Possono
crearle gli utenti con ruolo **Magazzino** o **Amministratore di sistema**.

1. In **Catalogo**, fare clic su **Gestisci categorie** nel menu contestuale in
   alto a destra.
2. Selezionare **Nuova categoria**.
3. Indicare il nome, che deve essere unico in azienda.
4. Scegliere se la categoria richiede la **verifica danni obbligatoria** alla
   riconsegna.
5. Salvare con **Crea categoria**.

Le categorie sono condivise tra tutte le sedi dell'azienda: crearne una a Brescia
la rende disponibile anche a Verona. Una categoria che contiene almeno un modello
non può essere eliminata; va prima svuotata spostando i modelli altrove.

## Aggiungere un modello di mezzo {#aggiungere-modello}

Il modello descrive un tipo di attrezzatura. Va creato una volta sola, prima di
registrare i singoli esemplari.

1. Dalla schermata **Catalogo**, premere **Nuovo** e scegliere **Modello**.
2. Assegnare un nome commerciale chiaro, es. *Generatore diesel 60 kVA*.
3. Selezionare la categoria di appartenenza.
4. Compilare la scheda tecnica: peso, dimensioni, alimentazione, potenza.
5. Caricare almeno una foto, che comparirà sui documenti di noleggio.
6. Indicare se il modello richiede **patentino o abilitazione** da parte del
   cliente.
7. Confermare con **Salva modello**.

Il modello appena creato non è ancora noleggiabile: diventa disponibile solo dopo
che è stata registrata almeno un'unità fisica associata. Un modello senza unità
compare nel catalogo con l'indicazione *Nessun esemplare*.

## Registrare una nuova unità {#registrare-unita}

L'unità è il singolo esemplare fisico. Ogni attrezzatura presente in magazzino
deve corrispondere a un'unità in Rentaly, altrimenti non può essere noleggiata.

1. Aprire la scheda del modello a cui l'esemplare appartiene.
2. Nella sezione **Esemplari**, fare clic su **Aggiungi unità**.
3. Inserire il **codice unità**, oppure lasciare che Rentaly lo generi in
   automatico.
4. Indicare il numero di matricola o telaio del costruttore.
5. Inserire la data di acquisto e il valore di acquisto, usati nei report.
6. Selezionare la sede di appartenenza.
7. Premere **Registra unità**.

L'unità nasce nello stato *Disponibile* ed è immediatamente prenotabile. Il numero
di matricola deve essere univoco in tutta l'azienda: Rentaly lo usa per impedire
che lo stesso esemplare venga registrato due volte in sedi diverse.

## Codice unità ed etichette QR {#codice-unita-qr}

Ogni unità Rentaly ha un **codice unità** univoco, che compare sui contratti, sui
verbali di riconsegna e sull'etichetta applicata all'attrezzatura.

Il codice generato automaticamente segue lo schema `CAT-MOD-NNN`: tre lettere
della categoria, identificativo del modello, numero progressivo a tre cifre. Ad
esempio `GEN-60-004` è il quarto generatore da 60 kVA registrato. Il codice può
anche essere inserito a mano, purché non sia già in uso.

Per stampare l'etichetta con il codice QR:

1. Aprire la scheda dell'unità dal catalogo.
2. Fare clic su **Stampa etichetta**.
3. Scegliere il formato: adesivo 50×25 mm oppure targhetta 100×50 mm.
4. Confermare con **Genera PDF** e stampare il file ottenuto.

Il codice QR contiene il codice unità e permette di richiamare la scheda
inquadrandolo con la fotocamera durante consegna e riconsegna. Il codice unità non
può essere modificato dopo la registrazione, perché compare su documenti già
emessi.

## Impostare la tariffa di noleggio {#impostare-tariffa}

Le tariffe si definiscono sul modello e valgono per tutti i suoi esemplari.
Possono modificarle gli utenti con ruolo **Amministrazione** o **Amministratore di
sistema**.

1. Aprire la scheda del modello e selezionare la scheda **Tariffe**.
2. Premere **Modifica tariffe**.
3. Compilare la tariffa **giornaliera**, quella **settimanale** e quella
   **mensile**.
4. Indicare la **cauzione** richiesta per ogni unità noleggiata.
5. Impostare l'eventuale **tariffa oraria di ritardo** applicata ai rientri fuori
   orario.
6. Salvare con **Applica tariffe**.

Rentaly sceglie automaticamente la tariffa più conveniente per il cliente in base
alla durata: un noleggio di nove giorni viene conteggiato come una settimana più
due giorni se questo costa meno di nove tariffe giornaliere. Le modifiche alle
tariffe non hanno effetto sui contratti già stipulati, che mantengono i prezzi
concordati alla firma.

## Allegare documenti e foto a un'unità {#allegati-unita}

Alla scheda di ogni unità si possono allegare i documenti che ne accompagnano la
vita: certificati, libretti, verbali di collaudo, foto dello stato attuale.

1. Individuare l'esemplare nel catalogo e aprirne la scheda.
2. Scorrere fino alla sezione **Allegati**.
3. Trascinare i file nell'area tratteggiata, oppure premere **Scegli file**.
4. Assegnare a ciascun allegato un tipo: *Certificato*, *Libretto*, *Foto*,
   *Verbale*, *Altro*.
5. Attendere il completamento del caricamento.

Sono accettati file PDF, JPG e PNG fino a **20 MB** ciascuno, per un massimo di 50
allegati per unità. Gli allegati di tipo *Foto* vengono proposti automaticamente
come riferimento durante la verifica dei danni alla riconsegna, per confrontare lo
stato del mezzo prima e dopo il noleggio.

## Mettere un'unità fuori servizio {#fuori-servizio}

Quando un'attrezzatura non è noleggiabile — perché guasta, in riparazione o in
attesa di collaudo — va segnata come non disponibile, così che il calendario non
la proponga più.

1. Individuare l'unità nel catalogo e aprirne la scheda.
2. Premere **Cambia stato** nella barra delle azioni.
3. Scegliere **In manutenzione** oppure **Fuori servizio**.
4. Indicare la motivazione e la data prevista di rientro in servizio.
5. Confermare con **Applica**.

La differenza tra i due stati è gestionale: *In manutenzione* indica una fermata
tecnica temporanea e l'unità compare nei report di manutenzione; *Fuori servizio*
indica una decisione aziendale a tempo indeterminato.

Se l'unità ha prenotazioni future, Rentaly avvisa e ne mostra l'elenco: le
prenotazioni non vengono annullate in automatico e vanno riassegnate a un altro
esemplare.

## Dismettere un'unità {#dismettere-unita}

Un'attrezzatura venduta, rottamata o rubata va **dismessa**, non eliminata: la
dismissione conserva lo storico dei noleggi, necessario per report e contenziosi.

1. Aprire la scheda dell'unità nel catalogo.
2. Premere **Cambia stato** e scegliere **Dismessa**.
3. Selezionare il motivo: *Venduta*, *Rottamata*, *Rubata*, *Restituita al
   fornitore*.
4. Inserire la data di dismissione.
5. Confermare con **Dismetti unità**.

Un'unità dismessa scompare dal catalogo attivo e dal calendario, ma resta
consultabile attivando il filtro **Includi dismesse**. Non è possibile dismettere
un'unità che si trova nello stato *A noleggio*: va prima registrata la riconsegna.
La dismissione è reversibile solo da un **Amministratore di sistema** entro 30
giorni.

## Importare il catalogo da file {#importare-catalogo}

Per il caricamento iniziale del parco mezzi, Rentaly accetta un file di importazione
in formato CSV. La funzione è riservata al ruolo **Amministratore di sistema**.

1. Andare in **Impostazioni › Importazione dati**.
2. Fare clic su **Scarica modello CSV** e compilare il file con i propri dati.
3. Caricare il file compilato con **Seleziona file**.
4. Controllare l'anteprima: Rentaly mostra le prime 20 righe e segnala gli errori
   di formato.
5. Fare clic su **Avvia importazione**.

Il file deve essere codificato in UTF-8, con il punto e virgola come separatore, e
non può superare le **5.000 righe** per importazione. Le colonne obbligatorie sono
categoria, modello, codice unità e sede. L'importazione crea categorie e modelli
mancanti, ma non aggiorna record esistenti: le righe con un codice unità già
presente vengono saltate e riportate nel resoconto finale.

## Messaggi di errore sul catalogo {#errori-catalogo}

Errori che Rentaly mostra durante la gestione del catalogo e come intervenire.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Codice unità già assegnato* | Un altro esemplare usa lo stesso codice nella stessa azienda | Scegliere un codice diverso o lasciare che Rentaly lo generi automaticamente |
| *Matricola già registrata in un'altra sede* | Lo stesso esemplare risulta censito in un altro deposito | Verificare se l'unità va trasferita anziché registrata di nuovo |
| *Il modello non ha esemplari disponibili* | Si sta prenotando un modello privo di unità registrate | Registrare almeno un'unità associata al modello |
| *Categoria non eliminabile: contiene modelli* | Si sta eliminando una categoria non vuota | Spostare i modelli in un'altra categoria, poi ripetere l'eliminazione |
| *Allegato troppo grande* | Il file supera i 20 MB consentiti | Ridurre la risoluzione della foto o comprimere il PDF |
| *Impossibile dismettere un'unità a noleggio* | L'esemplare risulta ancora presso il cliente | Registrare prima la riconsegna, poi procedere con la dismissione |
