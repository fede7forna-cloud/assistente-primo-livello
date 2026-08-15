---
doc_id: utenti-ruoli-permessi
title: Utenti, ruoli e permessi
version: "1.0"
---

# Utenti, ruoli e permessi

Guida alla gestione degli utenti di Rentaly: quali ruoli esistono, cosa può fare
ciascuno, e come creare, modificare o disattivare un account.

## Panoramica degli utenti in Rentaly {#panoramica-utenti}

In Rentaly ogni persona che accede al sistema ha un proprio account personale,
identificato dall'indirizzo email aziendale. Non esistono account condivisi tra
più persone: ogni operazione registrata nel sistema — un contratto firmato, una
riconsegna verificata, una modifica al catalogo — resta associata all'utente che
l'ha eseguita.

A ogni account è assegnato **un solo ruolo**. Il ruolo determina quali sezioni di
Rentaly l'utente vede nel menu e quali azioni può compiere. Un utente non può
avere due ruoli contemporaneamente: se una persona svolge mansioni diverse, le si
assegna il ruolo più ampio tra quelli necessari.

Ogni account è inoltre collegato a una o più **sedi** dell'azienda. Il ruolo
stabilisce *cosa* l'utente può fare, la sede stabilisce *su quali dati* può farlo.

## I quattro ruoli di Rentaly {#ruoli}

Rentaly prevede quattro ruoli predefiniti. Non è possibile crearne di nuovi né
modificare i permessi di un ruolo esistente.

| Ruolo | A chi è destinato | Ambito principale |
|---|---|---|
| **Magazzino** | Personale che movimenta fisicamente le attrezzature | Catalogo mezzi, calendario disponibilità, riconsegne |
| **Banco** | Operatori che ricevono il cliente e stipulano i noleggi | Contratti di noleggio, calendario, anagrafica clienti |
| **Amministrazione** | Ufficio amministrativo e contabile | Report, fatturazione, addebiti per danni, tutti i contratti |
| **Amministratore di sistema** | Referente informatico dell'azienda | Tutte le aree, più la gestione degli utenti |

Il ruolo **Amministratore di sistema** è l'unico che può creare o modificare altri
account. Ogni azienda deve avere almeno un utente con questo ruolo attivo: Rentaly
impedisce la disattivazione dell'ultimo amministratore rimasto.

## Matrice dei permessi {#matrice-permessi}

La tabella riassume cosa può fare ciascun ruolo di Rentaly in ogni area del
prodotto. **L** indica sola lettura, **LS** lettura e scrittura, **—** nessun
accesso (l'area non compare nel menu).

| Area | Magazzino | Banco | Amministrazione | Amministratore di sistema |
|---|---|---|---|---|
| Catalogo mezzi | LS | L | L | LS |
| Calendario disponibilità | LS | LS | L | LS |
| Anagrafica clienti | — | LS | LS | LS |
| Contratti di noleggio | L | LS | LS | LS |
| Riconsegna e verifica danni | LS | L | LS | LS |
| Addebito danni al cliente | — | — | LS | LS |
| Report | — | L | LS | LS |
| Gestione utenti | — | — | — | LS |

Due permessi meritano attenzione perché sono spesso fonte di richieste di
assistenza: il ruolo **Banco** può registrare una riconsegna solo in lettura,
quindi non può chiudere il verbale di verifica danni; e il ruolo **Magazzino**
non vede l'anagrafica clienti, quindi nei contratti visualizza il numero di
contratto ma non i dati anagrafici del cliente.

## Creare un nuovo utente {#creare-utente}

Solo un utente con ruolo **Amministratore di sistema** può creare nuovi account
in Rentaly.

1. Da **Impostazioni › Utenti**, fare clic su **Nuovo utente** in alto a destra.
2. Compilare i campi obbligatori: nome, cognome ed email aziendale. L'email sarà
   il nome utente per l'accesso e non potrà essere modificata in seguito.
3. Selezionare il **ruolo** dall'elenco a discesa.
4. Selezionare una o più **sedi** a cui l'utente avrà accesso. È obbligatorio
   indicarne almeno una.
5. Fare clic su **Crea utente**.

Rentaly invia automaticamente all'indirizzo indicato un'email di attivazione con
un link valido **72 ore**. Finché l'utente non completa l'attivazione impostando
la propria password, l'account resta nello stato *In attesa di attivazione* e non
consente l'accesso. Se il link scade, l'amministratore può inviarne uno nuovo
dalla scheda dell'utente con il pulsante **Reinvia invito**.

## Modificare il ruolo di un utente esistente {#modificare-ruolo-utente}

Il ruolo di un utente Rentaly può essere cambiato in qualsiasi momento da un
**Amministratore di sistema**, senza dover creare un nuovo account.

1. Aprire **Impostazioni › Utenti** e cercare la persona nell'elenco degli account.
2. Fare clic sul suo nome per aprirne la scheda.
3. Nella sezione **Ruolo e accessi**, fare clic su **Modifica**.
4. Selezionare il nuovo ruolo dall'elenco a discesa.
5. Fare clic su **Salva modifiche**.

Il nuovo ruolo diventa effettivo al successivo accesso dell'utente: se in quel
momento l'utente ha una sessione aperta, continuerà a vedere i permessi
precedenti finché non esegue la disconnessione. Per rendere immediato il
cambiamento, utilizzare il pulsante **Termina sessioni attive** presente nella
stessa scheda.

Il cambio di ruolo non altera in alcun modo i documenti già creati dall'utente:
contratti, verbali di riconsegna e movimenti restano attribuiti a lui.

## Disattivare un utente {#disattivare-utente}

Quando una persona lascia l'azienda, il suo account Rentaly va **disattivato**,
non eliminato. La disattivazione impedisce l'accesso ma conserva lo storico delle
operazioni, necessario per la tracciabilità dei contratti.

1. In **Impostazioni › Utenti**, individuare la persona e aprirne la scheda
   facendo clic sul suo nome.
2. Fare clic su **Disattiva utente** in fondo alla scheda.
3. Confermare l'operazione nella finestra di dialogo.

L'utente disattivato viene immediatamente disconnesso da tutte le sessioni attive
e non compare più negli elenchi di assegnazione. Il suo nome resta però visibile
sui documenti che ha creato, seguito dall'indicazione *(non attivo)*.

Un account disattivato può essere riattivato in qualsiasi momento dalla stessa
scheda con il pulsante **Riattiva utente**; l'utente dovrà impostare una nuova
password al primo accesso.

## Reimpostare la password di un utente {#reimpostare-password}

Se un utente Rentaly non riesce ad accedere, un **Amministratore di sistema** può
avviare la reimpostazione della password. L'amministratore non vede mai la
password dell'utente e non può impostarla al suo posto.

1. Raggiungere l'elenco degli account da **Impostazioni › Utenti**.
2. Aprire la scheda della persona interessata.
3. Fare clic su **Reimposta password** e confermare.

Rentaly invia all'utente un'email con un link di reimpostazione valido **2 ore**.
Le sessioni attive dell'utente restano valide fino alla scadenza naturale, a meno
che l'amministratore non usi anche **Termina sessioni attive**.

L'utente può avviare la stessa procedura in autonomia dalla schermata di accesso
con il collegamento **Password dimenticata**, senza coinvolgere l'amministratore.

## Accesso a più sedi {#accesso-multi-sede}

Nelle aziende che gestiscono più depositi, ogni sede Rentaly ha un proprio
catalogo mezzi, un proprio calendario e propri contratti. Un utente vede
esclusivamente i dati delle sedi a cui è stato abilitato.

1. Nella scheda dell'utente, raggiungibile da **Impostazioni › Utenti**,
   individuare la sezione **Ruolo e accessi**.
2. Fare clic su **Modifica**.
3. Selezionare le sedi desiderate nell'elenco a scelta multipla.
4. Fare clic su **Salva modifiche**.

Il ruolo assegnato vale in modo identico su tutte le sedi selezionate: non è
possibile, ad esempio, avere ruolo **Banco** in una sede e **Magazzino** in
un'altra.

Un utente abilitato a più sedi le alterna tramite il selettore in alto a destra
nella barra di navigazione. Le operazioni che compie — creazione di un contratto,
registrazione di una riconsegna — vengono attribuite alla sede attiva in quel
momento.

## Autenticazione a due fattori {#autenticazione-due-fattori}

Rentaly supporta l'autenticazione a due fattori (2FA) tramite app di
autenticazione compatibile con lo standard TOTP, ad esempio Google Authenticator
o Microsoft Authenticator. L'invio di codici via SMS non è supportato.

Per attivarla sul proprio account:

1. Fare clic sul proprio nome in alto a destra e selezionare **Profilo**.
2. Aprire la scheda **Sicurezza**.
3. Fare clic su **Attiva autenticazione a due fattori**.
4. Inquadrare il codice QR mostrato a schermo con la propria app di
   autenticazione.
5. Digitare il codice a sei cifre generato dall'app e fare clic su **Conferma**.
6. Salvare in un luogo sicuro i **codici di recupero** mostrati: sono l'unico modo
   per accedere in caso di smarrimento del dispositivo.

Un **Amministratore di sistema** può rendere obbligatoria la 2FA per tutti gli
utenti dell'azienda da **Impostazioni › Sicurezza**. In tal caso, agli utenti che
non l'hanno ancora configurata viene richiesta la configurazione al primo accesso
successivo.

## Registro delle modifiche agli utenti {#registro-modifiche-utenti}

Rentaly registra ogni operazione compiuta sugli account: creazione, cambio di
ruolo, modifica delle sedi, disattivazione, riattivazione e reimpostazione della
password. Il registro è consultabile dai soli **Amministratori di sistema**.

1. Da **Impostazioni › Utenti**, fare clic su **Registro modifiche** in alto a
   destra.
2. Filtrare per intervallo di date, utente interessato o tipo di operazione.
3. Per esportare il risultato, fare clic su **Esporta** e scegliere il formato CSV
   o PDF.

Ogni voce del registro riporta data e ora, l'amministratore che ha eseguito
l'operazione, l'utente interessato e il valore precedente e successivo del campo
modificato. Le voci del registro sono conservate per **24 mesi** e non possono
essere modificate né eliminate.

## Messaggi di errore sulla gestione degli utenti {#errori-utenti}

Errori che Rentaly mostra durante la creazione o la modifica degli account e come
risolverli.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Indirizzo email già utilizzato* | Esiste già un account Rentaly con quella email, eventualmente disattivato | Cercare l'utente includendo i disattivati e, se corrisponde, riattivarlo invece di crearne uno nuovo |
| *Impossibile disattivare l'ultimo amministratore* | Si sta disattivando l'unico Amministratore di sistema attivo | Assegnare prima il ruolo di Amministratore di sistema a un altro utente |
| *Selezionare almeno una sede* | L'utente è stato salvato senza sedi abilitate | Selezionare almeno una sede nella sezione Ruolo e accessi |
| *Link di attivazione non più valido* | Sono trascorse più di 72 ore dall'invio dell'invito | Aprire la scheda dell'utente e fare clic su Reinvia invito |
| *Permessi insufficienti per questa operazione* | Il ruolo dell'utente non prevede l'azione richiesta | Verificare il ruolo necessario nella matrice dei permessi e, se opportuno, richiederne la modifica a un Amministratore di sistema |
