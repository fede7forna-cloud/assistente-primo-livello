---
doc_id: riconsegna-verifica-danni
title: Riconsegna e verifica danni
version: "1.0"
---

# Riconsegna e verifica danni

Come registrare il rientro delle attrezzature in Rentaly, compilare il verbale di
verifica e addebitare al cliente eventuali danni.

## Il processo di riconsegna {#processo-riconsegna}

La riconsegna in Rentaly è il momento in cui l'attrezzatura rientra fisicamente in
magazzino e viene controllata. Si compone di tre atti distinti: la registrazione
del rientro, la compilazione del verbale di verifica e l'eventuale addebito dei
danni riscontrati.

Registrazione e verbale sono separati perché nella pratica avvengono in momenti
diversi: l'attrezzatura viene scaricata al banco, ma il controllo accurato può
richiedere ore o avvenire il giorno successivo. Finché il verbale non è chiuso,
l'unità resta nello stato *In verifica* e non è prenotabile.

La registrazione del rientro compete al ruolo **Magazzino**; l'addebito economico
dei danni al cliente compete al ruolo **Amministrazione**. Il ruolo **Banco** vede
le riconsegne in sola lettura e non può chiudere il verbale.

## Registrare una riconsegna {#registrare-riconsegna}

La registrazione segna il rientro fisico dell'attrezzatura e ferma il conteggio dei
giorni di noleggio.

1. Andare in **Riconsegne** e premere **Nuova riconsegna**.
2. Identificare il contratto inquadrando il codice QR di un'unità o digitando il
   numero di contratto.
3. Spuntare le unità effettivamente rientrate.
4. Registrare per ciascuna il livello di carburante e la lettura del contatore ore.
5. Indicare data e ora effettive del rientro, se diverse dal momento corrente.
6. Premere **Registra rientro**.

Le unità passano allo stato *In verifica* e il contratto allo stato *In riconsegna*.
Il conteggio dei giorni di noleggio si ferma alla data e ora indicate al punto 5,
non al momento in cui si compila la schermata: registrare un rientro il lunedì
mattina per un mezzo tornato il sabato non fa pagare al cliente il fine settimana,
purché si corregga la data.

## Riconsegna parziale {#riconsegna-parziale}

Quando il cliente riporta solo una parte delle attrezzature noleggiate, si registra
una riconsegna parziale: le unità rientrate escono dal conteggio, le altre restano
a noleggio.

1. Aprire il contratto in stato *In corso* dall'elenco **Contratti**.
2. Premere **Riconsegna parziale**.
3. Selezionare esclusivamente le unità effettivamente rientrate.
4. Compilare per ciascuna carburante e ore di utilizzo.
5. Confermare con **Registra rientro parziale**.

Il contratto resta *In corso* perché non tutte le unità sono rientrate; le unità
riconsegnate passano a *In verifica* e successivamente, chiuso il verbale, a
*Disponibile*. Ciascuna riconsegna parziale genera un verbale a sé, con numerazione
propria. Il conteggio dei giorni si chiude per unità: un esemplare rientrato con
cinque giorni di anticipo viene fatturato per i giorni effettivi.

## Compilare il verbale di verifica {#verbale-verifica}

Il verbale documenta lo stato dell'attrezzatura al rientro ed è il presupposto di
qualsiasi addebito al cliente.

1. Aprire la riconsegna dall'elenco **Riconsegne**, filtrando per *Da verificare*.
2. Selezionare la prima unità e premere **Avvia verifica**.
3. Scorrere la lista di controllo prevista per la categoria, indicando per ogni
   voce *Conforme* o *Non conforme*.
4. Per ogni voce non conforme, descrivere il danno e assegnargli un livello di
   gravità.
5. Allegare le fotografie del danno riscontrato.
6. Ripetere per le altre unità della riconsegna.
7. Chiudere con **Completa verbale**.

La lista di controllo dipende dalla categoria dell'attrezzatura ed è configurata
dall'amministratore. Alla chiusura del verbale, le unità senza danni tornano
*Disponibile*; quelle con danni di gravità media o alta passano automaticamente *In
manutenzione*.

## I livelli di gravità del danno {#gravita-danno}

Rentaly classifica ogni danno riscontrato su tre livelli, che determinano il
comportamento successivo dell'unità e la proposta di addebito.

| Livello | Descrizione | Effetto sull'unità | Addebito |
|---|---|---|---|
| **Lieve** | Usura normale, graffi superficiali, sporco | Torna disponibile | Nessuno |
| **Medio** | Componente danneggiato ma riparabile, parte mancante | Passa in manutenzione | Proposto, a discrezione |
| **Grave** | Danno strutturale, mezzo non riparabile o non sicuro | Passa fuori servizio | Sempre proposto |

L'usura normale non è mai addebitabile: rientra nel costo del noleggio. La
distinzione tra *Lieve* e *Medio* è la riparabilità — se serve un intervento
tecnico o un ricambio, il danno è almeno medio.

Per i danni di livello **Grave**, Rentaly richiede obbligatoriamente almeno due
fotografie e una descrizione di almeno 40 caratteri prima di consentire la chiusura
del verbale.

## Allegare fotografie al verbale {#foto-verbale}

Le fotografie sono la prova documentale del danno e vanno acquisite prima di
chiudere il verbale, perché a verbale chiuso non è più possibile aggiungerne.

1. Nella schermata di verifica, individuare la voce non conforme.
2. Premere l'icona della fotocamera accanto alla descrizione del danno.
3. Scattare la foto direttamente da tablet o smartphone, oppure selezionare un file
   già presente sul dispositivo.
4. Ripetere per ogni angolazione utile, fino a un massimo di 10 foto per danno.

Rentaly affianca automaticamente le foto scattate alla consegna, così da rendere
immediato il confronto prima/dopo. I file accettati sono JPG e PNG fino a **10 MB**
ciascuno; le immagini più grandi vengono ridimensionate automaticamente al
caricamento. Ogni foto conserva data, ora e utente che l'ha acquisita.

## Addebitare un danno al cliente {#addebitare-danno}

L'addebito trasforma un danno rilevato nel verbale in un importo a carico del
cliente. È riservato ai ruoli **Amministrazione** e **Amministratore di sistema**.

1. Aprire il verbale già completato dall'elenco **Riconsegne**.
2. Individuare il danno nella sezione **Danni riscontrati** e premere **Valorizza**.
3. Indicare l'importo, scegliendo tra costo del ricambio, costo di riparazione o
   forfait.
4. Allegare, se disponibile, il preventivo dell'officina.
5. Scegliere se compensare l'importo con la cauzione o fatturarlo separatamente.
6. Confermare con **Addebita al cliente**.

L'addebito confluisce nel riepilogo economico del contratto e viene sottratto alla
cauzione al momento della chiusura. Se l'importo supera la cauzione trattenuta, la
differenza resta come importo da fatturare. Rentaly registra l'utente che ha
valorizzato l'addebito e non consente di modificarlo dopo la chiusura del contratto.

## Gestire la contestazione del cliente {#contestazione-danno}

Se il cliente non riconosce il danno addebitato, la contestazione va registrata:
sospende l'incasso e conserva la traccia della controversia.

1. Aprire il contratto e raggiungere la sezione **Addebiti**.
2. Individuare la riga contestata e premere **Registra contestazione**.
3. Indicare la data della contestazione e riportare le motivazioni del cliente.
4. Allegare eventuale documentazione fornita dal cliente.
5. Salvare con **Conferma contestazione**.

L'addebito passa allo stato *Contestato* e viene escluso dal calcolo della cauzione
da trattenere, così che la restituzione possa avvenire per la parte non
controversa. Il contratto può essere chiuso anche con un addebito contestato
aperto. La contestazione si risolve con **Accogli** — l'addebito viene azzerato — o
con **Respingi**, che lo riporta esigibile.

## Riconsegna in ritardo e penali {#riconsegna-ritardo}

Un rientro oltre la data prevista genera una penale, calcolata da Rentaly sulla
base della tariffa di ritardo configurata sul modello.

Il calcolo segue due regole: fino a **due ore** di ritardo non viene applicata
alcuna penale; oltre le due ore, si applica la tariffa oraria di ritardo fino al
raggiungimento dell'importo di una giornata piena, oltre il quale il ritardo viene
conteggiato come giorni interi di noleggio aggiuntivi.

La penale compare automaticamente nel riepilogo del contratto quando si registra
un rientro successivo alla data prevista. Per annullarla in caso di ritardo
giustificato:

1. Aprire il contratto interessato e raggiungere il riepilogo economico.
2. Individuare la riga **Penale di ritardo** e premere **Abbuona**.
3. Indicare la motivazione dell'abbuono.
4. Confermare con **Applica abbuono**.

L'abbuono richiede il ruolo **Amministrazione** e resta registrato con nome
dell'utente e data.

## Rientro con carburante mancante {#carburante-mancante}

Le attrezzature con motore termico vengono consegnate con il serbatoio pieno e
devono rientrare nelle stesse condizioni. La differenza viene addebitata al
cliente.

Rentaly confronta il livello di carburante indicato alla consegna con quello
registrato al rientro e calcola l'importo moltiplicando i litri mancanti per il
prezzo al litro configurato in **Impostazioni › Parametri noleggio**. Al costo del
carburante si aggiunge il diritto fisso di rifornimento, se previsto.

Il livello si registra in ottavi di serbatoio, non in litri: la schermata di
riconsegna propone un selettore da 0/8 a 8/8. Rentaly converte automaticamente in
litri usando la capacità del serbatoio indicata nella scheda tecnica del modello.
Se la capacità non è compilata, l'addebito non può essere calcolato e va inserito
a mano come danno forfettario.

## Messaggi di errore sulla riconsegna {#errori-riconsegna}

Errori che Rentaly mostra durante la registrazione dei rientri e la verifica danni.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Verbale non chiudibile: danno grave senza fotografie* | Un danno di livello Grave ha meno di due foto allegate | Acquisire le fotografie mancanti, poi ripetere la chiusura |
| *Unità non appartenente al contratto* | Il codice QR letto è di un esemplare non presente su questo noleggio | Verificare il numero di contratto o registrare il rientro sul contratto corretto |
| *Data di rientro anteriore alla consegna* | La data effettiva indicata precede l'uscita del mezzo | Correggere data e ora effettive del rientro |
| *Capacità serbatoio non configurata* | Manca il dato nella scheda tecnica del modello | Completare la scheda del modello, oppure inserire l'addebito carburante come importo forfettario |
| *Addebito non modificabile: contratto chiuso* | Si sta correggendo un importo su un noleggio già chiuso | Richiedere all'Amministrazione una nota di rettifica |
| *Verifica già completata per questa unità* | Il verbale dell'esemplare è stato chiuso da un altro utente | Aggiornare la pagina e consultare il verbale esistente |
