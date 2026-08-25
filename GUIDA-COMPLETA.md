# Milan Radar 4.1 — PWA iPhone e motore Python

## Scopo

Milan Radar dà priorità assoluta all’**AC Milan** e risponde, partita per partita, a cinque domande:

1. una delle sei emittenti richieste ha nominato esattamente Milan e avversaria?
2. si tratta della diretta integrale, di una differita, di highlights o di una pagina risultati?
3. qual è il canale o la piattaforma?
4. in quale territorio e con quali requisiti è accessibile?
5. la prova ufficiale è puntuale o esiste soltanto un diritto/schema plausibile?

Le sei aree monitorate sono:

- **RSI LA 2** — Svizzera;
- **Digi Sport 1–4** — Romania;
- **BBC iPlayer / BBC ALBA** — Regno Unito;
- **ITVX** — Regno Unito;
- **CBS Sports Golazo Network** — Stati Uniti;
- **RTBF Auvio** — Belgio.

Il pannello Milan contiene tutte le 38 gare di Serie A 2026/27. Il confronto generale di 380 partite e 249 Paesi/territori resta disponibile nelle altre schede.

## Uso principale: PWA indipendente su iPhone

La consegna include una Progressive Web App installabile da Safari e pubblicabile gratuitamente con GitHub Pages. I due workflow inclusi:

- eseguono il motore Python online ogni sei ore e anche su richiesta;
- convalidano catalogo e test prima di salvare i dati;
- ripubblicano automaticamente il sito dopo ogni controllo riuscito;
- non espongono token nel frontend.

Dopo la prima pubblicazione apri l’URL Pages in Safari e scegli **Condividi → Aggiungi alla schermata Home**. La PWA usa percorsi relativi, quindi funziona con qualunque nome di repository. Il service worker conserva shell e JSON; il frontend mantiene inoltre l’ultima copia valida nel browser. Il PC non deve restare acceso.

Su GitHub Pages il pulsante è **Sincronizza dati**: scarica il catalogo già prodotto dal workflow. Un browser statico non può avviare Python in sicurezza e il pulsante non finge il contrario. La procedura completa senza terminale è in `GUIDA-GITHUB.md`.

## Avvio facoltativo su Windows senza terminale

1. Estrai l’intero archivio in una cartella normale.
2. Fai doppio clic su `AVVIA-WINDOWS.bat`.
3. Se Windows segnala che Python manca, installa Python 3 da [python.org](https://www.python.org/downloads/) selezionando **Add Python to PATH**.
4. Fai di nuovo doppio clic sul launcher.
5. Il browser apre `http://localhost:8788/`; se la porta è occupata, il launcher ne sceglie automaticamente una delle successive.
6. Lascia aperta la finestra nera durante l’uso.
7. Premi **Aggiorna e verifica**: nella modalità locale Python esegue subito la scansione.

Non sono richiesti `pip`, librerie, chiavi API, account tecnici o comandi. Python serve soltanto per questa modalità locale, non per l’app iPhone ospitata su GitHub.

## Il pannello Milan Radar

La gara iniziale è la prossima partita del Milan in calendario. Puoi cambiarla dal menu oppure dalla striscia delle 38 fixture.

Per ogni emittente la scheda mostra:

- verdetto prudente;
- territorio e lingua;
- canale e orario, se provati;
- disponibilità della partita integrale;
- gratuità reale;
- requisiti di accesso e registrazione;
- stato tecnico delle fonti;
- prova o motivo dell’assenza di conferma;
- collegamento alla fonte ufficiale.

## Stati e regole

### Confermata gratis — `CONFIRMED_FREE`

Richiede una fonte ufficiale che nomini la partita precisa, data, canale/piattaforma e una diretta integrale accessibile senza abbonamento a pagamento nel territorio autorizzato.

Solo questo stato incrementa **Gratis Milan provate**.

### Confermata, non gratis — `CONFIRMED_NOT_FREE`

La diretta integrale è provata, ma l’accesso richiede un abbonamento o altro servizio a pagamento. Digi Sport Romania rientra qui quando il palinsesto prova il canale ma lo streaming resta riservato agli abbonati Digi.

### Probabile / possibile

- `PROBABLE_NOT_FREE`: diritto e schema sono solidi, ma il canale della singola gara manca ancora; l’accesso noto è a pagamento.
- `POSSIBLE_NOT_CONFIRMED`: esiste un pacchetto selettivo o un segnale automatico, ma la partita non è ancora ufficialmente attribuita.

Questi stati non sono promesse di visione.

### Non provata

- `NOT_CONFIRMED`: un controllo puntuale non ha trovato la selezione;
- `NO_EVIDENCE`: non è stata trovata una prova corrente di diritti o copertura utile.

“Non provata” descrive le fonti controllate, non certifica un’assenza mondiale assoluta.

### Contenuto non integrale

- `HIGHLIGHTS_ONLY`: sintesi o clip;
- `TEXT_SCORE_ONLY`: risultato, statistiche o cronaca testuale.

Nessuno dei due può essere contato come partita gratuita.

## Situazione verificata alla consegna

### Milan–Venezia — 28 agosto 2026, evento `401874758`

- **Digi Sport 3**: diretta integrale puntualmente annunciata alle 21:45 locali; streaming riservato agli abbonati Digi Romania. Stato: confermata, non gratis.
- **BBC iPlayer / BBC ALBA**: BBC ha un pacchetto selettivo di 38 gare, ma la fonte conservata non nomina Milan–Venezia. Stato: non confermata.
- **RTBF Auvio**: gara non presente nell’indice live al controllo del 25 agosto. Stato: non confermata.
- **RSI LA 2, ITVX e CBS Golazo**: nessuna diretta gratuita puntuale conservata per questa gara.

### Torino–Milan — 23 agosto 2026, evento `401874932`

- **Digi Sport 3**: diretta integrale confermata ma non gratuita online;
- **CBS Sports Golazo**: highlights; la diretta integrale era indicata su Paramount+;
- **RTBF**: pagina risultato/cronaca, non prova video Auvio.

Queste evidenze sono in `editorial/milan-radar.json` e non vengono ricostruite da semplici parole chiave.

## Che cosa accade con “Aggiorna e verifica”

1. Python aggiorna il calendario Serie A dal feed configurato.
2. Valida 380 eventi, 38 giornate e 10 partite per turno.
3. Identifica nuovamente le 38 gare del Milan.
4. Interroga le 22 fonti registrate; 15 hanno priorità Milan.
5. Nelle fonti abilitate cerca i nomi di entrambe le squadre a distanza ravvicinata.
6. Registra possibili segnali `LIVE`, `HIGHLIGHTS`, `PAID_PLATFORM` e `TEXT_SCORE`.
7. Inserisce i risultati in una coda di revisione con `automaticConfirmation: false`.
8. Unisce le sole evidenze editoriali puntuali validate.
9. controlla territori, URL, stati, fixture, broadcaster e regole di gratuità.
10. Sostituisce i JSON soltanto dopo una convalida riuscita.

Un nuovo palinsesto può quindi produrre automaticamente un **Nuovo segnale da verificare** nel pannello. Non viene promosso automaticamente a “confermato”: pagine come CBS possono mescolare Golazo gratis, Paramount+ a pagamento e highlights, quindi la promozione cieca sarebbe inaffidabile.

## Le 15 fonti prioritarie

Il registro controlla:

- live e FAQ territoriali RSI;
- palinsesti Digi Sport 1, 2, 3 e 4 e condizioni di accesso;
- annuncio diritti BBC e requisiti iPlayer;
- indice sport ITVX e riferimento storico Serie A;
- palinsesto Golazo e comunicato diritti CBS/Paramount;
- indice live RTBF Auvio e pagina risultati Milan.

Altre 7 fonti ereditate mantengono il confronto generale. Nella scheda **Fonti**, le prioritarie Milan sono evidenziate.

`OK` o `CHANGED` significa solo che la pagina è tecnicamente raggiungibile. Non dimostra né gratuità né diretta integrale.

## Territorio e definizione di “gratis”

È ammessa una diretta integrale accessibile senza abbonamento a pagamento nel territorio autorizzato. Sono compatibili, se dichiarati:

- account gratuito;
- pubblicità;
- canale FAST;
- free-to-air;
- licenza TV obbligatoria;
- dispositivo compatibile.

Sono esclusi:

- prove promozionali;
- servizi inclusi solo in un altro abbonamento;
- VPN, proxy o aggiramenti geografici;
- streaming non ufficiali;
- highlights, radio, programmi studio e live testuali.

Milan Radar non modifica la posizione dell’utente e non suggerisce VPN. RSI, per esempio, limita il live alla Svizzera e dichiara controlli anche contro l’uso di VPN; BBC iPlayer richiede Regno Unito, account BBC e licenza TV per il live.

## Confronto mondiale

`config/countries.json` contiene i 249 codici ISO 3166-1 alpha-2. La scheda **249 Paesi** separa:

- conferme puntuali;
- programmi selettivi in attesa;
- elementi da verificare;
- nessuna conferma trovata.

Non esiste una fonte ufficiale mondiale, gratuita e completa di ogni palinsesto. Il confronto mostra quindi l’estensione reale del catalogo e le sue lacune, senza inventare copertura.

## Aggiornamento locale e online

### Locale

Con Python attivo, il pulsante chiama `POST /api/refresh`: i controlli vengono eseguiti subito e il catalogo viene ricaricato.

### GitHub Pages / iPhone

Un sito statico non può eseguire Python nel browser. `aggiorna.yml` esegue l’aggiornamento online ogni sei ore o manualmente; `pubblica.yml` parte sia dopo i caricamenti sia al completamento dell’aggiornamento, evitando di dipendere da un secondo evento `push` del token GitHub. Il pulsante **Sincronizza dati** scarica l’ultimo catalogo già prodotto. Segui `GUIDA-GITHUB.md` per la configurazione guidata.

## Archivio personale

In **⚙ Impostazioni → Aggiungi verifica** puoi conservare localmente una conferma per una partita precisa. L’elemento:

- resta separato dal catalogo pubblico;
- vive nel `localStorage` del browser;
- può essere esportato/importato in JSON;
- non trasforma una rilevazione automatica in prova editoriale.

## Struttura tecnica

- `index.html`, `assets/app.css`, `assets/app.js`: interfaccia PWA responsive;
- `manifest.webmanifest`, `service-worker.js`, `assets/icon-*.png`: installazione e copia offline;
- `.github/workflows/aggiorna.yml`: controllo Python automatico ogni sei ore e manuale;
- `.github/workflows/pubblica.yml`: pubblicazione Pages iniziale e post-aggiornamento;
- `app.py`: avvio locale semplice;
- `calciodove/server.py`: server locale e API;
- `calciodove/calendar.py`: calendario e validazione;
- `calciodove/sources.py`: controllo fonti e rilevazione prudente;
- `calciodove/catalog.py`: modello Milan Radar e catalogo mondiale;
- `calciodove/updater.py`: sequenza di aggiornamento;
- `editorial/milan-radar.json`: sei profili ed evidenze puntuali Milan;
- `editorial/catalogo-editoriale.json`: catalogo generale separato;
- `config/fonti.json`: 22 fonti, 15 prioritarie Milan;
- `data/catalogo-tv.json`: dati letti dall’interfaccia;
- `data/coda-revisione.json`: segnali automatici non confermati;
- `tests/test_core.py`: invarianti e smoke test.

Il progetto usa soltanto la libreria standard Python 3.10+.

## Garanzia realistica

Milan Radar è definitivo come metodo: priorità Milan, fonti dichiarate, stati separati, convalida, tracciabilità e nessuna promozione automatica di indizi ambigui. Non può garantire al 100% una selezione prima che l’emittente pubblichi il proprio palinsesto, né aggirare Cloudflare, CAPTCHA, geoblocchi o paywall. Quel limite è mostrato esplicitamente, non nascosto.
