---
doc_id: errori-frequenti
title: Errori frequenti
version: "1.0"
---

# Errori frequenti

Problemi che possono presentarsi in qualunque area di Rentaly — accesso, sessione,
stampa, email, prestazioni — e come risolverli prima di contattare l'assistenza.

Gli errori legati a una singola area del prodotto sono documentati nella pagina di
quell'area: i messaggi sulla creazione degli account nella guida agli utenti,
quelli sul catalogo nella guida al catalogo mezzi, e così via.

## Come leggere un messaggio di errore {#leggere-errore}

Ogni messaggio di errore mostrato da Rentaly contiene tre informazioni utili, ed è
buona pratica annotarle prima di chiudere l'avviso.

- Il **testo del messaggio**, che descrive la causa in linguaggio comune.
- Il **codice**, nella forma `RTY-1234`, riportato in piccolo sotto il testo. Serve
  all'assistenza per identificare con precisione il punto in cui l'errore si è
  verificato.
- L'**ora esatta** in cui il messaggio è comparso.

Gli avvisi con sfondo giallo sono segnalazioni bloccanti ma recuperabili:
l'operazione non è stata eseguita e i dati inseriti restano a schermo. Gli avvisi
con sfondo rosso indicano un errore tecnico: l'operazione potrebbe essere stata
eseguita solo in parte, ed è opportuno ricaricare la pagina e verificare lo stato
prima di riprovare.

## Non riesco ad accedere a Rentaly {#problemi-accesso}

Quando l'accesso viene rifiutato, la causa è quasi sempre una di quattro. Da
verificare in quest'ordine:

1. Controllare che l'indirizzo del browser sia quello della propria azienda, nella
   forma `https://nomeazienda.rentaly.app`. Un indirizzo di un'altra azienda
   rifiuta credenziali valide.
2. Verificare che l'email digitata sia quella aziendale usata per l'invito, non un
   indirizzo personale.
3. Se il messaggio indica *Account non attivo*, l'account è stato disattivato da un
   amministratore oppure l'invito iniziale non è mai stato completato.
4. Se il messaggio indica *Credenziali non valide*, usare **Password dimenticata**
   nella schermata di accesso per ricevere un link di reimpostazione.

Dopo **cinque tentativi** falliti consecutivi, Rentaly blocca l'account per 15
minuti come misura di sicurezza. Il blocco si risolve da solo allo scadere del
tempo; un amministratore può rimuoverlo prima reimpostando la password
dell'utente.

## Sessione scaduta durante il lavoro {#sessione-scaduta}

Rentaly chiude la sessione dopo **8 ore di inattività**. Alla ripresa compare
l'avviso *Sessione scaduta, effettua di nuovo l'accesso* e la schermata torna al
modulo di autenticazione.

I dati non ancora salvati vanno persi: un contratto in compilazione non confermato
con il pulsante di salvataggio non viene conservato. Rentaly non salva bozze
automatiche.

La sessione può interrompersi prima delle 8 ore in tre casi: un amministratore ha
usato **Termina sessioni attive** sull'account; la password è stata modificata da un
altro dispositivo; l'utente è stato disattivato. In tutti e tre i casi il rientro
richiede semplicemente un nuovo accesso, con la password aggiornata dove pertinente.

## La pagina resta in caricamento o non si aggiorna {#pagina-bloccata}

Se una schermata di Rentaly resta con l'indicatore di caricamento o mostra dati
palesemente vecchi, il problema è quasi sempre locale al browser.

1. Ricaricare la pagina forzando lo svuotamento della cache con `Ctrl+F5` su
   Windows o `Cmd+Shift+R` su Mac.
2. Se il problema persiste, chiudere e riaprire la scheda del browser.
3. Provare in una finestra di navigazione privata: se lì funziona, la causa è
   un'estensione del browser o la cache.
4. Disattivare temporaneamente le estensioni di blocco pubblicità e riprovare.
5. Verificare la connessione aprendo un altro sito.

Rentaly richiede una delle due versioni più recenti di Chrome, Edge, Firefox o
Safari. Con browser più datati alcune schermate restano vuote senza mostrare alcun
messaggio: in caso di comportamenti inspiegabili, controllare la versione in uso
prima di ogni altra verifica.

## Le email di Rentaly non arrivano {#email-non-arrivano}

Rentaly invia email per gli inviti ai nuovi utenti, la reimpostazione delle
password, i report pianificati e le notifiche di rientro previsto.

Se un destinatario non le riceve, verificare nell'ordine:

1. La cartella della posta indesiderata del destinatario.
2. L'esattezza dell'indirizzo nella scheda dell'utente o nella pianificazione del
   report.
3. Eventuali regole del filtro antispam aziendale che bloccano il mittente
   `notifiche@rentaly.app`.
4. Che il destinatario abbia attive le notifiche nelle preferenze del proprio
   profilo, se si tratta di una notifica e non di un invito.

Il tempo normale di recapito è entro **cinque minuti**. Se l'email non arriva dopo
un'ora, e le verifiche precedenti non hanno dato esito, conviene chiedere al
proprio reparto informatico di autorizzare in modo esplicito il dominio
`rentaly.app` sul server di posta aziendale.

## Problemi di stampa e apertura dei PDF {#problemi-stampa}

Contratti, verbali, etichette e report vengono prodotti da Rentaly come file PDF
generati sul momento e aperti in una nuova scheda del browser.

Se dopo aver premuto un pulsante di stampa non accade nulla, la causa più frequente
è il blocco delle finestre pop-up: il browser impedisce l'apertura della nuova
scheda senza mostrare alcun avviso evidente. Autorizzare le finestre pop-up per
l'indirizzo di Rentaly nelle impostazioni del browser risolve il problema.

Se il PDF si apre ma risulta vuoto o incompleto, attendere qualche secondo e
ricaricarlo: i documenti con molte fotografie richiedono più tempo di generazione.
Per le etichette con codice QR, verificare che la stampa sia impostata al **100%**
e non su *Adatta alla pagina*: il ridimensionamento rende il codice illeggibile ai
lettori ottici.

## Il codice QR non viene letto {#lettore-qr}

Durante consegna e riconsegna, le unità si identificano inquadrandone l'etichetta
con la fotocamera del tablet o con un lettore ottico.

Se la lettura non riesce:

1. Pulire l'etichetta: polvere, grasso e cemento sono la causa più comune.
2. Migliorare l'illuminazione ed evitare i riflessi diretti sulla superficie.
3. Allontanare leggermente la fotocamera: a distanza troppo ravvicinata l'immagine
   resta sfocata.
4. Verificare che il browser abbia il permesso di usare la fotocamera del
   dispositivo.
5. Se l'etichetta è rovinata, digitare a mano il codice unità nel campo di ricerca.

Un'etichetta danneggiata va ristampata dalla scheda dell'unità nel catalogo. Il
codice unità resta lo stesso: la nuova etichetta è identica alla precedente e non
richiede alcuna modifica ai documenti già emessi.

## Modifiche non salvate {#modifiche-perse}

Rentaly non salva automaticamente ciò che si sta compilando: i dati vengono
registrati solo premendo il pulsante di conferma della schermata.

Quando si tenta di lasciare una pagina con modifiche non salvate, il browser mostra
un avviso di conferma. L'avviso non compare in due casi: se la sessione è già
scaduta, e se la scheda del browser viene chiusa bruscamente.

Se due utenti modificano lo stesso documento contemporaneamente, Rentaly applica la
regola dell'ultimo salvataggio e avvisa il secondo utente che il documento è
cambiato nel frattempo, proponendo di ricaricarlo. Ricaricare fa perdere le
modifiche non ancora confermate: conviene annotarle prima di procedere.

Per i documenti lunghi, come un verbale di verifica con molte unità, conviene
salvare a tratti anziché compilare tutto in un'unica sessione.

## Rentaly è lento {#prestazioni}

Un rallentamento generalizzato ha in genere una causa esterna a Rentaly. Prima di
segnalarlo, provare a circoscriverlo.

1. Aprire un altro sito per verificare che la connessione sia complessivamente
   reattiva.
2. Provare da un altro dispositivo collegato alla stessa rete: se lì è veloce, il
   problema è sul primo computer.
3. Provare da una rete diversa, ad esempio l'hotspot di un telefono: se lì è
   veloce, il problema è sulla rete aziendale.
4. Chiudere le schede del browser inutilizzate: le schermate di calendario con
   molte unità consumano memoria.
5. Verificare se il rallentamento riguarda tutte le schermate o solo una.

Alcune operazioni sono lente per natura e non indicano un malfunzionamento: la
generazione di un report su 24 mesi, l'importazione di un catalogo di migliaia di
righe, la produzione di un PDF con molte fotografie allegate.

## Segnalare un problema all'assistenza {#segnalare-problema}

Quando le verifiche non risolvono, la segnalazione va aperta dall'interno di
Rentaly, così che porti con sé le informazioni tecniche di contesto.

1. Fare clic sul punto interrogativo in alto a destra nella barra di navigazione.
2. Scegliere **Segnala un problema**.
3. Descrivere cosa si stava facendo, cosa ci si aspettava e cosa è successo invece.
4. Riportare il codice dell'errore, se ne è comparso uno, e l'ora esatta.
5. Allegare una schermata dell'avviso.
6. Inviare con **Invia segnalazione**.

La segnalazione include automaticamente utente, sede, browser e ultima schermata
visitata: non è necessario indicarli a mano. Il riscontro arriva all'indirizzo
email dell'account entro **un giorno lavorativo**. Per i blocchi che impediscono
del tutto il lavoro, l'azienda può contattare il numero di assistenza indicato nel
contratto di servizio.
