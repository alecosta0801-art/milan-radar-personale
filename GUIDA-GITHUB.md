# Milan Radar su iPhone — guida clic per clic

Questa è la procedura principale. Al termine Milan Radar funzionerà dall’iPhone anche con il PC spento. GitHub ospiterà gratuitamente la PWA ed eseguirà i controlli ogni sei ore.

## Prima di iniziare

Ti servono soltanto:

- l’account GitHub che hai già creato e con e-mail confermata;
- lo ZIP di Milan Radar estratto in una cartella sul PC;
- Safari sull’iPhone.

Non servono Python, terminale, Xcode, App Store, token o carta di credito.

## 1. Crea il repository

1. Accedi a [github.com](https://github.com/).
2. In alto a destra premi **+**, poi **New repository**.
3. In **Repository name** scrivi `milan-radar-personale`.
4. Seleziona **Public**. GitHub Pages gratuito usa il sito pubblico.
5. Non aggiungere README, `.gitignore` o licenza: i file sono già pronti.
6. Premi **Create repository**.

Puoi scegliere un altro nome, ma in quel caso cambierà anche l’indirizzo finale.

## 2. Carica i 41 file già pronti

1. Nella pagina del repository vuoto premi **uploading an existing file**. Se non appare, usa **Add file → Upload files**.
2. In Esplora file apri la cartella estratta `MilanRadar-Python`.
3. Seleziona **il contenuto della cartella**, non la cartella esterna e non lo ZIP.
4. Trascina la selezione nella pagina GitHub.
5. Attendi che GitHub mostri **41 file** pronti per il caricamento.
6. Nel messaggio scrivi `Prima versione Milan Radar`.
7. Premi **Commit changes**.

Alla radice del repository devono vedersi direttamente `index.html`, `app.py`, `assets`, `data`, `config`, `editorial`, `calciodove`, `service-worker.js` e `manifest.webmanifest`.

Controllo molto importante: deve esserci anche:

- `.github/workflows/aggiorna.yml`
- `.github/workflows/pubblica.yml`

Se vedi invece una sola cartella `MilanRadar-Python`, i file sono un livello troppo in basso: non attivare Pages finché `index.html` non è alla radice.

## 3. Autorizza gli aggiornamenti automatici

1. Nel repository apri **Settings**.
2. Nel menu a sinistra apri **Actions → General**.
3. Scorri fino a **Workflow permissions**.
4. Seleziona **Read and write permissions**.
5. Premi **Save**.

Questa autorizzazione permette al bot del tuo repository di salvare il catalogo aggiornato. Non crea né espone password.

## 4. Attiva GitHub Pages

1. Sempre in **Settings**, apri **Pages**.
2. In **Build and deployment**, alla voce **Source**, scegli **GitHub Actions**.
3. Torna alla scheda **Actions** del repository.
4. Se GitHub chiede di abilitare i workflow, conferma.
5. Attendi il segno verde accanto a:
   - **Aggiorna catalogo Milan Radar**;
   - **Pubblica Milan Radar**.

Il primo controllo può richiedere alcuni minuti. Dopo l’aggiornamento, la pubblicazione riparte automaticamente con i dati più recenti.

Se il primo aggiornamento era già partito prima di cambiare i permessi e appare rosso, aprilo e premi **Re-run all jobs**.

## 5. Trova l’indirizzo dell’app

Apri **Settings → Pages**. Vedrai un indirizzo simile a:

`https://TUO-NOME-GITHUB.github.io/milan-radar-personale/`

Premi **Visit site** per provarlo. Non devi configurare URL nell’app: tutti i percorsi sono già relativi e funzionano con il nome del tuo repository.

L’indirizzo Pages e i dati pubblicati sono pubblici. Non inserire password, token o dati personali nel repository.

## 6. Installa Milan Radar sull’iPhone

1. Invia l’indirizzo Pages all’iPhone oppure scrivilo direttamente.
2. Aprilo con **Safari**, non dentro il browser incorporato di WhatsApp, Mail o altre app.
3. Attendi che l’interfaccia e il catalogo siano caricati.
4. Premi il pulsante **Condividi** di Safari, il quadrato con la freccia verso l’alto.
5. Scorri e premi **Aggiungi alla schermata Home**.
6. Lascia il nome **Milan Radar** e premi **Aggiungi**.
7. Chiudi Safari e apri la nuova icona **MR** dalla schermata Home.

Da questo momento l’app si apre in una finestra autonoma. Il PC può restare spento.

## Uso normale sull’iPhone

### Aggiornamento automatico

GitHub esegue **Aggiorna catalogo Milan Radar** ogni sei ore. Il workflow:

1. aggiorna il calendario;
2. controlla prima le fonti Milan;
3. convalida 380 gare, 38 fixture Milan, 249 territori e sei emittenti;
4. mantiene prudenti i segnali ambigui;
5. salva soltanto dati validi;
6. ripubblica automaticamente la PWA.

GitHub può avviare i controlli pianificati con qualche ritardo.

### Pulsante “Sincronizza dati”

Nell’app iPhone premi **Sincronizza dati** per scaricare l’ultimo catalogo già verificato online. Il pulsante non esegue Python sull’iPhone e non promette una scansione istantanea delle emittenti.

La data sotto **Aggiornamento online** indica quando è stato generato il catalogo disponibile.

### Controllo immediato manuale

Quando non vuoi attendere il prossimo ciclo:

1. apri GitHub e il repository;
2. apri **Actions**;
3. scegli **Aggiorna catalogo Milan Radar**;
4. premi **Run workflow**;
5. lascia selezionato `main` e premi di nuovo **Run workflow**;
6. attendi il segno verde dell’aggiornamento e poi di **Pubblica Milan Radar**;
7. torna nell’app e premi **Sincronizza dati**.

Non è richiesto alcun comando.

## Funzionamento offline

Dopo almeno un’apertura online, Milan Radar conserva l’interfaccia e l’ultima copia valida. Se la rete manca, mostra **Cache locale** e permette di consultare i dati già scaricati. Naturalmente link esterni e nuove sincronizzazioni richiedono una connessione.

Evita di cancellare i dati dei siti di Safari se vuoi mantenere cache e archivio personale.

## Dati personali nell’app

Le voci create in **⚙ → Aggiungi verifica**:

- restano nel browser dell’iPhone;
- non vengono inviate al repository;
- non sono visibili agli altri visitatori;
- possono essere esportate in JSON.

Il repository, il catalogo automatico e l’URL Pages sono invece pubblici. Non usare i file del progetto per annotazioni personali.

## Se qualcosa non va

### Non vedo i workflow in Actions

Controlla che `.github/workflows/aggiorna.yml` e `.github/workflows/pubblica.yml` siano realmente presenti e che `index.html` sia alla radice.

### “Aggiorna catalogo” è rosso e parla di permesso negato

Ripeti **Settings → Actions → General → Workflow permissions → Read and write permissions → Save**, poi esegui **Re-run all jobs**.

### “Pubblica Milan Radar” è rosso

Controlla **Settings → Pages → Source: GitHub Actions**, poi riavvia il workflow da **Actions**.

### Il sito mostra 404

Attendi il segno verde di **Pubblica Milan Radar**, poi ricarica l’URL indicato in **Settings → Pages**. Non aprire `index.html` direttamente dallo ZIP.

### Non compare “Aggiungi alla schermata Home”

Assicurati di avere aperto l’URL in Safari. Nel menu Condividi usa **Modifica azioni** se la voce è nascosta. Anche se il suggerimento interno è stato chiuso, il comando di Safari continua a funzionare.

### Il workflow pianificato si ferma dopo molto tempo

GitHub può sospendere i workflow pianificati dei repository rimasti inattivi a lungo. Apri **Actions**, riabilita il workflow se richiesto ed esegui una volta **Run workflow**. L’app conserva comunque l’ultimo catalogo valido.

## Sicurezza e limiti

- nessun token è presente nel frontend;
- non servono segreti o API a pagamento;
- Milan Radar non ospita partite e non aggira geoblocchi;
- non usa né suggerisce VPN;
- una fonte raggiungibile non prova una diretta;
- una rilevazione automatica resta da verificare finché mancano gara, canale, territorio, accesso e fonte ufficiale puntuale.
