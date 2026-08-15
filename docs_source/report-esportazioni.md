---
doc_id: report-esportazioni
title: Report ed esportazioni
version: "1.0"
---

# Report ed esportazioni

Come estrarre da Rentaly i dati su utilizzo dei mezzi, fatturato, danni e scadenze,
e come esportarli verso altri strumenti aziendali.

## I report disponibili {#report-disponibili}

Rentaly mette a disposizione quattro report predefiniti, raggiungibili dalla voce
**Report** della barra di navigazione. Non è possibile costruire report
personalizzati: per analisi diverse si esportano i dati grezzi e si elaborano
altrove.

| Report | Risponde alla domanda |
|---|---|
| **Utilizzo mezzi** | Quanto ha lavorato ciascuna attrezzatura nel periodo? |
| **Fatturato per periodo** | Quanto abbiamo fatturato, e su quali categorie? |
| **Danni e addebiti** | Quali danni sono stati rilevati e quanto è stato addebitato? |
| **Scadenze contratti** | Quali noleggi scadono nei prossimi giorni? |

L'accesso ai report dipende dal ruolo: **Amministrazione** e **Amministratore di
sistema** li consultano tutti e possono esportarli; il ruolo **Banco** li vede in
sola lettura; il ruolo **Magazzino** non ha accesso all'area Report.

## Generare un report {#generare-report}

Tutti i report di Rentaly si producono con la stessa sequenza, cambiando i
parametri richiesti.

1. Aprire **Report** dalla barra di navigazione e scegliere il report desiderato.
2. Impostare l'intervallo di date nella barra dei parametri in alto.
3. Selezionare la sede, oppure **Tutte le sedi** se si è abilitati a più depositi.
4. Applicare gli eventuali filtri specifici del report.
5. Premere **Genera**.

L'elaborazione avviene sul momento e richiede pochi secondi per periodi fino a un
anno. I report riflettono i dati al momento della generazione: non esiste una
funzione di aggiornamento automatico, per rivedere numeri cambiati occorre premere
di nuovo **Genera**.

## Report di utilizzo dei mezzi {#report-utilizzo}

Il report di utilizzo misura quanto ciascuna unità è stata effettivamente
noleggiata nel periodo selezionato, ed è lo strumento per decidere acquisti e
dismissioni.

Per ogni unità la tabella riporta: giorni disponibili nel periodo, giorni
effettivamente a noleggio, giorni di fermo per manutenzione e **tasso di utilizzo**,
cioè il rapporto tra giorni a noleggio e giorni disponibili.

I giorni in cui l'unità era in manutenzione o fuori servizio non entrano nel
denominatore: un mezzo fermo un mese per riparazione non risulta sottoutilizzato
per quel periodo. I giorni di preparazione e rientro configurati sul modello sono
invece conteggiati come indisponibilità e riducono il tasso.

Il filtro **Soglia di utilizzo** permette di isolare le unità sotto una certa
percentuale, tipicamente per individuare attrezzature da dismettere o spostare in
un'altra sede.

## Report di fatturato per periodo {#report-fatturato}

Il report di fatturato somma gli importi dei contratti chiusi nel periodo, con
dettaglio per categoria di attrezzatura, per cliente o per sede.

Il criterio di attribuzione è la **data di chiusura del contratto**, non la data di
inizio noleggio né la data di fatturazione: un noleggio iniziato a marzo e chiuso a
maggio compare interamente nel fatturato di maggio. I contratti ancora in corso non
figurano nel report, nemmeno per la quota di giorni già maturata.

Gli importi sono al netto di IVA e comprendono canone di noleggio, penali di
ritardo, addebiti per danni e addebiti per carburante, ciascuno su colonna
separata. Gli abbuoni concessi sono mostrati come valore negativo.

Il report di fatturato non è un registro fiscale: serve a leggere l'andamento
commerciale, non a sostituire i documenti contabili emessi dal gestionale
aziendale.

## Report danni e addebiti {#report-danni}

Questo report elenca i danni rilevati nei verbali di verifica del periodo, con il
relativo esito economico.

Ogni riga riporta contratto, cliente, unità coinvolta, data del verbale, livello di
gravità, descrizione del danno e importo addebitato. Gli addebiti in stato
*Contestato* sono evidenziati e riportati in una colonna separata dagli importi
esigibili.

Tre filtri sono particolarmente utili: **gravità**, per isolare i danni gravi;
**cliente**, per valutare la sinistrosità di un noleggiatore ricorrente prima di
concedere nuovi noleggi; **categoria**, per capire quali tipi di attrezzatura si
danneggiano più spesso.

I danni classificati come *Lievi* compaiono nel report ma con importo zero, perché
rientrano nell'usura normale e non sono addebitabili.

## Report scadenze contratti {#report-scadenze}

Il report scadenze mostra i contratti la cui data di rientro previsto cade nel
periodo selezionato, ed è pensato per organizzare il lavoro dei giorni successivi.

Le righe sono divise in tre gruppi: **rientri previsti**, cioè contratti ancora nei
termini; **in scadenza oggi**; e **già scaduti**, cioè contratti *In corso* la cui
data di rientro è passata senza che sia stata registrata una riconsegna.

Per ogni riga sono indicati numero di contratto, cliente, recapito telefonico,
unità coinvolte e giorni di ritardo accumulati. La colonna **Penale maturata**
mostra l'importo che verrebbe addebitato se il rientro avvenisse nella giornata
corrente.

Lo stesso elenco, limitato alla giornata, compare nel cruscotto all'accesso: il
report serve quando occorre guardare più avanti nel tempo o filtrare per cliente.

## Filtri e intervalli di date {#filtri-report}

Tutti i report Rentaly condividono la stessa barra dei parametri, con alcune
scorciatoie per gli intervalli più usati.

1. Aprire il selettore delle date in alto nella schermata del report.
2. Scegliere un intervallo predefinito — *Mese corrente*, *Mese precedente*,
   *Trimestre*, *Anno in corso* — oppure impostare date personalizzate.
3. Selezionare una o più sedi dal menu a discesa.
4. Applicare i filtri specifici del report scelto.
5. Premere **Genera** per aggiornare i risultati.

L'intervallo massimo consultabile in una sola volta è di **24 mesi**. Per analisi su
periodi più lunghi occorre generare più report ed unirli fuori da Rentaly. Le
combinazioni di filtri usate più spesso si salvano con **Salva filtro**, che le
rende disponibili nel menu a discesa personale dell'utente.

## Esportare un report in CSV {#esportare-csv}

L'esportazione CSV produce i dati grezzi del report, adatti a essere elaborati in
un foglio di calcolo o importati nel gestionale contabile.

1. Generare il report con i parametri desiderati.
2. Premere **Esporta** nella barra in alto e scegliere **CSV**.
3. Selezionare la codifica: **UTF-8** per fogli di calcolo moderni, **Windows-1252**
   per compatibilità con installazioni datate di Excel.
4. Attendere la preparazione del file.
5. Salvare il file proposto dal browser.

Il separatore è il punto e virgola e il separatore decimale è la virgola, secondo
la convenzione italiana. Le date sono in formato `GG/MM/AAAA`. Il file CSV contiene
sempre tutte le colonne disponibili, anche quelle nascoste a schermo, e riporta
nella prima riga l'intestazione dei campi.

## Esportare un report in PDF {#esportare-pdf}

L'esportazione PDF produce un documento impaginato, pensato per essere stampato o
allegato a una comunicazione.

1. Generare il report che si desidera stampare.
2. Fare clic su **Esporta** e selezionare **PDF**.
3. Scegliere l'orientamento: verticale per report con poche colonne, orizzontale per
   quelli larghi.
4. Indicare se includere il grafico riepilogativo mostrato a schermo.
5. Confermare con **Genera PDF**.

Il documento riporta in intestazione il nome dell'azienda, il periodo, la sede e i
filtri applicati, così che resti comprensibile a distanza di tempo. Il piè di
pagina indica data e ora di generazione e l'utente che l'ha prodotto. I report PDF
sono limitati a **200 pagine**: oltre tale soglia Rentaly propone l'esportazione
CSV.

## Report pianificati via email {#report-pianificati}

Rentaly può generare un report a cadenza fissa e inviarlo per email, senza che
nessuno debba accedere al sistema.

1. Generare il report con i filtri che si vogliono rendere ricorrenti.
2. Premere **Pianifica** nella barra in alto.
3. Scegliere la frequenza: *Giornaliera*, *Settimanale* o *Mensile*.
4. Indicare giorno e ora di invio.
5. Inserire gli indirizzi email dei destinatari, separati da virgola.
6. Scegliere il formato dell'allegato tra CSV e PDF.
7. Salvare con **Attiva pianificazione**.

L'intervallo di date diventa relativo alla data di invio: un report mensile
pianificato contiene sempre il mese precedente. Si possono avere al massimo **10
pianificazioni attive** per azienda, gestibili da **Impostazioni › Report
pianificati**. I destinatari non devono necessariamente essere utenti di Rentaly.

## Limiti delle esportazioni {#limiti-esportazioni}

Le esportazioni di Rentaly hanno limiti tecnici precisi, utili da conoscere prima di
impostare un'estrazione di grandi dimensioni.

- Un'esportazione CSV contiene al massimo **50.000 righe**. Superata la soglia, il
  file viene troncato e Rentaly avvisa a schermo: occorre restringere l'intervallo
  di date e generare più file.
- Un'esportazione PDF si ferma a **200 pagine**.
- L'intervallo di date massimo interrogabile è di **24 mesi**.
- Non esiste un'interfaccia di programmazione (API) per prelevare i dati in
  automatico da sistemi esterni: l'esportazione manuale e i report pianificati via
  email sono gli unici canali disponibili.
- Non è possibile esportare allegati, fotografie dei danni o contratti firmati in
  blocco: si scaricano uno alla volta dalla scheda del documento.

Per esigenze di integrazione continuativa con altri gestionali, l'azienda deve
rivolgersi al proprio referente commerciale Rentaly.

## Messaggi di errore sui report {#errori-report}

Errori che Rentaly mostra durante la generazione e l'esportazione dei report.

| Messaggio | Causa | Soluzione |
|---|---|---|
| *Intervallo superiore a 24 mesi* | Le date selezionate coprono un periodo troppo ampio | Ridurre l'intervallo e, se serve, generare più report separati |
| *Esportazione troncata a 50.000 righe* | Il risultato supera il limite del formato CSV | Restringere le date o i filtri e ripetere l'esportazione in più file |
| *Nessun dato per i filtri selezionati* | La combinazione di filtri non produce risultati | Allargare l'intervallo di date o rimuovere i filtri più restrittivi |
| *Limite di pianificazioni raggiunto* | L'azienda ha già 10 report pianificati attivi | Disattivare una pianificazione esistente da Impostazioni › Report pianificati |
| *Report non disponibile per il tuo ruolo* | Il ruolo dell'utente non prevede l'accesso all'area Report | Richiedere la modifica del ruolo a un Amministratore di sistema |
| *Documento PDF troppo lungo* | Il report supera le 200 pagine stampabili | Esportare in CSV oppure restringere l'intervallo di date |
