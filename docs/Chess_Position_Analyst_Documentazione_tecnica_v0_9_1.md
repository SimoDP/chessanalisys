# Chess Position Analyst — Documentazione tecnica v0.9.1

*Titolo provvisorio. App locale, indipendente, con un solo scopo: data una posizione e un livello Elo, produrre la migliore analisi testuale possibile.*

**v0.9.1** è la v0.9 dopo un audit di coerenza (elenco in §0.7, D-63). **v0.9** è la versione **esecutiva**. La v0.8.2 aveva fissato l'architettura; la v0.9 la lascia invariata e chiude tutto ciò che la v0.8.2 lasciava alla scelta di chi implementa: punto di vista e unità dei valori nel pacchetto (§6), algoritmo di analisi a profondità minima (§3.1), ordine e tempi delle fasi (§3-ter), selezione delle candidate passo per passo (§3-ter.3), definizioni operative di tutte le feature (§5.1), grammatica completa dei token con le regole di resa (§9-bis), colonne e righe delle tabelle T1–T4 (§8.5), budget di parole per sezione e regola di conteggio (§8.4, §9-bis.8), protocollo di retry con il modello (§9.3), contenuto integrale dei file di configurazione (Appendice D), prompt di sistema (Appendice E), schema dello strumento (Appendice F), fixture dei test (Appendice G). Il procedimento per gli esempi golden è stato reso eseguibile (§8-bis) e la milestone M1 è divisa in tre parti con dipendenze esplicite (§13). L'elenco completo delle modifiche è in §0.6 (decisioni D-37…D-62).

**v0.8.2** era la versione di congelamento: regola unica sulla saturazione di Maia-2, token `plan`, titoli e fusioni per fascia, livelli di E3, fase E2b, M1a/M1b (D-24…D-36). **v0.8.1** ha reso il documento consegnabile a Claude Code (ingresso FEN/PGN, Maia-2, output strutturato, SectionPlan, criteri testabili, milestone).

---

## Come usare questo documento (istruzioni per Claude Code)

1. Leggi tutto prima di scrivere codice, comprese le appendici: **le appendici D–G sono normative** (contenuto dei file di configurazione, prompt, schema, fixture) e vanno copiate nel repository così come sono, salvo i valori che §0.5 dichiara modificabili.
2. In caso di conflitto prevale il registro delle decisioni (§0.3); tra due decisioni vale quella con ID più alto.
3. Lavora **una milestone alla volta** nell'ordine di §13 (M0 → M1a → M1b → M1c → M2 …). Non implementare ciò che appartiene a milestone successive; lascia solo l'interfaccia (classe astratta o stub) quando serve, e rifiuta esplicitamente le opzioni non ancora disponibili (D-30).
4. **Non inventare versioni, API o pesi.** Dove il documento descrive un'API esterna (Stockfish via `python-chess`, Maia-2, Anthropic, banca dati delle aperture) la descrizione è marcata come *attesa*: la verifichi dalla fonte ufficiale, la isoli nell'adattatore indicato e annoti le differenze in `docs/MAIA2_NOTES.md` o `docs/OPEN_QUESTIONS.md`. Una differenza che resta confinata nell'adattatore **non** è un cambio di progetto.
5. Ogni costante numerica è una **ipotesi di partenza** e vive in `config/*.yaml` (Appendice D), mai nel codice. Le sole eccezioni sono i valori dei pezzi (P = 1, N = B = 3, R = 5, Q = 9) e i limiti di formato della scacchiera.
6. Tutto ciò che è visibile all'utente è in **italiano**; codice, commenti, nomi di variabile, chiavi YAML e JSON in inglese.
7. I test non richiedono motori, rete né chiave API: usano fixture registrate (§12.1, Appendice G). I test che usano motori o rete hanno i marker `engines`, `network`, `llm` e sono esclusi per default.
8. **Il documento è congelato (v0.9.1).** Le decisioni D-01…D-63 non si riaprono. Se in implementazione una premessa si rivela falsa e non rientra tra i parametri modificabili di §0.5, **fermati**: scrivi il problema, la prova e una proposta in `docs/OPEN_QUESTIONS.md` e chiedi all'utente prima di cambiare il progetto.
9. Dubbi minori che non toccano architettura, schema, token o criteri di accettazione: scegli il default indicato (§15.2), annotalo in `docs/OPEN_QUESTIONS.md` e prosegui.
10. Quando un paragrafo dice «vedi Appendice …», l'appendice contiene il valore o il testo esatto da usare.

---

## 0. Cronologia e registro delle decisioni

### 0.1 Cronologia

| Versione | Contenuto |
| --- | --- |
| v0.1 | Idea, architettura, motori, evidence pack, verifica |
| v0.2 | Category Scoring Engine (§5-bis), Maia che filtra le linee di Stockfish |
| v0.3–v0.7 | CLI, prospettiva per colore, modalità *entrambi*, ingresso (FEN / PGN, nella v0.7 scritto «PNG» / esempio), output di riferimento (§8-bis) |
| v0.8 | Ingresso FEN/PGN senza immagini, Maia-2, schema di output e token, piano delle sezioni, esplorazione, raccomandazione, scala Elo, accettazione testabile, milestone |
| **v0.8.1** | Coerenza roadmap (E1 e E3 a un livello in M1, E3 multilivello in M2); AC-10 diviso per livelli (2400 in M2); apertura per EPD in M1; «PNG» chiarito come PGN |
| **v0.8.2** | Congelamento: saturazione di Maia-2 e conversione Elo (D-24, D-25); token `plan` e verifica dei numeri (D-26); titoli/fusioni per fascia e mappa degli esempi (D-27); livelli di E3, K/M/R, E2b e `complexity` (D-28, D-29); opzioni per milestone (D-30); avversario al tratto (D-31); colonne della matrice e definizioni (D-32); parole di prosa (D-33); nomi file ASCII (D-34); M1a/M1b (D-35); chiusure minori (D-36) |
| **v0.9** | Versione esecutiva: valori nel pacchetto e punto di vista (D-39, D-40); grammatica completa dei token (D-41); algoritmi di selezione, esplorazione e tempo (D-42, D-43, D-58); tabelle T1–T4 (D-44); budget per sezione e conteggio parole (D-45); golden e milestone M1a/M1b/M1c (D-49, D-50); verifiche precisate (D-46, D-47, D-51, D-52); configurazioni, prompt, schema e fixture complete (App. D–G) |
| **v0.9.1** | Audit di coerenza: bug YAML sulle chiavi di fascia, bande di valutazione con buco, selezione delle candidate per `pre` (D-63), fase R in modalità avversario, riferimenti rotti, tipo `Table`, registrazioni dei motori (§0.7) |

### 0.2 Problemi della v0.7 e dove sono risolti

| # | Problema | Soluzione | Dove |
| --- | --- | --- | --- |
| 1 | Formato di output del LLM non definito; verifica impossibile su prosa libera | Output JSON con token `{{…}}` e asserzioni tipizzate | §9-bis, §10 |
| 2 | Contenuto «teorico» in contraddizione con «solo dal pacchetto» | Fonte `theory` ammessa, taggata, senza cifre, non verificata | §9, §9-bis.4 |
| 3 | MVP promette un output con radar ma il radar è nella v0.2 | Tabella di disponibilità delle sezioni per milestone | §8.3, §13 |
| 4 | Maia-1 arriva a 1900; `p_up` non definito oltre | Maia-2 unico modello; saturazione ≥ ~2000 gestita | §3.2, §3-bis |
| 5 | Scala Elo non decisa (FIDE/Lichess) | Scala interna Lichess, conversione configurabile | §3-bis |
| 6 | Struttura degli esempi (apertura) applicata a ogni posizione | Profilo di posizione e matrice di applicabilità delle sezioni | §5.2, §8.2 |
| 7 | Esempi con `[MAIA]` e numeri illustrativi usati come few-shot | Esempi riscritti in forma token, scelta dell'esempio più vicino | §8-bis, §9 |
| 8 | Esplorazione dell'albero non specificata; budget incompatibili con i dati degli esempi | Piano di esplorazione con fasi, tetti e profondità minime | §3-ter |
| 9 | «Mossa consigliata» senza regola | Formula deterministica per livello | §4.3 |
| 10 | «Livello di dettaglio 1–5» senza significato | Tabella dettaglio → parole, candidate, linee | §7.2 |
| 11 | Accettazione vaga («confrontabile») | Test AC-01…AC-20 | §12.3 |
| 12 | Dettagli pratici assenti (SO, chiave API, replay, rete) | `doctor`, `rerun`, pacchetto sempre salvato | §2-bis.5, §11 |
| 13 | Candidate: §7 dice 3–5, gli esempi ne elencano 12 | Distinzione «spiegate» e «elencate» | §7.1 |
| 14 | Roadmap «v0.2/v0.3» confusa con le versioni del documento | Milestone M0–M6 | §13 |

### 0.3 Registro delle decisioni

| ID | Decisione | Sostituisce |
| --- | --- | --- |
| D-01 | **Nessun ingresso da immagine.** Rimossi: chiamata di visione, trascrizione, OCR, `--double-read`. Nota: «PNG» nei documenti precedenti indicava la notazione delle mosse, cioè **PGN** | §2-bis.3 v0.7 |
| D-02 | Ingresso: **esempio** (default), **FEN**, **PGN**; per FEN e PGN il testo si **incolla** oppure si indica il **percorso di un file**; il formato del contenuto è riconosciuto automaticamente | §2-bis v0.7 |
| D-03 | **Maia-2** è l'unico modello di comportamento umano. Niente `lc0`, niente Maia-1 | §3.2 v0.7, Q5 |
| D-04 | Maia-2 valuta la **sola posizione** (FEN), non la storia. Il PGN serve a Stockfish (ripetizioni, 50 mosse), all'apertura per sequenza e al contesto, non a Maia | §2-bis.2 v0.7 |
| D-05 | Scala Elo **interna = Lichess** (quella di Maia-2). L'utente dichiara l'Elo nella sua scala (default FIDE); conversione in `config/elo_conversion.yaml` | Q3 |
| D-06 | Sopra la soglia di saturazione di Maia-2 (~2000, da verificare) `p_up` è disattivato e la confidenza di Maia è «bassa» | §3.2 v0.7 |
| D-07 | Nel testo le valutazioni sono **dal punto di vista dell'utente** (positivo = meglio per lui) | nuovo |
| D-08 | Il LLM non scrive mai numeri, valutazioni o mosse-pezzo «libere»: usa **token** risolti dal codice | §8, §10 |
| D-09 | Contenuto `theory` ammesso: tagged, **senza cifre**, non verificato dal motore, con tetto di parole | §9 v0.7 |
| D-10 | Le sezioni da scrivere sono decise da un **SectionPlan** deterministico, non dal LLM | §8 v0.7 |
| D-11 | MVP (M1) **senza** radar e senza «Minacce invisibili»; arrivano in M3 | roadmap |
| D-12 | La **mossa consigliata è calcolata** dal codice, mai scelta dal LLM | nuovo |
| D-13 | Gli esempi few-shot sono in **forma token** (nessun numero letterale); si sceglie l'esempio più vicino all'Elo | §8-bis.5 |
| D-14 | Notazione delle mosse: **SAN inglese** (Nf3, Be3) anche nel testo italiano | nuovo |
| D-15 | Lingua dell'output: **solo italiano** in v1 | Q2 |
| D-16 | Modalità *entrambi*: Elo distinti per colore consentiti (`--elo-white`, `--elo-black`), default uguali | Q9 |
| D-17 | Syzygy: 3-4-5 pezzi obbligatorio, 6 pezzi opzionale, 7 pezzi escluso | Q (§3.3) |
| D-18 | Chiave API **solo** da variabile d'ambiente `ANTHROPIC_API_KEY` | nuovo |
| D-19 | Il pacchetto di evidenze è **sempre salvato**; `chessanalyst rerun` rifà solo LLM e verifica | nuovo |
| D-20 | Il budget è definito da **tempo e profondità minima** (non solo tempo): i profili della v0.7 (30/120/600 s) non bastavano a riprodurre i dati degli esempi | §3.1 v0.7 |
| D-21 | Calibrazione delle costanti di §5-bis rimandata a **M5**, su partite del database aperto Lichess | Q7 |
| D-22 | Eseguibile **multipiattaforma** (Windows/macOS/Linux): niente comandi di shell nel codice, percorsi con `pathlib` | nuovo |
| D-23 | Ripartizione per milestone: **E0, E1, E2, E2b, E4 e E3 al solo livello ℓ1 in M1** (D-28, D-29); E3 ai livelli ℓ2–ℓ3 (profili `standard`/`deep`) e riconoscimento dell'apertura **per sequenza** in M2; in M1 l'apertura è riconosciuta solo per EPD; il criterio AC-10 vale in M1 per 1500 e 1900, per 2400 in M2 | roadmap v0.8 |
| D-24 | **Saturazione di Maia-2, regola unica.** `saturated(elo_maia) := elo_maia ≥ top_bucket_lower`, con `top_bucket_lower` in `config/maia2_limits.yaml` (scritto da M0; segnaposto 2000). Se vero: `maia.confidence = "low"`, `p_up = null`, dichiarazione nel testo (V11), `improbable_error` non assegnata (D-25). Con la conversione segnaposto l'ancora 1900 FIDE (→ 2025 Lichess) e l'ancora 2400 risultano sature: è un esito previsto, non un errore. Nessun ramo di codice o di progetto dipende dall'esito di M0: cambiano solo i valori e il contenuto degli esempi `rendered` | D-06 (precisata) |
| D-25 | Se `p_up` è `null`, `improbable_error` non viene assegnata; `natural_trap`, `hard_move`, `solid`, `practical_alt` usano solo `p_user` e `loss_cp`. Se più categorie valgono, vince la prima nell'ordine della tabella di §4.2 | §4.2 v0.8.1 |
| D-26 | Spinte di pedone, catene di mosse e sequenze di piano si scrivono **solo** con il token `{{plan:…}}` (§9-bis.3). V03 vieta in chiaro anche catene di case (`g4-g5`), puntini (`...b5`), numeri di mossa e **qualunque cifra residua** dopo aver tolto token e case isolate; i conteggi si scrivono in lettere; l'Elo si scrive con `{{elo:user}}`/`{{elo:opp}}` | §9-bis.2, V03 v0.8.1 |
| D-27 | Titoli, fusioni ed esclusioni di sezione **per ancora** (§8.2-bis); l'ordine di §8.1 è normativo; posizione delle tabelle T1–T4; mappa file raw → sezioni (§8.2-ter); gli esempi `rendered` sono il **target completo** (profilo `deep`), l'output di M1 ne è un sottoinsieme | nuovo |
| D-28 | **Livelli di E3**: ℓ1 (dopo candidata e risposta, tocca all'utente), ℓ2 (dopo la mossa seguente dell'utente, tocca all'avversario), ℓ3 (dopo la risposta successiva, tocca all'utente). Profili: `fast` ℓ1, `standard` ℓ1–ℓ2, `deep` ℓ1–ℓ3; **M1 limita tutti i profili a ℓ1**. `K`, `M`, `R` definiti (§3-ter, §7.1). Profilo di riferimento per gli esempi: `deep` | D-23 (precisata) |
| D-29 | **Fase E2b e `complexity`.** `complexity` conta le mosse obbligate (gap ≥ 100 cp con `MultiPV` 2) nei nodi «tocca all'utente» lungo la PV, calcolati dalla fase E2b. `explained` = prime `K` entro `L_max` + mossa più probabile di Maia-2 (anche oltre `L_max`); la raccomandata è `argmax rec_score` **tra le `explained`** con `loss ≤ L_max`. I giudizi su quale mossa preferire nei file raw non sono vincolanti | §3-ter.3, §4.3 v0.8.1 |
| D-30 | Fino a M3 «entrambi» (`--elo-white`, `--elo-black`) e dettaglio ≠ 4 sono **rifiutati** con messaggio esplicito e codice di uscita 2; mai ignorati in silenzio | nuovo |
| D-31 | **Avversario al tratto**: ID `R<n>` per le risposte, `R<n>.u<k>` per le migliori risposte dell'utente; token dedicati; blocco `replies` nel pacchetto; S07 alternativa; E2b/E3 non eseguite; S08 omessa; nessuna raccomandazione; criterio AC-21 | §2-bis.6 v0.8.1 |
| D-32 | Funzione `matrix_column(profile)` e definizioni operative di `tactical`, `quiet`, `hanging_piece`, `unresolved_capture`; la colonna 1 della matrice diventa «Apertura o mediogioco non tattico» | §5.2, §8.2 v0.8.1 |
| D-33 | Le «parole di prosa» e il budget di V07 contano **tutto** il testo scritto dal LLM, comprese le celle di testo delle tabelle e le didascalie | §7.1 v0.8.1 |
| D-34 | Nomi di file e cartelle solo ASCII, senza spazi, `:` né trattini lunghi. La documentazione si chiama `Chess_Position_Analyst_Documentazione_tecnica_v0_8_2.md` | §8-bis.1 v0.8.1 |
| D-35 | M1 è diviso in **M1a** (fino a `pack.json`, senza LLM) e **M1b** (LLM, verifica, render) | §13 v0.8.1 |
| D-36 | Chiusure minori: priorità tra categorie (D-25); riuso della cache con `MultiPV` e profondità ≥ richiesti (§3-ter.4); conversione di esempio 1900 FIDE → 2025 e non 2040; tabelle indicate per ruolo (`opp_replies`, non `black_replies`) | vari |
| D-37 | **v0.9 versione esecutiva.** L'architettura della v0.8.2 resta; la v0.9 aggiunge solo precisazioni, algoritmi e contenuti normativi (Appendici D–G). Il congelamento si estende a D-01…D-62 | §0.5 v0.8.2 |
| D-38 | **Elo di riferimento.** Fascia di calibrazione (§7) e ancora (§9.2) si calcolano su `elo_ref_fide`, cioè l'Elo dichiarato riportato in scala FIDE (identità se `elo_scale = fide`, conversione inversa se `lichess`). Conversione con interpolazione lineare a tratti ed estrapolazione a offset costante (§3-bis) | §3-bis, §7 v0.8.2 |
| D-39 | **Valori nel pacchetto.** I nodi conservano `eval_white_cp` (punto di vista del Bianco); candidate, risposte e PV espongono `eval_user_cp` (punto di vista dell'utente). Il matto in `n` mosse vale `±(10000 − n)` cp equivalenti e porta anche `mate_user`; valori senza matto con modulo > 10000 sono limitati a ±9999. WDL in per mille dal punto di vista dell'utente | §3.1, §6 v0.8.2 |
| D-40 | **Valutazione di una candidata e di un nodo sono due dati distinti.** `{{ev:C<n>}}` è il valore della riga di E0 (o di E4) alla radice; `{{ev:N<n>}}` è la prima riga dell'analisi propria del nodo. Possono differire di qualche centesimo: i confronti tra candidate usano sempre i token `C` | §9-bis.2 v0.8.2 |
| D-41 | **Grammatica completa dei token** (§9-bis.2): nuovi riferimenti `SAN@N` per mosse in un nodo (`m`, `ev`, `loss`, `pct`), token `diag`, `opening`, `txt`, `elo:…:full`. Un token che punta a un valore `null` è un errore V02 | §9-bis.2 v0.8.2 |
| D-42 | **Selezione delle candidate**: algoritmo esatto di §3-ter.3 (la mossa più probabile di Maia-2 entra al posto dell'ultima delle prime `K`, così il totale non supera mai `K`). E4 valuta le mosse mancanti con una ricerca alla radice ristretta (`root_moves`), non analizzando il nodo figlio | §3-ter.3 v0.8.2 |
| D-43 | **Esplorazione eseguibile**: primitiva di analisi a profondità minima con `engine.analysis()` (§3.1.3); ordine di esecuzione E0 → E4 → E1 → E2 → E3-ℓ1 → E2b → E2c → E3-ℓ2 → E3-ℓ3; tempo per nodo = quota di fase / nodi pianificati; scadenza globale e ordine di scarto unico (§3-ter.2). E1 è **un solo** nodo di mossa nulla alla radice | §3-ter v0.8.2 |
| D-44 | **Tabelle T1–T4**: righe, colonne per ancora, celle di testo ammesse e formato (§8.5, `config/tables.yaml`). T3 mostra la «mossa di contesto» dell'avversario scelta da un algoritmo (§3-ter.6), non scelta a mano | §8.2-bis v0.8.2 |
| D-45 | **Budget di parole per sezione** da `config/section_budget.yaml` (pesi per ancora, rinormalizzati sulle sezioni presenti). Conteggio delle parole definito in §9-bis.8. Tolleranza = max(25%, 15 parole). Lo sforamento del budget dà un solo retry e poi un avviso, mai la rimozione di testo | §8.4, V07 v0.8.2 |
| D-46 | **La frase di bassa confidenza di Maia-2 è inserita dal render**, all'inizio di S06 e S08 (e in nota a T1), non scritta dal LLM. V11 diventa un controllo deterministico del documento finale | V11 v0.8.2 |
| D-47 | **`refs` rimosso dallo schema di output**: i riferimenti si ricavano dai token. V10 fissa quali token richiede e quali vieta ogni valore di `source` | §9-bis.5 v0.8.2 |
| D-48 | **Quota `theory` per ancora** (1500: 70%, 1900: 50%, 2400: 35%); all'ancora 1500 S08 è sempre presente («errori tipici») e ammette contenuto `theory` | §9-bis.4 v0.8.2 |
| D-49 | **Golden eseguibili.** I file raw sono tre (uno per ancora) più la fonte della guida di calibrazione; M0 rigenera i dati; in M1b i pacchetti golden sono congelati nel repository, i `fewshot/*.json` sono scritti una volta (da Claude Code, con revisione umana) e devono passare la verifica; `rendered/*.md` è **generato** dal render a partire da fewshot + pacchetto | §8-bis.4 v0.8.2 |
| D-50 | **M1 in tre parti**: M1a pacchetto, M1b verifica + render + golden, M1c LLM + retry + `rerun`. Ogni parte inizia solo quando la precedente ha superato i suoi criteri | D-35 |
| D-51 | V03 ammette i letterali di `config/wording.yaml: v03_allowed_literals` (default: `Maia-2`) e vieta le figurine Unicode; le linee geometriche («diagonale a7–g1») si scrivono con `{{diag:a7-g1}}` | V03 v0.8.2 |
| D-52 | **V09 (contaminazione)** è attivo solo se l'EPD della posizione analizzata differisce da quella dell'esempio few-shot; `_terms.txt` ha alias in inglese per il confronto con il nome dell'apertura nel pacchetto | V09 v0.8.2 |
| D-53 | **Colore predefinito: bianco** (coerente con la posizione d'esempio, in cui tocca al Bianco). La v0.8.2 aveva `black` in `default.yaml`, che sull'esempio avrebbe attivato la modalità «tocca all'avversario» | §11.4 v0.8.2 |
| D-54 | **Avversario al tratto, dettagli**: selezione delle risposte con algoritmo esatto (§2-bis.6); S03 omessa (motivo `opponent_to_move`); E4 copre le mosse con `p_opp ≥ 3%`; T1 alternativa con colonne fisse | D-31 (precisata) |
| D-55 | **Catalogo delle feature con definizioni operative** e milestone di introduzione (§5.1). In M1a si implementa solo il sottoinsieme marcato «M1» | §5.1 v0.8.2 |
| D-56 | **CLI**: codici di uscita fissi (§2-bis.1), precedenza della configurazione (riga di comando > `profile.yaml` > `config/local.yaml` > `config/default.yaml`), libreria `argparse` | §2-bis v0.8.2 |
| D-57 | **Condizioni della matrice precisate**: valori di `castling`, condizione di S04 (qualcuno ha ancora diritti di arrocco), di S03 in posizioni tattiche, di S05 «pezzi coinvolti», di S08 (categorie che contano) | §8.2 v0.8.2 |
| D-58 | **E2b** copre le candidate `explained` con `loss_cp ≤ max(L_max, practical_alt.max_loss)`, così `practical_alt` è sempre valutabile; se il tetto di nodi taglia parte di E2b, `complexity` si calcola sui nodi disponibili e la candidata porta `complexity_partial: true` | §3-ter.2 v0.8.2 |
| D-59 | **Aperture**: unica fonte `lichess-org/chess-openings` (licenza CC0), indice EPD costruito in setup; nessun libro Polyglot. `phase = opening` se la posizione è nell'indice e `fullmove ≤ 15` | §3.3, §5.2 v0.8.2 |
| D-60 | **Cache**: la chiave di Stockfish include la parte di storia rilevante per le ripetizioni; con `Threads > 1` Stockfish non è deterministico, quindi la riproducibilità è garantita solo dalla cache e dalle fixture | §3-ter.4 v0.8.2 |
| D-61 | **Protocollo con l'API**: errori di rete gestiti dal programma (SDK con `max_retries = 0`, tre tentativi con attesa 2/4/8 s); retry di verifica come conversazione con `tool_result` di errore (§9.3); `stop_reason = max_tokens` equivale a V01 | §9.1 v0.8.2 |
| D-62 | **Syzygy dentro Stockfish solo da M2** (`SyzygyPath`); in M0–M1 le tablebase si scaricano e si controllano ma non si usano | §3.3 v0.8.2 |
| D-63 | **Selezione delle candidate per punteggio di preferenza** `pre = −loss + A·100·p_user` (§3-ter.3), non per sola valutazione; bande di valutazione sul modulo (§6.4); chiavi YAML di fascia sempre tra virgolette; fase R in modalità avversario (§2-bis.6); `Table` definita (§6.2); schema dello strumento verificato per equivalenza, non per testo (App. F) | D-42 (precisata) |

### 0.4 Revisione della v0.8.1: dubbi chiusi

| # | Dubbio emerso | Decisione | Dove |
| --- | --- | --- | --- |
| 1 | Con la conversione segnaposto 1900 FIDE → 2025 in scala Lichess: se Maia-2 satura da ~2000 l'ancora 1900 è già «satura» e `p_up` non esiste; il pacchetto d'esempio diceva il contrario (e 2040 non era il valore della tabella) | Regola unica senza rami (D-24); limite in `config/maia2_limits.yaml`; esempi corretti | §3.2, §3-bis, §6 |
| 2 | `improbable_error` richiede `p_up`, che può essere `null`; categorie sovrapposte senza priorità | Non assegnata se `p_up` è `null` (D-25); priorità = ordine della tabella | §4.2 |
| 3 | Le spinte di pedone e i piani («g4-g5», `O-O` dopo Be2) non erano esprimibili con i token né rilevabili da V03; le case contengono cifre ma sono ammesse | Token `plan`, V03 in due passi, nessuna cifra residua, token `elo` (D-26) | §9-bis.2, §10 |
| 4 | Gli esempi golden non corrispondevano a S01–S13 (titoli, sezioni mancanti, ordine, posizione delle tabelle) | Titoli per ancora, fusioni/esclusioni, mappa dei file raw, ordine di §8.1 normativo (D-27) | §8.2-bis, §8.2-ter |
| 5 | «E3 a un livello» ambiguo; `K`, `M`, `R` non definiti; l'esempio 2400 non è riproducibile con `standard` | Livelli ℓ1–ℓ3, `K`/`M`/`R`, profilo di riferimento `deep` (D-28) | §3-ter, §7.1 |
| 6 | `complexity` senza dati per calcolarla; circolarità tra candidate spiegate e raccomandata; `rec_score` d'esempio incoerente con la formula | Fase E2b, definizione operativa, raccomandata scelta tra le `explained`, esempio ricalcolato (D-29) | §3-ter, §4.3, §6 |
| 7 | «Entrambi» e dettaglio 1–5 offerti in M1 ma disponibili da M4 | Rifiuto esplicito fino a M3 (D-30) | §2-bis.1, §7.2 |
| 8 | «Tocca all'avversario» senza ID, token, pacchetto né criterio di accettazione | ID `R<n>`, token, `replies`, AC-21 (D-31) | §2-bis.6, §9-bis.2 |
| 9 | La matrice non copriva il mediogioco né tattico né quieto; `tactical`, `quiet`, `hanging_piece` non definiti | `matrix_column()` e definizioni operative (D-32) | §5.1, §5.2, §8.2 |
| 10 | Le celle di testo delle tabelle contano nel budget di parole? | Sì: tutto il testo scritto dal LLM (D-33) | §7.1 |
| 11 | Nomi dei file raw con «—» e «:» non validi su Windows | Nomi ASCII (D-34) | §8-bis.1, App. A |
| 12 | M1 troppo grande per essere affidato a Claude Code in un passo | M1a (pacchetto) e M1b (testo) (D-35) | §13 |
| 13 | Minori: riuso della cache, nomi delle tabelle, numeri d'esempio | D-36 | §3-ter.4, §6 |

### 0.5 Congelamento: che cosa è fisso e che cosa può cambiare

**Fisso (non si rinegozia in implementazione):** architettura e moduli (§2); registro D-01…D-63; grammatica dei token (§9-bis.2) e schema di output (§9-bis.6, Appendice F); schema del pacchetto (§6.2); elenco, ID, titoli e ordine delle sezioni (§8.1, §8.2-bis); matrice di applicabilità e `matrix_column()` (§8.2, §5.2); definizioni di profilo, feature, classificazione, `complexity` e raccomandazione (§4, §5); algoritmi di selezione e di esplorazione (§3.1.3, §3-ter); struttura delle tabelle (§8.5); controlli V01–V11 (§10); criteri AC-01…AC-35 (§12.3); suddivisione in milestone (§13).

**Modificabile dalla Fase M0 (solo valori, annotati in `docs/MAIA2_NOTES.md` o `docs/golden_diff.md`):** `version_pin` di Stockfish e Maia-2; versione di Python (3.12, oppure 3.11 se `maia2` non si installa sulla 3.12); `config/maia2_limits.yaml`; in `config/exploration.yaml` profondità minime, tempi `B`, fattori di tetto e nodi massimi; `config/elo_conversion.yaml` se arriva una fonte per O-1; nomi esatti dei file da scaricare in `scripts/setup_engines.py`.

**Modificabile dalla Fase M1b (dopo la scrittura dei fewshot):** colonna «Parole di prosa» (`band_params.*.prose_words`), pesi di `config/section_budget.yaml`, `theory_max_share` per ancora, `config/tables.yaml: t1_line_plies`. Ogni modifica è annotata in `docs/golden_diff.md` con la misura che la giustifica.

**Modificabile dalla Fase M5 (calibrazione):** costanti `A`, `B`, `L_max`, `θ`, `k_c`, `w_c`, soglie di §4.2, bande di §6.4, soglie di `quiet`, `tactical`, `context_spread_cp`.

**Se una premessa fissa si rivela falsa** (Maia-2 non eseguibile come descritto, un'API differisce in modo non isolabile nell'adattatore, un criterio di accettazione è irraggiungibile): non si cambia il progetto in silenzio. Si scrive in `docs/OPEN_QUESTIONS.md` il problema, la prova e una proposta, e si chiede all'utente.

### 0.6 Revisione della v0.8.2: punti chiusi nella v0.9

| # | Problema nella v0.8.2 | Decisione | Dove |
| --- | --- | --- | --- |
| 1 | Il pacchetto d'esempio aveva `eval_cp` senza dire da quale punto di vista; il database era «dal Bianco» | Nodi dal Bianco, candidate e testo dall'utente; matti e WDL definiti | D-39, §6.2 |
| 2 | `{{ev:C1}}` e `{{ev:N5}}` davano numeri diversi per la «stessa» mossa (ricerche diverse) senza regola | Due dati distinti, confronti solo con `C` | D-40 |
| 3 | `python-chess` con `Limit(time, depth)` si ferma alla **prima** condizione: «profondità minima» non era implementabile con `analyse()` | Primitiva con `engine.analysis()` e regole di arresto | D-43, §3.1.3 |
| 4 | Ordine delle fasi, tempo per nodo, scadenza globale e ordine di scarto non erano definiti insieme; E2b e E3 non potevano riusare la cache nell'ordine dato | Ordine unico, quote per nodo, scarto unico | D-43, §3-ter.2 |
| 5 | «K candidate + la mossa di Maia» poteva superare `K` e quindi violare AC-11 | Sostituzione dell'ultima | D-42, §3-ter.3 |
| 6 | E4 valutava le mosse di Maia analizzando il nodo figlio: valori non confrontabili con la radice | Ricerca alla radice con `root_moves` | D-42 |
| 7 | `practical_alt` richiede `complexity`, che non era calcolata oltre `L_max` | Copertura E2b estesa | D-58 |
| 8 | Fascia e ancora calcolate su `elo_declared` in scale diverse (1900 Lichess ≠ 1900 FIDE) | `elo_ref_fide` | D-38 |
| 9 | Colonne delle tabelle mai definite; T3 dipendeva da `...Nc6`, scelta umana non riproducibile | Specifica T1–T4 e mossa di contesto | D-44 |
| 10 | Il budget totale non era distribuito tra le sezioni; il conteggio delle parole non era definito; V07 «solo avviso» contraddiceva AC-07 | Pesi per sezione, conteggio, tolleranza, AC-07 riscritto | D-45 |
| 11 | La frase di bassa confidenza poteva essere scritta due volte (LLM e render) | Solo il render | D-46 |
| 12 | `refs` duplicava i token e poteva contraddirli | Rimosso; regole di V10 per `source` | D-47 |
| 13 | La quota `theory` del 45% era incompatibile con l'esempio 1500 (quasi tutto principi) | Quota per ancora | D-48 |
| 14 | `chessanalyst golden` doveva «convertire» prosa in token in modo automatico: non è deterministico; M0 dipendeva dal pacchetto, che nasce in M1a | Golden in due tempi, fewshot scritti e verificati, rendered generato | D-49, D-50 |
| 15 | V03 bocciava «Maia-2» (contiene una cifra) e «diagonale a7–g1» (catena di case) | Letterali ammessi, token `diag` | D-51 |
| 16 | V09 bocciava «Najdorf» o «Scheveningen» anche analizzando proprio la Najdorf; i nomi nel database sono in inglese | V09 condizionato, alias | D-52 |
| 17 | `default.yaml` aveva `color: black`: con la posizione d'esempio si attivava la modalità avversario | Default bianco | D-53 |
| 18 | Modalità avversario: S03 «sistemi» senza candidate; selezione delle risposte con eccedenze non regolata | Precisazioni | D-54 |
| 19 | Feature come `backward_pawn`, `weak_square`, `outpost` senza definizione | Catalogo operativo | D-55 |
| 20 | Codici di uscita, precedenza della configurazione, libreria CLI non fissati | Fissati | D-56 |
| 21 | «L'arrocco decide», «pezzi coinvolti», «mossa classificata» non definiti | Condizioni precise | D-57 |
| 22 | «E1 per entrambi i lati» ambiguo | Un solo nodo di mossa nulla | D-43 |
| 23 | Libro Polyglot e ECO citati senza fonte | Una sola fonte, CC0 | D-59 |
| 24 | Cache e riproducibilità con Stockfish multi-thread | Chiave con storia, riproducibilità da cache | D-60 |
| 25 | Retry: come rimandare gli errori al modello con `tool_choice` forzato | Protocollo con `tool_result` | D-61 |
| 26 | Testata, rapporto finale, formati numerici, prompt di sistema, schema JSON e fixture lasciati da scrivere | Testo normativo | §8.6, §9-bis.7, App. D–G |
| 27 | Errori di contenuto negli esempi raw (risposta «seconda» che era la prima, fianchetto «solo» contro Bd3, «de2») | Raw corretti, divisi per ancora, con intestazione | §8-bis.1 |

### 0.7 Audit della v0.9: difetti trovati e corretti nella v0.9.1

| # | Difetto | Correzione | Dove |
| --- | --- | --- | --- |
| 1 | In PyYAML la chiave `1200_1600` diventa l'intero 12001600: fasce e parametri non si sarebbero mai trovati | Chiavi sempre tra virgolette; il caricatore rifiuta chiavi non stringa | App. D, AC-34 |
| 2 | Bande di valutazione sul valore con segno: −0,15 non cadeva in nessuna banda | Bande sul modulo con suffisso `_plus`/`_minus`; test sui confini | §6.4, D.9, AC-28 |
| 3 | Le candidate spiegate erano le prime `K` per sola valutazione: a fasce basse una mossa naturale ma ottava non poteva essere spiegata né consigliata | Selezione per `pre = −loss + A·100·p_user` | §3-ter.3, D-63, AC-31 |
| 4 | In modalità avversario E2 era «non eseguita» ma i nodi delle risposte dovevano comunque essere analizzati: fase e tempo non definiti | Fase R con la quota di E2+E2b+E3 | §2-bis.6, §3-ter.2, AC-21 |
| 5 | E2b partiva dalla PV di E0 anche per le mosse venute da E4 | PV della riga di provenienza | §3-ter.2 |
| 6 | Tipo `Table` usato nel pacchetto e mai definito | Definito | §6.2 |
| 7 | Riferimenti a §9-bis.2-bis e §3-ter.1 non più esistenti | Corretti | D-26, glossario, §14 |
| 8 | Schema dello strumento «uguale al testo»: impossibile con `pydantic` | Verifica per equivalenza | §9.1, App. F |
| 9 | Un solo sforamento di parole poteva consumare due retry | Un retry per le sole parole | §9.3 |
| 10 | AC-01 richiedeva una risposta valida che nessuna milestone produceva | `good_najdorf_1900.json` = fewshot 1900 (M1b); registrazioni dei motori in M1a | App. G |
| 11 | AC-18 pretendeva la frase fissa in S08 anche quando S08 è omessa | «dove presenti» | AC-18 |
| 12 | c5 citava feature di M3 in una sezione di M2 | Solo feature disponibili | §8.2 |

---

## 1. Obiettivo e principi

**Input (v1):** posizione (esempio fisso Najdorf come default, oppure FEN, oppure PGN) + colore dell'utente (bianco / nero / entrambi) + Elo (opzionale: Elo avversario, default uguale) + livello di dettaglio + profilo di budget.
**Output:** un file Markdown con analisi a sezioni, ciascuna con spiegazione discorsiva calibrata sul livello, più il pacchetto di evidenze e il rapporto di verifica.

Principi, in ordine di priorità:

1. **Correttezza prima dell'eloquenza.** Il LLM non calcola e non valuta: *spiega* dati prodotti dai motori. Ogni mossa, variante, numero e valutazione nel testo proviene dal pacchetto tramite token (D-08).
2. **Il motore dice cosa è vero, Maia-2 dice cosa è umano.** Lo scarto tra i due è il valore aggiunto dell'app (§4).
3. **Calibrazione reale, non cosmetica.** Il livello cambia concetti, profondità di calcolo mostrata e cosa è «importante», non solo il vocabolario.
4. **Offline tranne la chiamata al modello.** Motori, tablebase e database aperture sono locali. La rete serve solo per l'analisi finale (e per scaricare i componenti in fase di setup).
5. **Onestà sui limiti.** L'app dichiara quando Maia-2 è poco affidabile, quando un dato è instabile, quali sezioni ha omesso e perché.

**Non-obiettivi v1:** immagini o scacchiere come ingresso; analisi di intere partite (una posizione per volta); output multilingua; account o cloud; giocare contro l'utente.

---

## 2. Architettura

```
[0 Ingresso: esempio / FEN / PGN]
        │
        ▼
[1 Validazione + conferma] ─► [2 Esplorazione con motori] ─► [3 Feature e profilo posizione]
                                                                        │
[8 Render] ◄── [7 Verifica] ◄── [6 LLM] ◄── [5 Evidence Pack + SectionPlan] ◄─ [4 Punteggi (M3) e raccomandazione]
```

| # | Modulo | Responsabilità |
| --- | --- | --- |
| 0 | Ingresso | Lettura di esempio/FEN/PGN, riconoscimento del formato, scelta della posizione nel PGN (§2-bis) |
| 1 | Validazione | `python-chess`: legalità, normalizzazione FEN, conferma visiva ASCII |
| 2 | Esplorazione | Stockfish (verità oggettiva), Maia-2 (comportamento umano), Syzygy; albero di nodi con cache (§3, §3-ter) |
| 3 | Feature | Tratti posizionali e tattici deterministici + **profilo della posizione** (§5) |
| 4 | Punteggi e raccomandazione | Classificazione umano/oggettivo (§4), mossa consigliata (§4.3), Category Scoring Engine (§5-bis, da M3) |
| 5 | Evidence Pack | JSON strutturato + **SectionPlan** (§6, §8) |
| 6 | LLM | Una chiamata a `claude-sonnet-5-5` con output strutturato (§9, §9-bis) |
| 7 | Verifica | Controlli V01–V11 con retry (§10) |
| 8 | Render | Markdown (poi HTML): sostituzione dei token, tabelle dai dati, rapporto finale |

**Identificatori stabili** (usati in pacchetto, output e log): `N<n>` nodo dell'albero, `C<n>` candidata, `R<n>` risposta dell'avversario, `PV<n>` variante principale, `L<n>` linea filtrata, `T<n>` tabella, `S<nn>` sezione. Gli ID sono assegnati in modo canonico alla costruzione del pacchetto (§6.3), indipendentemente dall'ordine di esecuzione e dalla cache; `R<n>.u<k>` indica le migliori risposte dell'utente alla risposta `R<n>`.

---

## 2-bis. Interfaccia CLI e ingresso della posizione

### 2-bis.1 Flusso utente

```
$ chessanalyst
Colore [bianco/nero, bianco]: bianco
Elo [1900]: 1900            (scala: fide)
Budget [fast/standard/deep, standard]: standard
Posizione da [esempio/fen/pgn] (invio = esempio): pgn

Incolla il PGN (termina con una riga che contiene solo un punto, oppure Ctrl-D / Ctrl-Z+Invio)
oppure scrivi il percorso di un file (.pgn / .txt):
> partite/mia_partita.pgn

  Trovata 1 partita: "Rossi - Bianchi, 2026.09.12", 43 semimosse, risultato *
  Analizzare la posizione finale (invio) oppure indicare la mossa (es. 17b = dopo la 17ª del Nero): 

<scacchiera ASCII + FEN + lato che muove + ultima mossa + apertura riconosciuta>
Confermi? [s/n/correggi]: s
Motori in esecuzione ...  (E0 radice · profondità 21 · 1/24 nodi)
Analisi salvata in output/20261003_1542_sicilian_defense_najdorf_variation/analysis.md
```

Il flusso mostra lo stato di M1–M3: «Colore» non offre `entrambi` e «Dettaglio» non viene chiesto (vale 4) fino a M4 (D-30). Da M4 il prompt diventa `Colore [bianco/nero/entrambi]` e compare `Dettaglio [1-5, 4]`.

**Risposte ai prompt.** Colore: `bianco`/`b`/`w`/`white` → `w`; `nero`/`n`/`black` → `b` (maiuscole indifferenti). Elo: intero entro `config/thresholds.yaml: elo_input` (400–3000). Budget: `fast`/`standard`/`deep`. Una risposta non valida ripete la domanda (massimo `input.max_attempts` volte, poi uscita con codice 3). Invio vuoto = valore proposto.

**Conferma.** `s` prosegue; `n` termina con codice 0 senza analizzare; `correggi` torna alla domanda «Posizione da …» mantenendo colore, Elo e budget.

**Profilo salvato.** Colore, Elo, scala Elo, budget (e dettaglio da M4) sono salvati in `<config_dir>/chessanalyst/profile.yaml` (`platformdirs.user_config_dir("chessanalyst")`) **solo** dal flusso interattivo, dopo la conferma. La volta successiva i valori salvati sono proposti come default. Metodo di ingresso e posizione non entrano mai nel profilo.

**Precedenza della configurazione (D-56).** Per ogni parametro: opzione da riga di comando > `profile.yaml` > `config/local.yaml` > `config/default.yaml`. `chessanalyst analyze` legge anche `profile.yaml` (se esiste) ma non lo scrive mai.

**Opzioni non ancora disponibili (D-30).** Fino a M3: `--color both`, `--elo-white`, `--elo-black` e `--detail` diverso da 4 sono rifiutati con il messaggio «Opzione disponibile da M4» e codice di uscita 2. `--elo-scale chesscom` è rifiutato con «Scala chess.com non ancora configurata» finché `chesscom_to_lichess` è vuota. Nessuna opzione viene mai ignorata in silenzio.

#### Comandi

| Comando | Funzione |
| --- | --- |
| `chessanalyst` | Flusso interattivo sopra |
| `chessanalyst analyze [opzioni]` | Non interattivo (opzioni sotto) |
| `chessanalyst rerun <cartella_output>` | Riusa `pack.json` e rifà solo LLM, verifica e render (D-19, §9.3) |
| `chessanalyst doctor` | Controlla l'ambiente (§11.3) |
| `chessanalyst golden --data` | M0: rigenera i dati dei golden (§8-bis.4) |
| `chessanalyst golden --packs` | M1b: rigenera e congela i pacchetti golden |
| `chessanalyst golden --render` | M1b: verifica i `fewshot/*.json` e genera `rendered/*.md` |

#### Opzioni di `analyze`

| Opzione | Valori | Note |
| --- | --- | --- |
| `--input` | `example` \| `fen` \| `pgn` | default `example`; incompatibile con `--text/--file/--stdin` se `example` (codice 2) |
| `--text "<…>"` / `--file <percorso>` / `--stdin` | — | esattamente una delle tre con `fen`/`pgn`; più di una → codice 2 |
| `--game N` | intero ≥ 1 | obbligatorio se il PGN contiene più partite |
| `--at <spec>` / `--ply N` | §2-bis.4 | alternative tra loro |
| `--color` | `white` \| `black` (`both` da M4) | |
| `--elo` / `--opp-elo` | intero | `--opp-elo` assente = uguale a `--elo` |
| `--elo-scale` | `fide` \| `lichess` (`chesscom` quando configurata) | vale per entrambi gli Elo |
| `--budget` | `fast` \| `standard` \| `deep` | |
| `--detail` | 4 (1–5 da M4) | |
| `--out <cartella>` | percorso | default `output.dir` |
| `--yes` | — | salta la conferma (test e automazione) |
| `--verbose` | — | log `DEBUG` anche su console |

#### Codici di uscita (D-56)

| Codice | Significato |
| --- | --- |
| 0 | Analisi prodotta (anche in modalità degradata, con avvisi nel rapporto) oppure uscita volontaria alla conferma |
| 1 | Errore inatteso (bug): traccia completa in `run.log` |
| 2 | Uso scorretto: opzione sconosciuta, combinazione non valida, opzione non ancora disponibile, formato rilevato diverso da `--input` in modalità non interattiva |
| 3 | Ingresso non valido dopo `max_attempts` tentativi (o subito, in modalità non interattiva) |
| 4 | Ambiente: motore o pesi mancanti, cartella non scrivibile, chiave API assente quando serve |
| 5 | Modello: API irraggiungibile dopo i tentativi o risposta non valida dopo i retry (il pacchetto resta salvato; il messaggio indica `chessanalyst rerun <cartella>`) |

### 2-bis.2 Metodi di ingresso

| Metodo | Come | Storia | Rete |
| --- | --- | --- | --- |
| **esempio** (default) | Invio al prompt: usa `examples/example.fen` (Najdorf) | no | no |
| **fen** | Testo incollato o file | no | no |
| **pgn** | Testo incollato o file | sì | no |

Posizione di esempio (si cambia solo modificando il file): `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6`

**Origine del testo.** Un'unica funzione `read_source(value) -> str`: se `value` (dopo `strip`) è il percorso di un file esistente lo legge in UTF-8 con `encoding="utf-8-sig"` (tollera il BOM); altrimenti lo considera testo incollato. Con `--stdin` legge tutto lo standard input. Nel flusso interattivo la prima riga letta decide: se è un percorso esistente si legge il file, altrimenti si continua a leggere righe fino a una riga che contiene solo `.` oppure alla fine del file (le righe vuote **non** terminano, perché il PGN le contiene).

**Riconoscimento del formato** `detect_format(text) -> "fen" | "pgn"`, dopo `strip`, rimozione del BOM e di un prefisso `FEN:` (maiuscole indifferenti):

1. esattamente una riga non vuota, il cui primo campo (separato da spazi) contiene esattamente 7 caratteri `/`, e che ha da 4 a 6 campi → **FEN**;
2. altrimenti, se il testo contiene una riga che inizia con `[` e termina con `]`, oppure il motivo `\b1\.` → **PGN**;
3. altrimenti errore «Formato non riconosciuto: né FEN né PGN».

**Contraddizione tra metodo e formato.** Nel flusso interattivo: «Hai scelto FEN ma il testo sembra un PGN. Uso PGN? [s/n]»; `n` richiede di nuovo il testo. Con `analyze`: uscita con codice 2 e messaggio che indica il formato rilevato.

**Regola:** dopo un input sbagliato (FEN non valida, PGN illeggibile, file inesistente) non si passa **mai** in silenzio all'esempio. Nel flusso interattivo si spiega l'errore e si richiede l'input (massimo `max_attempts`, poi codice 3); con `analyze` si esce subito con codice 3.

### 2-bis.3 FEN

Validazione con `chess.Board(fen)` (errore di sintassi → `ValueError`) e poi `board.status()`. Accettate FEN con 4 campi (completate con `0 1`) o 5 campi (completata con `1`). Messaggi (in `config/wording.yaml: errors`):

| Condizione (`python-chess`) | Messaggio |
| --- | --- |
| `ValueError` alla costruzione | «FEN malformata: …» con il testo dell'eccezione |
| `STATUS_NO_WHITE_KING` / `STATUS_NO_BLACK_KING` | «Manca il re bianco/nero» |
| `STATUS_TOO_MANY_KINGS` | «Troppi re» |
| `STATUS_TOO_MANY_WHITE_PAWNS` / `…_BLACK_PAWNS` / `…_PIECES` | «Troppi pedoni/pezzi per il Bianco/Nero» |
| `STATUS_PAWNS_ON_BACKRANK` | «Pedone in prima o ottava traversa» |
| `STATUS_BAD_CASTLING_RIGHTS` | «Diritti di arrocco incoerenti con la posizione di re e torri» |
| `STATUS_INVALID_EP_SQUARE` | «Casa di en passant non valida» |
| `STATUS_OPPOSITE_CHECK` | «Il lato che non muove è sotto scacco» |
| `STATUS_TOO_MANY_CHECKERS` / `STATUS_IMPOSSIBLE_CHECK` | «Scacco impossibile» |
| `board.is_checkmate()` / `is_stalemate()` / `is_insufficient_material()` | «Posizione terminale (matto/stallo/materiale insufficiente): non c'è nulla da analizzare» |
| altro stato ≠ `STATUS_VALID` | «Posizione non valida» + nome dello stato |

Il FEN normalizzato è `board.fen(en_passant="legal")` (la casa di en passant compare solo se la presa è legale): è quello che entra nel pacchetto e nelle chiavi di cache.

**Limiti senza storia (esempio e FEN):** nessun rilevamento delle ripetizioni (il contatore delle 50 mosse è nella FEN); il nome dell'apertura si cerca per posizione (EPD).

### 2-bis.4 PGN

Libreria: `chess.pgn`. Regole:

1. **Lettura:** si leggono tutte le partite con `chess.pgn.read_game()` in ciclo. Una partita con `game.errors` non vuota è «illeggibile».
2. **Più partite:** si elencano (indice da 1, Bianco, Nero, Evento/Data, semimosse, risultato) e si sceglie con numero o `--game N`. Una sola → nessuna domanda. Con `analyze` e più partite senza `--game` → codice 2.
3. **Posizione da analizzare** (`--at`, oppure risposta al prompt):
   - invio / assente → fine della linea principale;
   - `<n>w` → dopo la mossa `n` del Bianco (semimossa `2n − 1` contando dalla posizione iniziale standard); `<n>b` → dopo la mossa `n` del Nero (semimossa `2n`); con `[FEN]` iniziale la numerazione segue il `fullmove` e il lato al tratto del tag;
   - `ply:<k>` oppure `--ply k` → dopo `k` semimosse dalla posizione iniziale della partita (`0` = posizione iniziale);
   - espressione regolare: `^(\d+)([wb])$` oppure `^ply:(\d+)$`; un valore fuori dalla partita → errore «La partita ha solo N semimosse».
4. **Posizione iniziale personalizzata:** tag `[SetUp "1"]` + `[FEN "…"]` supportati; il FEN del tag passa la validazione di §2-bis.3 (salvo la regola sulla posizione terminale).
5. **Annotazioni:** commenti, NAG, varianti e tempi sono ignorati; si usa solo `game.mainline_moves()`.
6. **Mosse illegali o illeggibili:** `python-chess` interrompe la linea principale e registra l'errore in `game.errors`. Il messaggio riporta semimossa (numero di mosse lette + 1), numero di mossa e testo: «semimossa 3 (mossa 2 del Bianco): `Nf6` non è legale». Nessun recupero automatico.
7. **Posizione terminale** alla fine scelta → errore con invito a usare `--at`.
8. **Elo nei tag** (`WhiteElo`, `BlackElo`): ignorati fino a M4; da M4 proposti con conferma, chiedendo sempre la scala.
9. **Salvataggio:** la partita troncata alla posizione scelta, senza commenti, con i soli tag `Event`, `Site`, `Date`, `Round`, `White`, `Black`, `Result` (più `SetUp`/`FEN` se presenti), è salvata come `game.pgn` nella cartella di output.

**Effetti della storia (D-04):** a Stockfish si passa la posizione iniziale e le mosse (`python-chess` lo fa passando un `Board` con `move_stack`), così ripetizioni e regola delle 50 mosse sono corrette; il numero di ripetizioni della posizione corrente entra in `history.repetitions`; l'apertura si cerca per EPD (M1) e per sequenza (da M2). **Maia-2 non riceve la storia.**

### 2-bis.5 Conferma e robustezza

- **Conferma obbligatoria** prima dei motori: scacchiera ASCII (`str(board)` con coordinate aggiunte), FEN normalizzato, lato che muove, ultima mossa (se PGN), numero di semimosse, apertura riconosciuta (`ECO nome` oppure «non riconosciuta»), diritti di arrocco ed en passant. `--yes` la salta.
- **Cartella di output** `output/<AAAAMMGG_HHMM>_<slug>/` (ora locale). `slug` = nome dell'apertura in minuscolo ASCII (accenti rimossi con `unicodedata`), ogni sequenza di caratteri non alfanumerici sostituita da `_`, tagliato a 40 caratteri; senza apertura `pos_<primi 8 caratteri esadecimali di sha1(EPD)>`. Se la cartella esiste si aggiunge `_2`, `_3`, …
- **File prodotti:** `analysis.md`, `pack.json`, `llm_raw.json` (tutti i tentativi, in ordine), `verification.json`, `run.log`, `game.pgn` (se PGN). `pack.json` è scritto **prima** della chiamata al modello.
- **Log:** modulo `logging`; `run.log` a livello `DEBUG` (comandi UCI esclusi, salvo `--verbose`), console a livello `WARNING` con `rich`. La chiave API non compare mai nei log.
- **Errori di rete o API:** §9.3.

### 2-bis.6 Prospettiva: colore dell'utente

- **`bianco` / `nero`:** l'analisi è scritta **dal punto di vista dell'utente** (D-07). Feature e linee dell'avversario servono da input (minacce, risposte probabili) ma non hanno sezioni proprie.
- **Elo:** a ogni interrogazione di Maia-2 `elo_self` è l'Elo (in scala Maia) di **chi muove** nel nodo e `elo_oppo` quello dell'altro (§3.2).
- **Tocca all'utente:** sezione *Mosse candidate* (S07).
- **Tocca all'avversario (D-31, D-54):**
  1. E0 sulla radice con `MultiPV` radice; Maia-2 sulla radice con l'Elo avversario → `p_opp` per ogni mossa legale; E4 valuta con `root_moves` le mosse con `p_opp ≥ e4_min_p` non presenti in E0 (massimo `e4_max_moves`).
  2. **Risposte** `R1…Rk`: insieme `P` = mosse con `p_opp ≥ replies_min_p` (5%) e valutazione disponibile, ordinate per `p_opp` decrescente; insieme `B` = le 2 migliori per Stockfish (dal punto di vista dell'avversario). Risultato = `B` ∪ i primi elementi di `P` fino a `K` della fascia in totale; se `|B ∪ P| ≤ K` si prendono tutti. Ordine degli ID: `p_opp` decrescente; a parità, valutazione migliore per l'avversario.
  3. Per ogni `Rj`: analisi del nodo dopo `Rj` (tocca all'utente) con `MultiPV` risposte e Maia-2 all'Elo dell'utente; `Rj.u1…Rj.u3` = le prime tre mosse per valutazione, con `eval_user_cp`, `loss_cp` (rispetto a `Rj.u1`) e `p_user`.
  4. I nodi dei passi 3 formano la fase **R**, che sostituisce E2, E2b ed E3 (quota di tempo = somma delle tre, §3-ter.2; profondità minima `dmin.nodes`; `MultiPV` `multipv.nodes`). Le fasi E2b ed E3 sono registrate in `omitted_phases` con motivo `opponent_to_move`; E2 non compare (è sostituita da R). E1 (mossa nulla alla radice) mostra che cosa farebbe l'utente se avesse il tratto.
  5. `recommendation` è `null`; S03 e S08 sono omesse (motivo `opponent_to_move`); S07 usa il titolo alternativo e la tabella T1 alternativa (§8.5).
- **`entrambi` (da M4):** due analisi indipendenti, una per colore. Stockfish gira una sola volta per nodo (cache condivisa); Maia-2 si ripete per le coppie di Elo diverse. Punteggi, SectionPlan e chiamata al modello sono separati. Un solo `analysis.md` con le due prospettive una dopo l'altra (prima il colore al tratto).

---

## 3. Livello motori (tutto locale)

### 3.1 Stockfish

#### 3.1.1 Installazione e opzioni

- Ultima release stabile ufficiale (repository `official-stockfish/Stockfish`, pagina delle release), **versione fissata** in `engines.stockfish.version_pin` dopo verifica in M0. `scripts/setup_engines.py` sceglie il binario per sistema operativo e CPU (su x86-64 la variante `avx2` se la CPU la supporta, altrimenti la generica; su macOS arm64 la variante Apple Silicon): i nomi esatti dei file si verificano in M0 (§0.5). `doctor` stampa la versione letta da `engine.id["name"]` e avvisa se differisce dal pin.
- Comunicazione UCI con `chess.engine.SimpleEngine.popen_uci(path)` (pacchetto PyPI `chess`, ex `python-chess`). Un solo processo di Stockfish per esecuzione, aperto all'inizio di E0 e chiuso con `engine.quit()` anche in caso di eccezione.
- `engine.configure({"Threads": t, "Hash": h})` con `t = max(1, core_fisici − 1)` (`psutil.cpu_count(logical=False)`, se `None` si usa `os.cpu_count() // 2`) e `h = min(hash_mb, 25% della RAM totale)` arrotondato per difetto alla potenza di 2 in MB (`psutil.virtual_memory().total`). `UCI_ShowWDL` impostato a `true` se l'opzione esiste (`"UCI_ShowWDL" in engine.options`). **`MultiPV` non si imposta con `configure`**: lo gestisce `python-chess` tramite l'argomento `multipv`. `SyzygyPath` solo da M2 (D-62).
- Con `Threads > 1` due esecuzioni identiche possono dare risultati diversi: la riproducibilità è affidata alla cache e alle fixture (D-60).
- Le versioni recenti usano solo NNUE: il comando `eval` non scompone per categoria. Le categorie si ricavano da feature e linee (§5-bis).

#### 3.1.2 Conversione dei punteggi (D-39)

Per ogni riga ricevuta (`info["score"]`, un `PovScore`):

- `s = info["score"].white()`; se `s.is_mate()`: `n = s.mate()` (mosse, positivo = matta il Bianco); `eval_white_cp = 10000 − n` se `n > 0`, `−(10000 + n)` se `n < 0` (cioè `−(10000 − |n|)`); `mate_white = n`. Altrimenti `eval_white_cp = clamp(s.score(), −9999, 9999)` e `mate_white = null`.
- Punto di vista dell'utente: `eval_user_cp = eval_white_cp` se l'utente è il Bianco, altrimenti `−eval_white_cp`; `mate_user` idem.
- WDL: `w = info["wdl"].white()` → `(wins, draws, losses)` in per mille; per l'utente Nero si scambiano `wins` e `losses`. Se il motore non fornisce WDL il campo è `null`.
- Nel database e nella cache si salva solo il punto di vista del Bianco; la conversione all'utente avviene nella costruzione del pacchetto.

#### 3.1.3 Primitiva di analisi a profondità minima (D-43)

`Limit(time=…, depth=…)` di `python-chess` si ferma alla **prima** condizione raggiunta, quindi non garantisce una profondità minima. Tutte le analisi usano invece la funzione:

```
analyse_node(board, multipv, t_target, d_min, t_cap, root_moves=None) -> NodeResult

k = min(multipv, numero di mosse legali)            # oppure len(root_moves)
start = monotonic()
with engine.analysis(board, multipv=k, root_moves=root_moves) as an:   # ricerca infinita
    snapshot = None; lines = {}
    loop:
        elapsed = monotonic() - start
        if elapsed >= t_cap: break
        if snapshot and elapsed >= t_target and snapshot.depth >= d_min: break
        if an.would_block(): sleep(poll_s); continue      # poll_s = 0.05 s
        info = an.get()
        if info.get("lowerbound") or info.get("upperbound"): continue
        if "multipv" not in info or "pv" not in info or "depth" not in info: continue
        lines[info["multipv"]] = info
        if info["multipv"] == k and all(lines[i]["depth"] == info["depth"] for i in 1..k):
            snapshot = copia di lines alla profondità info["depth"]    # iterazione completa
    an.stop()
result = snapshot (se None: ultima iterazione disponibile, marcata unstable_depth)
unstable_depth = snapshot is None or snapshot.depth < d_min
```

- La forma esatta dei metodi (`would_block`, `get`, `stop`, attributi di `info`) si verifica in M0 sulla versione installata di `python-chess`; eventuali differenze restano dentro `engines/stockfish.py`.
- Il risultato registra: profondità e `seldepth` della iterazione usata, nodi, tempo effettivo, `k` righe ordinate per `multipv`, per ogni riga SAN, UCI, `eval_white_cp`, `mate_white`, WDL, PV completa in SAN (convertita con `board.variation_san` su una copia).
- AC-29 verifica la primitiva con un falso motore UCI che emette righe registrate (comprese righe con `lowerbound` e iterazioni incomplete).

### 3.2 Maia-2

Modello unificato (Tang et al., «Maia-2: A Unified Model for Human-Chess Alignment», NeurIPS 2024), PyTorch, condizionato sull'Elo di **entrambi** i giocatori. Repository ufficiale: CSSLab/maia2. L'interfaccia qui sotto è **attesa** e va confermata leggendo il codice installato (D-03):

| Aspetto | Atteso / da verificare |
| --- | --- |
| Installazione | `pip install maia2`; PyTorch CPU sufficiente, GPU opzionale |
| Caricamento | `from maia2 import model, inference`; `m = model.from_pretrained(type="rapid", device="cpu")` (i pesi si scaricano al primo uso: lo fa `setup_engines.py`); `prepared = inference.prepare()` |
| Chiamata singola | `move_probs, win_prob = inference.inference_each(m, prepared, fen, elo_self, elo_oppo)`: `move_probs` = dizionario UCI → probabilità sulle mosse legali; `win_prob` = probabilità di vittoria stimata (**verificare di quale lato**) |
| Chiamata a lotti | `inference.inference_batch(...)` su un DataFrame: verificare firma e colonne |
| Fasce Elo | funzione interna del tipo `create_elo_dict()`/`map_to_category()`: atteso `< 1100` → fascia 0, `1100–1199` → 1, …, `1900–1999` → 9, `≥ 2000` → 10 (fascia più alta) |
| Storia | **nessuna**: input = posizione singola |
| Modelli | `rapid` e `blitz`, addestrati su Lichess; default `rapid` |

**Adattatore `MaiaEngine`** (`engines/maia2.py`, unico modulo che importa `maia2`):

```
policy(fen, elo_self, elo_oppo) -> dict[uci, float]   # tutte le mosse legali, somma 1
expected_score(fen, elo_self, elo_oppo) -> float       # risultato atteso per chi muove, in [0, 1]
bucket(elo) -> int                                      # da config/maia2_limits.yaml
saturated(elo) -> bool                                  # elo >= top_bucket_lower
info() -> {"package_version", "model_type", "device"}
```

- `policy` completa con probabilità 0 le mosse legali assenti dall'output del modello, scarta (con avviso nel log) le mosse non legali e rinormalizza a somma 1. Le chiavi sono UCI del `python-chess` (arrocco `e1g1`); la conversione in SAN avviene fuori dall'adattatore.
- `expected_score` restituisce sempre il valore **per chi muove**; se M0 verifica che `win_prob` è riferito a un altro lato, l'adattatore lo converte.
- Cache SQLite su `(epd, elo_self, elo_oppo, model_type, package_version)`; si usa l'EPD perché il modello ignora gli orologi.
- **Test di M0 (in `docs/MAIA2_NOTES.md`):** per una posizione col Bianco al tratto e una col Nero al tratto tutte le chiavi restituite sono mosse legali; la somma è 1 ± 1e-6; la risposta è identica per due FEN che differiscono solo negli orologi; tempo medio per chiamata su CPU.

**Regole d'uso (D-06, D-24, D-25):**

- **Chi muove decide l'Elo.** A ogni nodo: `elo_self` = Elo Maia di chi ha il tratto in quel nodo, `elo_oppo` = Elo Maia dell'altro.
- **Nodi interrogati:** radice; nodi di E2 (tocca all'avversario); nodi di E3 ℓ1, ℓ2, ℓ3; nodi delle risposte in modalità avversario. Non si interrogano i nodi di E2b, E2c, né il nodo di mossa nulla.
- **`p_user`** = `policy` alla radice per le mosse dell'utente (o nei nodi in cui tocca all'utente). **`p_opp`** = `policy` nei nodi in cui tocca all'avversario.
- **`p_up`** (solo alla radice, solo se tocca all'utente): `elo_up = min(elo_maia + up_delta, elo_max_model)`; si calcola **solo se** `bucket(elo_up) ≠ bucket(elo_maia)`; `p_up_bucket = "top"` se `bucket(elo_up)` è la fascia più alta, altrimenti `"higher"`; se non calcolata `p_up = null` e `p_up_bucket = null`.
- **Saturazione (D-24):** `saturated(elo_maia) := elo_maia ≥ top_bucket_lower` (`config/maia2_limits.yaml`, segnaposto 2000). Se vero: `maia.confidence = "low"`, `p_up = null` (segue dalla regola sopra), `improbable_error` non assegnata, frase fissa inserita dal render (D-46). Altrimenti `maia.confidence = "normal"`. Con la conversione segnaposto l'ancora 1900 (→ 2025) e l'ancora 2400 risultano sature: è un esito atteso.
- La probabilità di vittoria si chiama **`human_expected_score`** (dal punto di vista dell'utente nel pacchetto): risultato atteso *a quell'Elo*, mai confuso con l'eval di Stockfish (V10).
- **Entropia** della policy alla radice in bit: `−Σ p log2 p` sulle mosse con `p > 0` (usata da M3).

### 3.3 Risorse accessorie locali

- **Syzygy (D-17, D-62):** 3-4-5 pezzi obbligatorio (circa 1 GB), 6 pezzi opzionale (circa 150 GB), 7 pezzi escluso. Scaricate da `setup_engines.py` (fonte da verificare in M0), controllate da `doctor` da M0, **usate da M2**: `SyzygyPath` a Stockfish e sonda diretta con `chess.syzygy.open_tablebase()` per WDL e DTZ. Con la tablebase l'esito esatto prevale sull'eval ed è espresso a parole.
- **Aperture (D-59):** unica fonte `lichess-org/chess-openings` (file `a.tsv` … `e.tsv`, colonne `eco`, `name`, `pgn`; licenza CC0), scaricata da `setup_engines.py`. Al setup si costruisce `data/openings_index.json`: per ogni riga si rigioca il PGN e si registra `EPD → {eco, name, plies}`; se più righe portano alla stessa EPD vince quella con più semimosse, a parità l'ordine del file. Ricerca per EPD esatta (M1); per sequenza (M2): la riga più lunga il cui PGN è prefisso delle mosse della partita. Nessun libro Polyglot. `in_book = true` se l'EPD della posizione è nell'indice.
- **Cache SQLite** (`<cache_dir>/chessanalyst/cache.sqlite`, `platformdirs.user_cache_dir`), tabelle:
  - `sf(key TEXT PRIMARY KEY, engine_version, multipv INTEGER, depth INTEGER, result_json, created_utc)` con `key = sha1(engine_version | fen_normalizzato | hist | root_moves_ordinati)`; `hist` = UCI delle mosse dall'ultima mossa irreversibile (cattura o mossa di pedone) se c'è storia, altrimenti stringa vuota (D-60);
  - `maia(key TEXT PRIMARY KEY, result_json, created_utc)` con chiave come in §3.2.
  - Un risultato in cache **soddisfa** una richiesta se `multipv ≥` richiesto e `depth ≥ d_min` richiesto e non è `unstable_depth`; in tal caso si usano solo le prime righe richieste. Un nuovo risultato sostituisce quello in cache solo se ha `depth` maggiore (a parità, `multipv` maggiore).

---

## 3-bis. Scala Elo e fasce

L'utente conosce il proprio Elo in una scala (FIDE, Lichess, chess.com), Maia-2 è addestrato su Lichess. Quattro numeri distinti:

| Nome | Significato | Usato per |
| --- | --- | --- |
| `elo_declared` | Elo dichiarato, nella scala `elo_scale` | Testata, token `{{elo:user}}` |
| `elo_ref_fide` | `elo_declared` riportato in scala FIDE (D-38) | Fascia di calibrazione (§7), ancora (§9.2), soglie in Elo (E3 obbligatoria da 2150, S11 da 2000) |
| `elo_maia` | `elo_declared` convertito in scala Lichess, arrotondato all'intero | Chiamate a Maia-2 |
| `elo_up` | `min(elo_maia + up_delta, elo_max_model)` | `p_up` (§3.2) |

Gli stessi quattro valori esistono per l'avversario (`opp_*`). `elo_ref_fide` dell'avversario non è usato.

**Conversione** (`config/elo_conversion.yaml`, Appendice D): interpolazione lineare a tratti sui punti `[x_fide, y_lichess]`. Fuori dall'intervallo dei punti si estrapola con offset costante: sotto il primo punto `y = x + (y0 − x0)`, sopra l'ultimo `y = x + (yn − xn)`. La conversione inversa (Lichess → FIDE) usa gli stessi punti con gli assi scambiati (la tabella è strettamente crescente). Arrotondamento all'intero più vicino, metà lontano da zero. `lichess` → `elo_maia = elo_declared`, `elo_ref_fide = inversa(elo_declared)`.

**Valori di riferimento del segnaposto (AC-30):** 1500 FIDE → 1700; 1900 FIDE → 2025; 2400 FIDE → 2400; 900 FIDE → 1200 (estrapolazione); inversa 2025 Lichess → 1900 FIDE. `doctor` stampa questa tabella con `bucket`, `top_bucket_lower` e `saturated` di ciascuna ancora.

**Fasce di calibrazione** (`band`, intervalli chiusi a sinistra e aperti a destra su `elo_ref_fide`): `lt1200` (< 1200), `1200_1600`, `1600_2000`, `2000_2400`, `ge2400` (≥ 2400). Nel testo per l'utente si scrivono «< 1200», «1200–1600», ecc.

**Ancora** (§9.2) su `elo_ref_fide`: < 1750 → `1500`; 1750–2149 → `1900`; ≥ 2150 → `2400`.

**Divisione dei ruoli:** la **fascia** decide i parametri numerici (parole totali, `K`, `plies`, `L_max`, `A`, `B`, soglie di classificazione); l'**ancora** decide forma e struttura (titoli, fusioni ed esclusioni, colonne delle tabelle, pesi del budget, quota `theory`, esempio few-shot). Esempio: 1700 FIDE ha fascia `1600_2000` (tecnica, 1400 parole) e ancora `1500` (struttura semplificata).

L'output riporta in testata entrambe le cifre («Elo dichiarato 1900 FIDE → 2025 in scala Lichess usata da Maia-2»). Se O-1 fornisce una fonte si aggiorna solo `elo_conversion.yaml`.

---

## 3-ter. Piano di esplorazione

Gli esempi di riferimento sono stati ottenuti con circa 40 s sulla radice, 15 s sulla mossa nulla, 25 s per ogni risposta e 22 s per ogni test di move order (profondità 17–22). I profili sono definiti da tempo **e** profondità minima (D-20).

### 3-ter.1 Profili (`config/exploration.yaml`)

| Parametro | `fast` | `standard` | `deep` |
| --- | --- | --- | --- |
| Tempo totale indicativo `B` | 60 s | 300 s | 900 s |
| Profondità minima E0, E1, E4 (`dmin.root`) | 16 | 18 | 20 |
| Profondità minima E2, E3, risposte in modalità avversario (`dmin.nodes`) | 14 | 16 | 18 |
| Profondità minima E2b, E2c (`dmin.pvwalk`) | 12 | 14 | 14 |
| Tetto per nodo `t_cap` (fattore su `t_target`) | ×2 | ×2 | ×1,5 |
| Scadenza globale (fattore su `B`) | ×2 | ×2 | ×1,5 |
| `MultiPV` radice (E0) | 8 | 12 | 16 |
| `MultiPV` risposte (E1, E2, E3, risposte) | 5 | 8 | 8 |
| `MultiPV` E2b | 2 | 2 | 2 |
| Livelli di E3 | ℓ1 | ℓ1–ℓ2 | ℓ1–ℓ3 |
| E3: candidate `M` / risposte `R` | 1 / 2 | 2 / 3 | 3 / 3 |
| `e4_max_moves` | 4 | 6 | 6 |
| Nodi massimi (tutte le fasi, nodi effettivamente analizzati) | 16 | 40 | 80 |

In M1 tutti i profili sono limitati a ℓ1 (D-23). Gli esempi `rendered` si generano con `deep`.

### 3-ter.2 Fasi, ordine e tempo

| Fase | Contenuto | Quota di `B` | `MultiPV` |
| --- | --- | --- | --- |
| E0 Radice | Analisi della posizione | 30% | radice |
| E4 Seed Maia | Una ricerca alla radice ristretta (`root_moves`) alle mosse con `p ≥ e4_min_p` (3%) di chi muove, assenti da E0, al massimo `e4_max_moves` (le più probabili) | 10% | = numero di mosse |
| E1 Mossa nulla | Se il lato al tratto non è sotto scacco: `board.push(chess.Move.null())` e analisi; mostra che cosa farebbe l'altro lato se avesse il tratto. Altrimenti omessa (`omitted_phases: E1, in_check`) | 8% | risposte |
| E2 Risposte | Per ogni candidata `explained` (ordine di §3-ter.3): nodo dopo la candidata | 26% | risposte |
| E3 Move order | Livelli ℓ1…ℓk (sotto) | 20% | risposte |
| E2b Cammino sulla PV (D-29, D-58) | Nodi «tocca all'utente» lungo la PV (di E0, o di E4 per le mosse che vengono da E4) delle candidate interessate | 6% | 2 |
| E2c Completamento del contesto | Ricerche con `root_moves` = {mossa di contesto} nei nodi di T3 dove manca (§3-ter.6) | dalla quota di E3 | 1 |
| R Risposte (solo avversario al tratto, §2-bis.6) | Nodi dopo ciascuna risposta `R<n>`; sostituisce E2, E2b ed E3. In questa modalità E2c non si esegue e T3 non esiste | 52% (= 26 + 6 + 20) | risposte |

**Ordine di esecuzione (D-43):** Maia-2 alla radice → E0 → E4 → selezione delle candidate (§3-ter.3) → E1 → E2 (+ Maia-2 sui nodi) → E3-ℓ1 (+ Maia-2) → E2b → E2c → E3-ℓ2 → E3-ℓ3. E3-ℓ1 precede E2b perché un nodo di ℓ1 analizzato con `MultiPV` ≥ 2 soddisfa anche E2b (cache).

**Tempo per nodo.** `t_target(nodo) = quota_fase × B / nodi_pianificati_nella_fase`; `t_cap = fattore × t_target`. Per E2c: `t_target` = metà del `t_target` di E3. E0, E1 ed E4 hanno un solo nodo.

**Pianificazione e tetto di nodi.** Prima di ogni fase si calcola la lista dei nodi da analizzare togliendo quelli già soddisfatti dalla cache (che non contano nel tetto). Se `nodi_già_analizzati + nodi_pianificati` supera il tetto, si scartano nodi nell'**ordine di scarto unico**: E3-ℓ3, poi E3-ℓ2, poi E2c, poi E2b (dalla candidata con rango peggiore), poi E3-ℓ1 (dalla coppia candidata/risposta con rango peggiore). E0, E4, E1 ed E2 non si scartano mai. Per pianificare E3-ℓ1 prima di E2 si riservano `M × (R + 1)` nodi.

**Scadenza globale.** Se il tempo trascorso dall'inizio di E0 supera `fattore × B`, i nodi rimanenti si scartano nello stesso ordine; quelli non scartabili (E0–E2) proseguono con `t_target = 0` (si fermano appena raggiunta la profondità minima, o al tetto). Ogni scarto è registrato in `omitted_nodes: [{phase, reason: "node_cap" | "deadline", ref}]` e citato nel rapporto finale.

**Livelli di E3 (D-28).** Per ciascuna delle prime `M` candidate `explained` (per valutazione) e per ogni sua risposta `r` dell'insieme `Rset(c)`:

| Livello | Nodo analizzato | Tocca a | Maia-2 | Esempio (Najdorf) |
| --- | --- | --- | --- | --- |
| ℓ1 | dopo `c, r` | utente | Elo utente | `6.Be3 Ng4` → `7.Bg5` / `7.Bc1` |
| ℓ2 | dopo `c, r, u` (`u` = prima mossa di ℓ1) | avversario | Elo avversario | `6.Be3 e5 7.Nb3` → costo di `...Nc6` |
| ℓ3 | dopo `c, r, u, r′` (`r′` = prima mossa di ℓ2) | utente | Elo utente | `6.Be3 e5 7.Nb3 Be6` → `8.h3` / `8.Qd2` / `8.f3` |

`Rset(c)` = le prime `R` mosse per valutazione nel nodo di E2 di `c` (dal punto di vista dell'avversario), più la mossa più probabile per Maia-2 (Elo avversario) in quel nodo se non già inclusa (massimo `R + 1`).

**E2b (D-29, D-58).** Insieme delle candidate: `explained` con `loss_cp ≤ max(L_max, practical_alt.max_loss)`. Per ciascuna, sia `pv` la PV della riga della candidata in E0 o E4 (inizia con la candidata); i nodi sono le posizioni dopo `2, 4, …` semimosse, fino a `plies_max − 1` e comunque non oltre la lunghezza della PV. Ogni nodo con `MultiPV` 2. Se alcuni nodi mancano (tetto o scadenza) la `complexity` si calcola sui nodi disponibili e la candidata porta `complexity_partial: true`.

### 3-ter.3 Selezione delle candidate (utente al tratto, D-42)

Dati: righe di E0 e di E4 alla radice, con `eval_user_cp`; `best = max eval_user_cp` tra le righe di **E0**; `loss_cp(c) = max(0, best − eval_user_cp(c))` (se una mossa di E4 risulta migliore di `best`, `loss_cp = 0` e avviso `e4_better_than_root`). Parametri della fascia: `K`, `explained_min`, `listed_max`, `L_max`.

```
S    = righe di E0 ordinate per eval_user_cp decrescente (a parità: rango MultiPV)
pre(c) = - loss_cp(c) + A(fascia) * 100 * p_user(c)          # = rec_score con complexity 0 (§4.3)
W    = [c in S if loss_cp(c) <= L_max]  ordinate per pre decrescente
       (a parità: eval_user_cp decrescente, poi rango in S, poi UCI alfabetico)
mt   = argmax p_user sulle mosse legali (a parità: rango in S, poi UCI alfabetico)
E    = W[:K]
if mt non in E:
    if mt ha una valutazione (E0 o E4): E = W[:K-1] + [mt]
    else: avviso maia_top_unevaluated (mt resta fuori)
for c in W, poi per c in S (in ordine) while len(E) < explained_min:
    if c not in E: E.append(c)
explained = E ordinate per eval_user_cp decrescente (a parità: rango in S)
listed    = S[:listed_max]
```

- **Perché `pre`, non la sola valutazione (D-63):** alle fasce basse `A` è alto, quindi le mosse naturali per un giocatore di quel livello (alta `p_user`, perdita contenuta) entrano tra le candidate spiegate invece di restare fuori perché «ottava per valutazione»; alle fasce alte `A` vale 0 e `pre` coincide con la valutazione. Senza questa regola la mossa consigliata, scelta solo tra le `explained`, non potrebbe mai essere una mossa sensata ma non tra le prime `K` del motore.
- Con dettaglio 4 `K` è quello della fascia (§7.1); da M4 il dettaglio lo modifica (§7.2).
- Ogni mossa alla radice con una valutazione (E0 ∪ E4) riceve un ID `C<n>`; gli ID si assegnano per `eval_user_cp` decrescente (a parità: rango MultiPV, poi le mosse di E4 per `p_user` decrescente). `PV<n>` è la PV di `C<n>`.
- La mossa consigliata (§4.3) si sceglie **tra** le `explained`: nessuna circolarità (D-29).
- **`quiet` (D-32):** `S_q = max(K, 3)` limitato al numero di righe di E0; `spread_cp = eval(S[0]) − eval(S[S_q − 1])`; `quiet = spread_cp ≤ quiet_spread_cp` (25). Esempio Najdorf a 1900 (`K` = 5): +37, +37, +35, +29, +25 → `spread` 12 → `quiet`. In modalità avversario si calcola sulle righe di E0 dal punto di vista di chi muove.
- **Trasposizioni:** per ogni coppia di candidate `explained` si confrontano gli EPD lungo le rispettive PV (fino a `plies_max` semimosse); la prima EPD comune genera `transpositions: [{a, b, ply_a, ply_b}]` (esempio: `6.f3 e5 7.Nb3 Be7 8.Be3 Be6 9.Qd2` e `6.Be3 e5 7.Nb3 Be7 8.f3 Be6 9.Qd2`). È un dato per il testo, non cambia la selezione.

### 3-ter.4 Albero

Ogni analisi è un **nodo** (schema in §6.2). Il pacchetto include solo i nodi citabili: radice, mossa nulla, E2, E3, nodi delle risposte; i nodi E2b ed E2c restano in `pack.json` (servono a `rerun` e ai test) ma sono marcati `citable: false` e non sono inviati al modello.

### 3-ter.5 Stima dei tempi

Tempo medio atteso ≈ `B` del profilo (una prospettiva). La chiamata al modello aggiunge 20–60 s. `doctor` esegue un benchmark (E0 sulla posizione d'esempio a profondità 16) e stampa la stima per profilo: `stima = B × (tempo_misurato / tempo_di_riferimento)` con `tempo_di_riferimento` in `config/exploration.yaml` (scritto da M0).

### 3-ter.6 Mossa di contesto dell'avversario (T3, D-44)

Serve a riprodurre in modo deterministico il ragionamento «`...Nc6` costa poco contro un sistema e molto contro un altro».

1. **Nodi di T3:** i nodi di E2 (dopo ogni candidata `explained`) e, da M2, i nodi di ℓ2; in tutti tocca all'avversario.
2. **Candidate di contesto:** mosse (confrontate per UCI) presenti nel `MultiPV` di almeno 2 nodi di T3, esclusa la mossa che è la migliore in **tutti** i nodi in cui compare.
3. Si ordinano per (numero di nodi in cui compaiono, `p_opp` medio) decrescenti e si tengono le prime 3. Per ciascuna, nei nodi di T3 dove è legale ma manca dal `MultiPV`, si esegue E2c (se il tetto lo consente).
4. `cost(m, n) = eval_best_opp(n) − eval_opp(m, n)` in cp (dal punto di vista dell'avversario, ≥ 0); `spread(m) = max cost − min cost` sui nodi con valutazione (almeno 2).
5. Mossa di contesto = quella con `spread` massimo se `spread ≥ context_spread_cp` (30); a parità, `p_opp` medio maggiore, poi UCI alfabetico. Se nessuna supera la soglia, `context_move = null` e T3 non c'è.

Sui nodi del raw 1900 (uno di E2 e tre di ℓ2, quindi da M2) l'algoritmo sceglie `...Nc6` (costi ≈ 8, 53, 10, 3 cp → `spread` 50).

---

## 4. Il valore differenziante: lo scarto umano/oggettivo

### 4.1 Tre numeri per ogni mossa alla radice

Per ogni mossa con ID `C<n>` (utente al tratto):

- `eval_user_cp` / WDL (Stockfish) e `loss_cp` rispetto alla migliore di E0 (§3-ter.3), entrambi dal punto di vista dell'utente;
- `p_user` = probabilità che Maia-2 all'Elo dell'utente giochi la mossa;
- `p_up` = probabilità a `elo_up` (o `null`, §3.2).

### 4.2 Classificazione automatica (soglie in `config/thresholds.yaml: classification`)

Si classificano **tutte** le mosse con ID `C<n>`. Le condizioni si valutano nell'ordine della tabella; vince la prima vera (D-25, D-36); se nessuna è vera `category = null`.

| Ordine | Categoria | Condizione di partenza | Uso nell'analisi |
| --- | --- | --- | --- |
| 1 | `natural_trap` (trappola naturale) | `p_user ≥ 20%` e `loss_cp ≥ 80` (fasce `lt1200` e `1200_1600`: `loss_cp ≥ 60`) | «La mossa che ti viene d'istinto è un errore perché…» |
| 2 | `hard_move` (mossa difficile) | `p_user < 5%` e `loss_cp ≤ 10` | «La mossa migliore è difficile da vedere perché…» |
| 3 | `solid` (mossa solida) | `p_user ≥ 15%` e `loss_cp ≤ 25` | Indicata come scelta pratica |
| 4 | `practical_alt` (alternativa pratica) | `25 < loss_cp ≤ 60` e `complexity ≤ 1` (`complexity` non `null`) | Rilevante a livelli bassi/medi |
| 5 | `improbable_error` (errore improbabile) | `p_user < 5%` e `loss_cp ≥ 80` e `p_up ≥ 8%` | Solo se istruttiva; con `p_up = null` non si assegna (D-25) |

Le percentuali si confrontano sul valore non arrotondato. Le etichette italiane sono in `config/wording.yaml: categories`.

### 4.3 La mossa consigliata (D-12, D-29)

Calcolata dal codice, mai dal LLM:

```
complexity(c) = numero di nodi E2b di c in cui la mossa dell'utente e' obbligata:
                eval(1a riga) - eval(2a riga) >= forced_gap_cp (100), dal punto di vista
                di chi muove, con i matti convertiti come in §3.1.2; oppure il nodo ha una
                sola mossa legale. null se c non e' nell'insieme di E2b.
rec_score(c)  = - loss_cp(c) + A(fascia) * 100 * p_user(c) - B(fascia) * 50 * complexity(c)
candidabili   = explained con loss_cp <= L_max(fascia)
raccomandata  = argmax rec_score tra le candidabili
```

**Parità e casi limite.** Due candidate con `rec_score` a meno di `rec_tie_points` (5) l'una dall'altra sono in parità; tra le candidate in parità con la migliore vince la `complexity` minore, poi la `loss_cp` minore, poi l'ordine di E0. Se le candidabili sono vuote (caso raro: `mt` aggiunta oltre `L_max` e nessuna altra), la raccomandata è `C1`. `rec_score` è `null` per le candidate non candidabili.

**Forza della raccomandazione.** `strength = "weak"` se `quiet` è vero (allora anche `no_unique_best: true` e il testo deve proporre **sistemi**, non una mossa unica); altrimenti `strength = "normal"`.

| Fascia | A | B | Nota |
| --- | --- | --- | --- |
| `lt1200` | 0,6 | 1,2 | Conta di più giocare semplice e naturale |
| `1200_1600` | 0,5 | 1,0 | |
| `1600_2000` | 0,3 | 0,5 | |
| `2000_2400` | 0,1 | 0,2 | |
| `ge2400` | 0,0 | 0,0 | Vale solo l'eval |

**Esempio numerico astratto** (usato da AC-24, non tratto dal pacchetto d'esempio; fascia `1600_2000`: `A` = 0,3, `B` = 0,5). `X`: `loss_cp` 0, `p_user` 18%, `complexity` 0 → `rec_score` = 0 + 0,3·100·0,18 − 0 = **5,4**. `Y`: `loss_cp` 15, `p_user` 12%, `complexity` 0 → −15 + 3,6 = **−11,4**. Vince `X`. Con `complexity` 1, `X` scende a 5,4 − 25 = **−19,6** e vince `Y`. I giudizi su quale mossa preferire nei file raw **non sono vincolanti**: negli esempi `rendered` la raccomandazione è quella calcolata.

---

## 5. Feature e profilo della posizione

### 5.1 Estrazione delle feature (deterministica, pre-LLM, D-55)

Tutto con `python-chess` e regole proprie, mai delegato al modello. Ogni feature è un fatto con testimone:

```json
{"key": "backward_pawn", "side": "b", "squares": ["d6"], "value": null}
```

`side` è il lato a cui la feature **appartiene** (per le debolezze: il lato che le subisce; per le tattiche: vedi definizione), `null` per le feature globali. `squares` sono in minuscolo, ordinate alfabeticamente. Le feature si calcolano sulla **radice**; da M3 anche sulle foglie delle linee (§5-bis). Le chiavi sono il vocabolario delle asserzioni (§9-bis.5).

**Convenzioni:** valori P = 1, N = B = 3, R = 5, Q = 9, K = 0. Traversa relativa `rr(S, q)` = traversa di `q` vista dal lato `S` (1 = propria prima traversa). File adiacenti = colonne a distanza 1. «Pezzo minore» = cavallo o alfiere.

| Chiave | Definizione operativa | `side` / testimone | Da |
| --- | --- | --- | --- |
| `material_balance` | Somma dei valori del Bianco − somma del Nero | `null`; `value` = differenza, `squares` vuoto | M1 |
| `bishop_pair` | `S` ha alfieri su entrambi i colori di casa e `O` no | `S`; case degli alfieri | M1 |
| `opposite_bishops` | Ciascun lato ha esattamente un alfiere e i due sono su colori diversi | `null`; case degli alfieri | M1 |
| `exchange_up` | torri(`S`) − torri(`O`) = 1 e minori(`O`) − minori(`S`) = 1 | `S` | M1 |
| `isolated_pawn` | Pedone di `S` senza pedoni di `S` sulle colonne adiacenti | `S`; casa del pedone (una feature per pedone) | M1 |
| `doubled_pawn` | Colonna con ≥ 2 pedoni di `S` | `S`; tutte le case di quella colonna | M1 |
| `backward_pawn` | Pedone `p` di `S` non isolato, tutti i pedoni di `S` sulle colonne adiacenti hanno `rr` > `rr(p)`, e la casa davanti a `p` è attaccata da un pedone di `O` | `S`; casa del pedone | M1 |
| `passed_pawn` | Nessun pedone di `O` davanti a `p` sulla sua colonna o sulle adiacenti | `S`; casa; `value` = `{"protected": bool, "connected": bool}` (difeso da un pedone di `S`; passato di `S` su colonna adiacente) | M1 |
| `pawn_island_count` | Numero di gruppi di colonne consecutive con almeno un pedone di `S` | `S`; `value` = numero | M1 |
| `pawn_majority` | Su un'ala (colonne a–d = `queenside`, e–h = `kingside`) `S` ha più pedoni di `O` | `S`; `value` = ala | M1 |
| `weak_square` | Casa `q` su colonne c–f con `rr(S, q)` tra 3 e 5, non occupata da un pedone di `S`, tale che nessun pedone di `S` sulle colonne adiacenti ha `rr ≤ rr(S, q) − 1` (nessun pedone di `S` potrà mai attaccarla) | `S` (chi ha la debolezza); case | M1 |
| `outpost` | Casa che è `weak_square` di `O`, con `rr(S, q)` tra 4 e 6, difesa da un pedone di `S` | `S` (chi può usarla); case | M1 |
| `knight_outpost` | Cavallo di `S` su un `outpost` di `S` | `S`; casa | M1 |
| `king_castled` / `can_castle_short` / `can_castle_long` / `castling_lost` | Corrispondono ai valori di `profile.castling` (§5.2) | `S`; casa del re | M1 |
| `pawn_shield_intact` | Re di `S` arroccato e, sulle colonne del re ± 1, ogni colonna ha un pedone di `S` con `rr` 2 o 3 | `S`; case dei pedoni dello scudo | M1 |
| `pawn_shield_weakened` | Re arroccato e almeno una di quelle colonne non ha il pedone | `S`; case `rr` 2 delle colonne scoperte | M1 |
| `open_file_to_king` | Una delle colonne del re ± 1 non ha pedoni di `S` (re arroccato o no) | `S`; casa del re; `value` = lettere delle colonne | M1 |
| `king_zone_attackers` / `king_zone_defenders` | Zona = casa del re + 8 case vicine; pezzi di `O` (esclusi pedoni e re) che attaccano almeno una casa della zona / pezzi di `S` (escluso il re) che ne difendono almeno una | `S`; case dei pezzi; `value` = numero | M3 |
| `piece_mobility` | Per pezzo: mosse pseudo-legali verso case non attaccate da pedoni di `O` | `S`; `value` = dizionario casa → numero | M3 |
| `inactive_piece` | Minore o torre di `S` con mobilità ≤ 2 (definizione sopra) | `S`; casa | M3 |
| `rook_open_file` | Torre di `S` su colonna senza pedoni (`value` = `open`) o senza pedoni di `S` (`semi_open`) | `S`; casa | M1 |
| `rook_seventh` | Torre di `S` con `rr` = 7 | `S`; casa | M1 |
| `bishop_diagonal_open` | Alfiere di `S` con almeno 7 mosse pseudo-legali | `S`; casa | M3 |
| `pin` | Pezzo di `S` inchiodato al proprio re (`board.is_pinned`) | `S` (chi subisce); `[casa inchiodata, casa dell'inchiodatore]` | M1 |
| `skewer` | Pezzo a lunga gittata di `O` che attacca un pezzo di `S` di valore maggiore, dietro il quale sulla stessa linea c'è un altro pezzo di `S` non difeso | `S`; `[attaccante, primo, secondo]` | M3 |
| `fork` | Pezzo di `O` che attacca ≥ 2 pezzi di `S` (re compreso) ciascuno di valore maggiore dell'attaccante o non difeso, e l'attaccante non è catturabile con SEE ≥ 0 per `S` | `S`; `[attaccante, bersagli…]` | M3 |
| `hanging_piece` | Pezzo di `S` diverso da pedone e re, attaccato e non difeso oppure attaccato da un pezzo di valore minore (D-32) | `S`; casa | M1 |
| `overloaded_piece` | Pezzo di `S` che è l'unico difensore di ≥ 2 pezzi o case attaccati | `S`; `[difensore, difesi…]` | M3 |
| `mate_in_n` | La prima riga di E0 ha un matto | lato che dà matto; `value` = `n` (mosse) | M1 |
| `unresolved_capture` | Il lato al tratto ha una cattura legale con SEE ≥ 3 | lato al tratto; `[da, a]`; `value` = SEE | M1 |
| `check_available` | Il lato al tratto ha almeno uno scacco legale (`board.gives_check`) | lato al tratto; case di arrivo | M1 |
| `undeveloped_pieces` | Minori di `S` sulle case di partenza (b1, g1, c1, f1 / b8, g8, c8, f8) con il pezzo del tipo originario | `S`; case | M1 |
| `development_lead` | `dev(S) − dev(O) ≥ 2`, con `dev` = minori non sulle case di partenza + 1 se arroccato | `S`; `value` = differenza | M1 |
| `tempo_count` | Mosse forzanti (scacchi, catture, minacce di cattura con SEE ≥ 3) nelle prime 6 semimosse della PV migliore | `S`; `value` | M3 |
| `minority_attack` | `S` ha 2 pedoni su a–c, `O` ne ha 3, e `S` ha torre o donna sulla colonna b o c | `S` | M3 |
| `space_advantage` | Case nella metà avversaria attaccate dai pedoni di `S` − stesso per `O` ≥ 3 | `S`; `value` = differenza | M3 |
| `file_control` | Colonna aperta con torre o donna di un solo lato | quel lato; `value` = colonna | M3 |
| `central_control` | Somma, sulle case d4 e4 d5 e5, del numero di attaccanti (pezzi e pedoni) di ciascun lato | `null`; `value` = `{"w": n, "b": n}` | M1 |
| `pawn_chain` | ≥ 3 pedoni di `S` collegati in diagonale, ciascuno difeso dal precedente | `S`; case | M3 |

**SEE** (`features/see.py`): scambio simulato su una casa con mosse **legali**; a ogni passo cattura il pezzo legale di valore minimo; si costruisce la sequenza dei guadagni e la si risolve all'indietro (`gain[i] = max(-gain[i+1], gain[i])` nella formulazione classica). Il re cattura solo se la mossa è legale.

**Verifica sulla posizione d'esempio (AC-25):** alla radice Najdorf non c'è `backward_pawn` nero (il pedone e7 è dietro); dopo `6.Be3 e5 7.Nb3` ci sono `backward_pawn` b `d6`, `weak_square` b `d5`, `outpost` w `d5`.

### 5.2 Profilo della posizione

Calcolato in modo deterministico; decide quali sezioni hanno senso (§8.2). Soglie in `config/thresholds.yaml: profile`.

| Campo | Definizione |
| --- | --- |
| `phase` | `endgame` se il materiale non-pedone **totale dei due lati** ≤ 24 oppure se non ci sono donne e ciascun lato ha al massimo 2 pezzi minori (torri senza limite); altrimenti `opening` se `in_book` e `fullmove ≤ 15`; altrimenti `middlegame` (D-59) |
| `castling` | Per lato: `castled_short` (nessun diritto d'arrocco e re sulle colonne g o h della prima traversa relativa), `castled_long` (nessun diritto e re sulle colonne c o b), `can_both`, `can_short`, `can_long` (in base ai diritti), `lost` (nessuno dei precedenti) |
| `tactical` | Vero se almeno una condizione; le condizioni vere sono elencate in `tactical_reasons`: `gap` (eval 1ª − 2ª riga di E0 ≥ `tactical.gap_cp`, 150, dal punto di vista di chi muove); `mate` (matto in ≤ `tactical.mate_plies` semimosse, 8, in una delle PV delle prime `K` righe di E0); `in_check`; `hanging_piece` (qualunque lato); `unresolved_capture` |
| `quiet` / `spread_cp` | §3-ter.3 |
| `closed` | ≥ 3 coppie di pedoni bloccati frontalmente (pedone bianco su `q`, pedone nero sulla casa immediatamente davanti dal punto di vista del Bianco) |
| `tablebase` | `true` se pezzi totali (re compresi) ≤ `syzygy.max_pieces` **e** le tablebase sono disponibili (da M2; in M0–M1 sempre `false`) |
| `in_book` | EPD presente nell'indice delle aperture (§3.3) |
| `material` | `{"w": somma, "b": somma, "balance": w − b}` con i valori sopra (re escluso) |
| `matrix_column` | `matrix_column(profile)` sotto |

**Colonna della matrice (D-32).** Funzione unica, testata da AC-25:

```
def matrix_column(profile):
    if profile.tablebase:          return 4   # Finale con tablebase
    if profile.phase == "endgame": return 3   # Finale
    if profile.tactical:           return 2   # Mediogioco tattico
    return 1                                  # Apertura o mediogioco non tattico
```

Il mediogioco né quieto né tattico ricade nella colonna 1: piani e sistemi sono ancora la chiave di lettura. Una posizione di apertura tattica (per esempio con il re sotto scacco) ricade nella colonna 2.

---

## 5-bis. Category Scoring Engine (da M3)

Cuore dell'app dal punto di vista dell'analisi. Trasforma i dati grezzi dei motori in un referto che dice al LLM **quanto conta ogni aspetto a quel livello Elo**, così spazio e tono sono proporzionati. Non fa parte dell'MVP (D-11).

### 5-bis.1 Categorie

| # | Categoria | Segnali statici | Segnali dinamici (linee) |
| --- | --- | --- | --- |
| 1 | `king_safety` | scudo, colonne aperte, difensori/attaccanti in zona | scacchi, matti, perdite vicino al re |
| 2 | `pawn_structure` | isolati, doppiati, arretrati, passati, maggioranze | rotture di pedone, passati creati |
| 3 | `space_center` | pedoni avanzati, case controllate | eval che cala se si cede il controllo |
| 4 | `piece_activity` | mobilità, pezzi inattivi, coppia degli alfieri, avamposti | riposizionamenti, pezzi intrappolati |
| 5 | `initiative_tempo` | sviluppo, tempi guadagnati | numero di mosse forzanti nelle PV |
| 6 | `threats_dynamics` | pezzi appesi/sovraccarichi, inchiodature | analisi null-move (E1) |
| 7 | `material` | bilancio, compensazione | esiti di catture e scambi |
| 8 | `transition_plans` | fase, finali raggiungibili | PV lunghe, Syzygy, stabilità in profondità |
| 9 | `practical_complexity` (meta) | — | entropia della policy Maia-2, mosse uniche |

L'elenco è estendibile: ogni categoria è un modulo con le sue feature e le sue regole di tag.

### 5-bis.2 Tre grandezze per categoria e per lato

- `balance` (−100…+100): chi sta meglio in quell'aspetto.
- `T` tranquillità (0–100): 100 = nessuna preoccupazione.
- `R` rilevanza (0–100): quanto l'aspetto incide sulla decisione *qui e ora*; decide lo spazio nel testo.

`T` e `R` dicono cose diverse: re al sicuro per entrambi → T alta, R bassa; struttura equilibrata con rottura imminente → T media, R alta. Soglie: `T ≥ 85` *non preoccuparti* · 60–85 *monitora* · 30–60 *attenzione* · `< 30` *critico*. Nel testo si mostra **T dell'utente e R** (T dell'avversario solo a dettaglio 5); il pacchetto le contiene entrambe.

### 5-bis.3 Maia-2 filtra le linee di Stockfish (visibilità per Elo)

Una linea che richiede tre mosse uniche non è una minaccia reale a 1500 ma lo è a 2500. Per ogni linea `ℓ`:

- `P_att` = prodotto delle probabilità Maia-2 delle mosse dell'attaccante lungo la linea, con Maia-2 interrogata a ogni nodo con l'Elo di chi muove (e quello dell'altro come `elo_oppo`);
- `P_dif` = probabilità che il difensore trovi le mosse di salvataggio (stesso calcolo);
- `risk(ℓ) = P_att × (1 − P_dif) × impatto(ℓ)`, con impatto = perdita in cp o cambio di esito WDL;
- opportunità pratica: stessa formula per le linee a favore dell'utente.

La linea entra nel referto solo se `risk` (o opportunità) ≥ `θ(Elo)`, con `θ` decrescente all'aumentare dell'Elo. Eccezione: matti forzati e perdite decisive entrano sempre, con `visible_at_level: false` se `P_att` è bassa; alimentano «Minacce invisibili al tuo livello». Le chiamate a Maia-2 usano l'inferenza a lotti e la cache.

### 5-bis.4 Calcolo dei punteggi

1. **Tag:** confronto delle feature tra radice e foglia (dopo quiescenza); una linea può avere più tag.
2. **Tranquillità dinamica:** `T_dyn(c, s) = 100 · exp(−Σ risk(ℓ) / k_c)` sulle linee con tag `c` che danneggiano il lato `s`.
3. **Tranquillità statica:** `T_stat(c, s)` da feature normalizzate (categorie lente: struttura, spazio, attività).
4. **Combinazione:** `T = w_c · T_dyn + (1 − w_c) · T_stat`; `w_c` alto per le tattiche (re ≈ 0,8), basso per le lente (struttura ≈ 0,3).
5. **Override:** matto o perdita decisiva con `P_att` sopra soglia minima → `T ≤ 30`.
6. **Rilevanza:** `R` = combinazione pesata di `100 − min(T_bianco, T_nero)`, `|balance|`, vicinanza temporale della minaccia, peso della categoria nella fase. Normalizzata.
7. **Confidenza:** bassa se l'eval di Stockfish è instabile tra profondità o se Maia-2 è saturo (§3.2).

**Onestà sui numeri:** `k_c`, `w_c`, `θ` e i pesi di `R` sono ipotesi iniziali. Per le categorie lente Stockfish non dà una verità per categoria, quindi quei punteggi sono euristici. Vanno calibrati su partite reali (M5, D-21): una `T` alta non deve precedere errori frequenti a quel livello, e viceversa.

### 5-bis.5 Dal referto al testo

- Lo spazio nel testo è proporzionale a `R`; le sezioni per categoria sono ordinate per `R` decrescente.
- `T ≥ 85`: una o due frasi **con motivazione concreta dai dati** («nessuna delle prime 10 linee minaccia il re entro 12 semimosse»). Mai un generico «il re è al sicuro».
- `T < 30`: sezione estesa con linee, difese e contromosse.
- Il LLM non ricalcola né modifica i punteggi; se li ritiene incoerenti con le linee lo segnala nel campo `notes`.

---

## 6. Evidence Pack (contratto verso il LLM)

### 6.1 Principi

- Salvato sempre come `pack.json` (D-19), UTF-8, chiavi in inglese, prima della chiamata al modello. `rerun` non lo modifica mai.
- Modelli `pydantic` v2 in `pack/schema.py`; `pack.json` = `model_dump_json(indent=2)`; i campi opzionali assenti valgono `null`, le liste vuote `[]`.
- Ogni mossa nel pacchetto è in **SAN** (con UCI accanto dove serve) ed è verificabile contro il FEN del nodo.
- Unità: centipawn interi; probabilità in [0, 1] con 4 decimali; WDL in per mille interi. Punto di vista: §3.1.2 (D-39).
- Al modello si invia una **vista ridotta** (`pack/llm_view.py`): sono esclusi `tables`, i nodi con `citable: false`, `omitted_nodes`, `config_hash`; nei nodi si inviano solo le prime 5 righe di `multipv` con PV troncata a 6 semimosse, e le prime 5 mosse di Maia-2.

### 6.2 Schema

```
Pack
  schema_version: "0.9"
  app_version: str
  created_utc: str (ISO 8601)
  config_hash: str                   # sha1 delle sezioni di config che influenzano l'esplorazione
  position:
    fen: str                         # normalizzato (§2-bis.3)
    epd: str
    side_to_move: "w" | "b"
    fullmove: int
    legal_moves: int
    in_check: bool
    last_move_san: str | null
    user_to_move: bool               # side_to_move == user.color
  history:
    source: "example" | "fen" | "pgn"
    plies: int                       # semimosse giocate dalla posizione iniziale della partita
    repetitions: int                 # quante volte la posizione corrente e' gia' comparsa
    start_fen: str | null
  user:
    color: "w" | "b"
    elo_declared: int, elo_scale: "fide" | "lichess", elo_ref_fide: int, elo_maia: int
    opp_elo_declared: int, opp_elo_maia: int
    band: "lt1200" | "1200_1600" | "1600_2000" | "2000_2400" | "ge2400"
    anchor: "1500" | "1900" | "2400"
    detail_level: int, language: "it", budget_profile: "fast" | "standard" | "deep"
  profile:
    phase, castling: {w, b}, tactical: bool, tactical_reasons: [str], quiet: bool, spread_cp: int,
    closed: bool, tablebase: bool, in_book: bool, material: {w, b, balance}, matrix_column: 1..4
  opening: {eco: str, name: str, matched_by: "epd" | "sequence"} | null
  engine:
    stockfish: {version, threads, hash_mb, profile}
    root: {node: "N1", depth: int, eval_user_cp: int, mate_user: int | null, wdl_user: [w, d, l] | null}
    candidates: [Candidate]          # vuota se tocca all'avversario
    replies: [Reply]                 # vuota se tocca all'utente
    pvs: [PV]
    null_move: {node: str} | null
    e3: [E3Entry]
    context_move: ContextMove | null
    transpositions: [{a: CID, b: CID, ply_a: int, ply_b: int}]
  maia:
    model_type, package_version, device
    bucket_user: int, bucket_opp: int, top_bucket_lower: int
    saturated: bool, confidence: "normal" | "low"
    p_up_elo: int | null, p_up_bucket: "higher" | "top" | null
    human_expected_score_user: float     # alla radice, dal punto di vista dell'utente
    entropy_bits: float
  recommendation: {id: CID, strength: "normal" | "weak", no_unique_best: bool} | null
  features: [Feature]                # §5.1
  categories: []                     # da M3 (§5-bis)
  filtered_lines: []                 # da M3
  tablebase: null                    # da M2: {wdl, dtz, result_text_key}
  tables: {T1: Table, T2?: Table, T3?: Table, T4?: Table}     # §8.5, costruite dal codice
  nodes: [Node]
  section_plan: [SectionPlanEntry]   # §8.4
  omitted_sections: [{id, reason}]
  omitted_phases: [{phase, reason}]
  omitted_nodes: [{phase, reason, ref}]
  warnings: [str]                    # codici: e4_better_than_root, maia_top_unevaluated, ...
  constraints: {max_pv_plies: int, plan_max_moves: int}

Table                                 # costruita dal codice (§8.5); il LLM non la scrive
  id: "T1".."T4", section: "S02" | "S06" | "S07"
  columns: [{key: str, header: str, kind: "data" | "text"}]
  rows: [{id: str, cells: {key: str | null}}]     # celle data = testo gia' formattato (§9-bis.7); celle text = null (le riempie il LLM)
  footnote: str | null                  # es. maia_low_confidence_table

Candidate
  id: "C<n>", san, uci, node: NID | null      # nodo di E2 se explained, altrimenti null
  source: "e0" | "e4", e0_rank: int | null
  eval_user_cp: int, mate_user: int | null, loss_cp: int, wdl_user: [w, d, l] | null
  pv: "PV<n>"
  p_user: float, p_up: float | null
  category: str | null
  complexity: int | null, complexity_partial: bool
  explained: bool, listed: bool, rec_score: float | null   # 2 decimali

Reply                                 # solo se tocca all'avversario (D-31)
  id: "R<n>", san, uci, node: NID, eval_user_cp, mate_user, p_opp: float
  user_best: [{id: "R<n>.u<k>", san, uci, eval_user_cp, mate_user, loss_cp, p_user}]   # k = 1..3

PV
  id: "PV<n>", start_node: NID, plies: [SAN], eval_end_user_cp: int   # plies[0] si gioca in start_node

E3Entry
  level: 1 | 2 | 3, candidate: CID, path: [SAN], node: NID          # path dalla radice

ContextMove
  san_by_node: {NID: SAN}, uci: str
  rows: [{node: NID, path: [SAN], best_san, best_eval_user_cp, move_eval_user_cp, cost_cp, p_opp}]
  spread_cp: int

Node
  id: "N<n>", fen, epd, parent: NID | null, via_san: str | null, via_uci: str | null
  phase: "E0" | "E1" | "E2" | "E2b" | "E2c" | "E3l1" | "E3l2" | "E3l3" | "R"
  path: [SAN]                         # mosse dalla radice (mossa nulla = "--")
  side_to_move, citable: bool
  depth, seldepth, nodes, time_s, unstable_depth: bool, root_moves: [UCI] | null
  multipv: [{rank, san, uci, eval_white_cp, mate_white, eval_user_cp, mate_user, wdl_user, pv: [SAN]}]
  maia: {elo_self, elo_oppo, policy: [{san, uci, p}], expected_score_user: float} | null
                                      # policy: mosse con p >= 0.001, ordinate per p decrescente
```

### 6.3 Assegnazione canonica degli ID

Gli ID non dipendono dall'ordine di esecuzione né dalla cache: si assegnano alla fine dell'esplorazione, in `pack/builder.py`.

- `N1` = radice; `N2` = mossa nulla (se eseguita); poi i nodi di E2 nell'ordine delle candidate; poi E3 per livello, candidata e risposta (`Rset` nell'ordine di §3-ter.2); poi i nodi delle risposte (modalità avversario) nell'ordine di `R`; poi E2b (candidata, semimossa); infine E2c. Numerazione senza buchi.
- `C<n>` e `PV<n>` secondo §3-ter.3; `R<n>` secondo §2-bis.6; `T<n>` fissi (T1 candidate o risposte, T2 move order, T3 contesto, T4 radar).

### 6.4 Linguaggio comune: bande verbali (`config/wording.yaml`)

Il LLM sceglie le parole; le asserzioni tipizzate (§9-bis.5) dichiarano la banda e il codice verifica che corrisponda al numero. Le bande di valutazione si applicano al **modulo** `|e|` (limite inferiore incluso, superiore escluso) e il segno sceglie `_plus` o `_minus`: quindi `+0,15` → `slight_plus`, `−0,15` → `slight_minus`, `−0,50` → `small_minus`. Le bande di probabilità hanno limite inferiore incluso e superiore escluso. I valori di eval sono in pedoni dal punto di vista dell'utente; il confronto si fa sui centipawn interi (`|cp| < 15` → `equal`).

| Grandezza | Bande (ID) |
| --- | --- |
| Eval | `equal` modulo < 0,15 · `slight_plus` / `slight_minus` 0,15–0,5 · `small_plus` / `small_minus` 0,5–1,0 · `clear_plus` / `clear_minus` 1,0–2,0 · `decisive_plus` / `decisive_minus` ≥ 2,0 · `mate_plus` / `mate_minus` se `mate_user` non è `null` |
| Probabilità Maia-2 | `very_unlikely` < 3% · `unlikely` 3–10% · `possible` 10–25% · `frequent` 25–45% · `very_frequent` ≥ 45% |
| Tranquillità `T` (M3) | come §5-bis.2 |

### 6.5 Esempio abbreviato (coerente con le regole)

Najdorf, utente Bianco, 1900 FIDE, profilo `standard`. I numeri di Stockfish sono quelli del raw 1900; le probabilità di Maia-2 sono **illustrative**.

```json
{
  "schema_version": "0.9",
  "position": {"fen": "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6",
               "side_to_move": "w", "fullmove": 6, "legal_moves": 43, "in_check": false,
               "last_move_san": null, "user_to_move": true},
  "user": {"color": "w", "elo_declared": 1900, "elo_scale": "fide", "elo_ref_fide": 1900,
           "elo_maia": 2025, "opp_elo_declared": 1900, "opp_elo_maia": 2025,
           "band": "1600_2000", "anchor": "1900", "detail_level": 4, "budget_profile": "standard"},
  "profile": {"phase": "opening", "castling": {"w": "can_both", "b": "can_both"},
              "tactical": false, "tactical_reasons": [], "quiet": true, "spread_cp": 12,
              "closed": false, "tablebase": false, "in_book": true, "matrix_column": 1},
  "opening": {"eco": "B90", "name": "Sicilian Defense: Najdorf Variation", "matched_by": "epd"},
  "engine": {
    "root": {"node": "N1", "depth": 20, "eval_user_cp": 37, "mate_user": null, "wdl_user": [72, 920, 8]},
    "candidates": [
      {"id": "C1", "san": "Be3", "uci": "c1e3", "node": "N3", "source": "e0", "e0_rank": 1,
       "eval_user_cp": 37, "loss_cp": 0, "pv": "PV1", "p_user": 0.18, "p_up": null,
       "category": "solid", "complexity": 0, "complexity_partial": false,
       "explained": true, "listed": true, "rec_score": 5.4},
      {"id": "C10", "san": "Be2", "uci": "f1e2", "node": null, "source": "e0", "e0_rank": 10,
       "eval_user_cp": 22, "loss_cp": 15, "pv": "PV10", "p_user": 0.12, "p_up": null,
       "category": null, "complexity": null, "complexity_partial": false,
       "explained": false, "listed": true, "rec_score": null}
    ],
    "pvs": [{"id": "PV1", "start_node": "N1", "plies": ["Be3", "e5", "Nb3", "Be7", "f3", "Be6", "Qd2"], "eval_end_user_cp": 41}],
    "null_move": {"node": "N2"},
    "replies": []
  },
  "maia": {"model_type": "rapid", "bucket_user": 10, "top_bucket_lower": 2000,
           "saturated": true, "confidence": "low", "p_up_elo": null, "p_up_bucket": null,
           "human_expected_score_user": 0.53, "entropy_bits": 3.1},
  "recommendation": {"id": "C1", "strength": "weak", "no_unique_best": true}
}
```

Coerenza: 1900 FIDE → 2025 Lichess → fascia più alta se il limite è 2000 (`saturated`, `p_up: null`); `C1` è `solid` (`p_user` ≥ 15%, `loss_cp` ≤ 25). La selezione di §3-ter.3 con `A` = 0,3 e le probabilità illustrative `Be3` 18%, `f3` 10%, `Bg5` 9%, `Nb3` 6%, `h3` 5%, `Bd3` 3%, `Be2` 12% dà `pre`: `Be3` +5,4; `f3` +3,0; `h3` −0,5; `Bg5` −5,3; `Nb3` −10,2; `Bd3` −11,1; `Be2` −11,4: le `explained` sono quindi `Be3`, `f3`, `h3`, `Bg5`, `Nb3`, e `Be2` (decima per valutazione, `C10`) resta solo `listed` e senza `rec_score`. `rec_score` di `C1` = 0 + 0,3·100·0,18 = 5,4. `quiet` perché `spread` = 37 − 25 = 12 ≤ 25. Il WDL d'esempio è illustrativo (il raw riporta «circa 92% di patta»). Le probabilità di Maia-2 sono inventate per l'esempio e non vanno copiate nei test.

---

## 7. Calibrazione per livello

Il parametro principale è la **fascia** calcolata su `elo_ref_fide` (§3-bis); il **dettaglio 1–5** è un asse indipendente (§7.2). Gli esempi di riferimento sono *ancore* a 1500, 1900 e 2400.

### 7.1 Parametri per fascia (`config/thresholds.yaml: band_params`)

| Fascia | Cosa spiegare | `plies_max` | Candidate spiegate (`explained_min`–`K`) | `listed_max` | `L_max` (cp) | Parole di prosa (dettaglio 4) | Linguaggio |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `lt1200` | Principi, minacce immediate, pezzi appesi | 3 | 1–2 | 3 | 40 | 450 | Semplice, esempi |
| `1200_1600` | Piani base, tattiche ricorrenti, strutture | 4 | 2–3 | 4 | 40 | 650 | Termini standard |
| `1600_2000` | Strutture pedonali, piani a lungo termine, perché i piani funzionano | 8 | 3–5 | 12 | 35 | 1400 | Tecnico |
| `2000_2400` | Sottigliezze posizionali, tempi, transizioni, prevenzione | 10 | 3–4 | 12 | 30 | 1100 | Preciso |
| `ge2400` | Concretezza, mosse d'attesa, zugzwang, compromessi dinamici, alternative sottili, motivi per rifiutare linee forzate | 12 | 4–5 | 12 | 25 | 800 | Sintetico, senza spiegare l'ovvio |

- `listed_max` è limitato dal `MultiPV` radice del profilo (con `fast` al massimo 8).
- Le «parole di prosa» sono **tutte le parole scritte dal LLM** (paragrafi, liste, celle di testo di `table` e `text_table`, didascalie), contate come in §9-bis.8, e non quelle prodotte dal render (D-33). Sono ipotesi: M1b le misura sui fewshot e aggiorna la colonna (§0.5).
- Il test di move order (E3) è obbligatorio con `elo_ref_fide` ≥ 2150 e attivo sotto con dettaglio ≥ 4 (in M1–M3 il dettaglio è sempre 4, quindi E3 è sempre attiva).

### 7.2 Significato del dettaglio (1–5, da M4)

| Dettaglio | Parole (× base) | `K` effettivo | `plies_max` | Sezioni opzionali incluse | Tabelle |
| --- | --- | --- | --- | --- | --- |
| 1 | ×0,35 | `explained_min` | −2 (minimo 2) | solo le obbligatorie della matrice | solo T1 |
| 2 | ×0,6 | `explained_min` | −1 | obbligatorie | T1 |
| 3 | ×0,8 | `explained_min` + 1 (massimo `K`) | 0 | obbligatorie + S08 | T1, T3 |
| **4 (default)** | ×1,0 | `K` | 0 | tutte le applicabili | tutte quelle dell'ancora (§8.5) |
| 5 | ×1,4 | `K` | +2 (massimo 12) | tutte + S11 + T avversario (M3) | tutte, T2 anche all'ancora 1900 |

**Disponibilità (D-30).** In M1–M3 è disponibile solo il dettaglio 4.

### 7.3 Regole trasversali

- A **basso livello** non mostrare linee oltre la capacità di verifica dell'utente; preferire l'**idea** al calcolo.
- Ad **alto livello** non spiegare ciò che un giocatore di quel livello sa; sintetizzare e andare al punto critico.
- L'Elo guida anche che cosa è «istruttivo»: gli errori che Maia-2 a quel livello commette spesso hanno priorità.
- La lunghezza massima di ogni linea mostrata è imposta dal token e controllata da V05, non lasciata al modello.

---

## 8. Struttura dell'analisi in output

### 8.1 Elenco delle sezioni

| ID | Contenuto | Fonte principale | `theory` ammessa |
| --- | --- | --- | --- |
| S01 | Chi sta meglio, esito in parole, in una frase + 2–3 frasi | engine | no |
| S02 | Radar delle categorie: tabella `T`/`R` ordinata per rilevanza (da M3) | categorie | no |
| S03 | Raggruppamento delle candidate in sistemi/piani con idea e per chi sono | engine + theory | sì |
| S04 | Lato di arrocco per sistema, corse di pedoni, diagonali critiche | feature + theory | sì |
| S05 | Obiettivo tipico e attenzioni per pezzo | theory + feature | sì |
| S06 | Idee principali dell'avversario (mossa nulla, policy di Maia-2, risposte per sistema, T3) | engine + maia | sì |
| S07 | Mosse candidate (T1, T2) oppure, se tocca all'avversario, risposte probabili e come prepararsi | engine + maia | no |
| S08 | Trappole naturali e mosse difficili (all'ancora 1500: errori tipici) | maia + engine | solo ancora 1500 (D-48) |
| S09 | Minacce invisibili al tuo livello (da M3) | filtered_lines | no |
| S10 | Processo di pensiero consigliato | theory + engine | sì |
| S11 | Alternative sottili, preferenze tra linee equivalenti, rilievi teorici | engine + theory | sì |
| S12 | Finale: esito esatto, piano, errori tipici (da M2) | tablebase + feature | sì |
| S13 | Tattica forzata: linea, difese, perché non si può evitare (da M2) | engine | no |

I titoli dipendono dall'ancora (§8.2-bis, `config/section_titles.yaml`) e sono scritti dal render, non dal LLM.

### 8.2 Matrice di applicabilità (profilo → sezioni)

Legenda: ✔ obbligatoria · ◐ condizionale · — omessa. Le condizioni (D-57) usano solo dati del pacchetto.

| Sezione | 1 Apertura o mediogioco non tattico | 2 Mediogioco tattico | 3 Finale | 4 Finale con tablebase |
| --- | --- | --- | --- | --- |
| S01 | ✔ | ✔ | ✔ | ✔ |
| S02 (M3) | ✔ | ✔ | ✔ | — |
| S03 | ✔ | ◐ c3 | — | — |
| S04 | ◐ c4 | ◐ c4 | — | — |
| S05 | ✔ | ◐ c5 | — (sostituita da S12) | — |
| S06 | ✔ | ✔ | ✔ | ✔ |
| S07 | ✔ | ✔ | ✔ | ✔ |
| S08 | ◐ c8 | ◐ c8 | ◐ c8 | — |
| S09 (M3) | ✔ | ✔ | ◐ c9 | — |
| S10 | ✔ | ✔ | ✔ | ✔ |
| S11 (M4) | ◐ c11 | ◐ c11 | ◐ c11 | — |
| S12 (M2) | — | — | ✔ | ✔ |
| S13 (M2) | — | ✔ | — | — |

Condizioni:

- **c3:** almeno 2 candidate `explained` con `loss_cp ≤ 30`.
- **c4:** `profile.castling` dell'utente **o** dell'avversario è `can_both`, `can_short` o `can_long`.
- **c5** (da M2; usa solo le feature disponibili nella milestone): la sezione tratta solo i pezzi «coinvolti»: quelli che compaiono nel testimone di una feature tattica (`pin`, `hanging_piece`, `unresolved_capture`, `fork`, `skewer`, `overloaded_piece`) o che si muovono nelle prime 4 semimosse delle PV delle prime 3 candidate. Il SectionPlan elenca le case in `focus_squares`.
- **c8:** almeno una mossa con `category` in {`natural_trap`, `hard_move`, `practical_alt`, `improbable_error`} (`solid` non conta). Eccezione: all'ancora 1500 S08 è sempre presente (D-48); all'ancora 2400 contano solo `natural_trap` e `hard_move`.
- **c9 (M3):** almeno una linea con `visible_at_level: false`.
- **c11 (M4):** `elo_ref_fide ≥ 2000` oppure dettaglio 5.

Ogni sezione omessa è registrata come `omitted_sections: [{id, reason}]` e citata nel rapporto finale. **Una sezione non si omette mai «per comodità»**: solo per una regola della matrice, di §8.2-bis o della milestone.

### 8.2-bis Titoli, fusioni ed esclusioni per ancora (D-27)

Il codice le applica nel SectionPlan **dopo** la matrice, nell'ordine: matrice → milestone → ancora → modalità avversario.

| Ancora | Fusioni | Esclusioni | Forma delle sezioni particolari |
| --- | --- | --- | --- |
| 1500 | S04 **assorbita** in S03 (il blocco «principi» nomina il lato di arrocco di ogni sistema) | S11 | S03 contiene anche la mossa consigliata e il «piano semplice» (`must_cover` = raccomandata); S08 sempre presente: errori tipici e tattiche semplici, `theory` ammessa |
| 1900 | nessuna | S11 salvo c11 | come §8.1 |
| 2400 | S04 **assorbita** in S03 («Piani per struttura»: ogni struttura nomina arrocco e corsa di pedoni) | S05 e S10 (salvo dettaglio 5, da M4); S08 secondo c8 | S08 = imprecisioni sottili; T2 in S07 |

**Modalità avversario al tratto (D-54):** S03 e S08 omesse (`opponent_to_move`); S04 segue c4 e, all'ancora 1500 e 2400, resta assorbita in una S03 che non c'è: in quel caso S04 **non** è assorbita ma omessa con motivo `opponent_to_move`. S07 prende il titolo alternativo.

Codici dei motivi: `milestone`, `matrix`, `band_1500`, `band_2400`, `elo<2000`, `detail`, `no_classified_move`, `opponent_to_move`, `unsupported_profile`.

I titoli sono in `config/section_titles.yaml` (Appendice D); `{opp}` si risolve in «il Bianco» o «il Nero» (colore dell'avversario).

**Ordine.** L'ordine di §8.1 è normativo per tutte le ancore.

### 8.2-ter Mappa dei file raw sulle sezioni (D-27, D-49)

I raw corretti (§8-bis.1) hanno ogni titolo marcato con l'ID di destinazione (`<!-- S03 -->`); la tabella riassume. Ogni sezione richiesta dalla matrice e assente nel raw viene scritta ex novo nel fewshot e marcata `needs_review: true` nei metadati.

| File raw | Sezione del raw | → ID | Nota |
| --- | --- | --- | --- |
| `najdorf_w_1500.md` | «In una frase» | S01 | |
| | «Le tre cose da fare adesso» + «La mossa consigliata» + «Piano semplice» | S03 | la raccomandazione nel fewshot è quella calcolata (§4.3) |
| | «Cosa vuole ogni pezzo» | S05 | |
| | «Cosa fa il Nero» | S06 | |
| | «Attenzione a questi errori tipici» | S08 | |
| | «Prima di ogni mossa, controlla» | S10 | |
| | «Radar semplificato» | S02 | da M3: fino ad allora non entra nel fewshot |
| | «Mosse candidate (versione semplice)» | S07 | tabella T1 (colonne dell'ancora 1500) |
| | (assente) | S04 | assorbita: il blocco principi di S03 nomina il lato di arrocco |
| `najdorf_w_1900.md` | sezioni 1–9 | S01, S02, S03, S04, S05, S06, S07, S08, S10 | uno a uno; «Dove vanno i pezzi neri» e la tabella di `...Nc6` stanno in S06 (la seconda è T3); la tabella delle candidate è T1 |
| `najdorf_w_2400.md` | «Sintesi» | S01 | |
| | «Test critici di move order» | S07 | T2 |
| | paragrafo «...Nc6 del Nero» | S06 | T3 + testo |
| | «Piani per struttura» | S03 | S04 assorbita |
| | «Fattori pratici (Maia a 2400)» | S06 | la frase di confidenza la mette il render (D-46): il fewshot ne conserva solo il resto |
| | (assente) | S07 T1 | il fewshot aggiunge T1 |
| `calibration_levels.md` | «Cosa cambia tra i livelli» | — | non è output: diventa `docs/CALIBRATION_GUIDE.md` |

### 8.3 Disponibilità per milestone

| Sezione | M1 | M2 | M3 | M4+ |
| --- | --- | --- | --- | --- |
| S01, S03, S04, S05, S06, S07, S08, S10 | ✔ | ✔ | ✔ | ✔ |
| S12, S13, matrice completa | — | ✔ | ✔ | ✔ |
| S02, S09 | — | — | ✔ | ✔ |
| S11, dettaglio 1–5, modalità *entrambi* | — | — | — | ✔ |

In M1 la matrice si applica solo alla colonna 1. Per le altre colonne il SectionPlan contiene solo S01, S06, S07, S10 (le altre `omitted: unsupported_profile`) e la testata riporta l'avviso `profile_unsupported`. Con `elo_ref_fide` ≥ 2150 in M1 il rapporto riporta l'avviso `move_order_limited`. Con avversario al tratto vale §2-bis.6.

### 8.4 SectionPlan

Il codice produce la lista ordinata delle sezioni (`pack/section_plan.py`):

```
SectionPlanEntry
  id: "S01".."S13"
  title: str | null                  # null se assorbita o omessa
  required: bool                     # true = il LLM deve scriverla
  absorbed_into: "S03" | null
  omitted: reason | null
  word_budget: int | null
  max_pv_plies: int                  # = plies_max della fascia (dettaglio compreso)
  theory_allowed: bool               # §8.1 e D-48
  tables: ["T1", ...]                # tabelle che devono comparire in questa sezione (§8.5)
  must_cover: [ID]                   # ID che devono comparire in almeno un token della sezione
  focus_squares: [str]               # solo S05 in colonna 2
  maia_low_confidence: bool          # il render inserira' la frase fissa (S06, S08)
```

**`must_cover`:** S07 → tutte le candidate `explained` (o tutte le `R<n>`); S08 → tutte le mosse con categoria che conta per c8; S03 all'ancora 1500 → la raccomandata; S01 → nessuno.

**Budget di parole (D-45):** `totale = prose_words(fascia) × moltiplicatore(dettaglio)`; per ogni sezione con `required: true`, `peso = section_budget[ancora][id] + Σ pesi delle sezioni assorbite in essa`; `word_budget = round(totale × peso / Σ pesi delle sezioni required, −1)` (arrotondato alle decine). I pesi sono in `config/section_budget.yaml` (Appendice D).

Esempio (ancora 2400, M2): S01 120 parole; S03 con S04 assorbita; S05 e S10 omesse (`band_2400`); S07 con `tables: ["T1", "T2"]` e `must_cover` = le candidate spiegate.

### 8.5 Tabelle T1–T4 (D-44, `config/tables.yaml`)

Le tabelle sono costruite dal render a partire da `pack.tables`; il LLM le colloca con un blocco `{"type": "table", "ref": "T1"}` e può riempire solo le colonne di testo indicate. Le celle di testo sono `ParagraphLite` (§9-bis.6), contano nelle parole della sezione e seguono tutte le verifiche. ID delle righe: `T1` usa gli ID delle mosse (`C<n>` o `R<n>`); `T2` e `T3` usano `r1`, `r2`, … in ordine di tabella.

**T1 — candidate (S07, utente al tratto).** Righe: `listed` ∪ `explained`, ordinate per `eval_user_cp` decrescente. La raccomandata è in grassetto con il simbolo ★ dopo la mossa.

| Ancora | Colonne (dati → testo) |
| --- | --- |
| 1500 | Mossa · Valutazione · Scelta a {elo} · **Per chi** (testo) |
| 1900 | Mossa · Valutazione · Scelta a {elo} · Linea del motore · **Idea** (testo) |
| 2400 | Mossa · Valutazione · Scelta a {elo} · Linea del motore · **Nota** (testo) |

- *Mossa* = mossa numerata (`6.Be3`); *Valutazione* = `{{ev:C}}`; *Scelta a {elo}* = `{{pct:C.p_user}}` (con l'Elo dichiarato nell'intestazione); se `maia.confidence = low` l'intestazione ha un asterisco e sotto la tabella c'è la nota `maia_low_confidence_table`.
- *Linea del motore* = semimosse della PV dalla seconda in poi, al massimo `t1_line_plies` (1900: 6; 2400: 8) e mai oltre `plies_max − 1`, numerate (`6...e5 7.Nb3 Be7 8.f3 Be6 9.Qd2`).
- Le celle di testo sono ammesse per ogni riga; una riga senza testo mostra «—».

**T1 alternativa (S07, avversario al tratto).** Righe: `R<n>`. Colonne: Risposta · Probabilità a {elo avversario} · Valutazione · La tua risposta migliore (`R<n>.u1` numerata con valutazione) · **Come prepararsi** (testo).

**T2 — move order (S07, solo ancora 2400; all'ancora 1900 solo con dettaglio 5).** Righe, per ogni candidata di E3 nell'ordine: una riga «Dopo `c`» con le mosse di `Rset(c)` e le loro valutazioni; poi per ogni `r` una riga «Dopo `c r`» con le prime 3 mosse del nodo ℓ1 e le valutazioni; da M2 le righe ℓ2 («Dopo `c r u`», prime 3 mosse dell'avversario) e ℓ3 («Dopo `c r u r′`», prime 3 dell'utente). Colonne: Dopo · Mosse (dalla migliore per chi muove) · **Nota** (testo). Formato delle mosse: `7.Bg5 (+0,38), 7.Bc1 (+0,36), 7.Qd2 (0,00)`.

**T3 — mossa di contesto (S06, ancore 1900 e 2400; assente se `context_move = null`).** Righe = `context_move.rows`. Colonne: Dopo… · Migliore di {opp} (mossa e valutazione) · {mossa di contesto} (valutazione) · Costo (`loss` in pedoni). Nessuna colonna di testo: il commento va nel paragrafo che segue.

**T4 — radar (S02, da M3).** Colonne: Categoria · T (tu) · R · **Nota** (testo). Righe ordinate per `R` decrescente.

Le tabelle assegnate a ciascuna sezione (`tables` del SectionPlan) sono: T1 → S07 sempre; T2 → S07 secondo la regola sopra e solo se E3 ha prodotto almeno una riga; T3 → S06 se esiste; T4 → S02.

### 8.6 Testata e rapporto finale

**Testata** (render, testi in `config/wording.yaml: header`):

```
# Analisi della posizione: {opening.name | "posizione senza nome"}

FEN: `{fen}` · Tratto: {il Bianco | il Nero} · Giochi con: {il Bianco | il Nero}
Elo dichiarato {elo_declared} {FIDE | Lichess} → {elo_maia} in scala Lichess usata da Maia-2 · Avversario: {…}
Fascia {fascia} · Ancora {ancora} · Profilo {budget} · Stockfish {versione} · profondità radice {depth}

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> {avvisi: references_not_validated, profile_unsupported, move_order_limited, maia_low_confidence_header, unstable_nodes}
```

**Rapporto finale** (in coda ad `analysis.md`, sotto il titolo «Rapporto tecnico»): versioni di Stockfish, Maia-2 e del modello di linguaggio; profilo, tempo totale, nodi analizzati, profondità minima e massima; nodi `unstable_depth` (elenco degli ID con il percorso); Elo dichiarato, Elo Maia, fascia, ancora, confidenza di Maia-2; sezioni omesse e assorbite con motivo; fasi e nodi omessi; numero di paragrafi `theory` e quota sulle parole; esito di ogni controllo V01–V11; numero di retry; elementi rimossi o marcati in modalità degradata; `notes` del modello; nota a piè di pagina «† contenuto teorico, non verificato dai motori» se ci sono paragrafi `theory`.

---

## 8-bis. Output di riferimento (golden examples)

Prima di scrivere codice e prompt abbiamo fissato con esempi concreti **come deve essere ogni output**, livello per livello.

### 8-bis.1 File raw

Tutti sulla posizione di esempio (Najdorf, Bianco, mossa 6): `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6`. I raw della v0.9 sono **corretti e divisi per ancora** (D-49) e si copiano in `examples/golden/raw/`:

| File (ASCII, D-34) | Contenuto | Origine |
| --- | --- | --- |
| `najdorf_w_1500.md` | Esempio 1500 | Parte A di «Esempi di output ideale — Najdorf, Bianco: 1500 e 2400.md» |
| `najdorf_w_1900.md` | Esempio 1900 | «Esempio di output ideale — Najdorf, Bianco, 1900.md» |
| `najdorf_w_2400.md` | Esempio 2400 | Parte B dello stesso file del 1500 |
| `calibration_levels.md` | Tabella «Cosa cambia tra i livelli» | Coda dello stesso file |

Ogni raw ha un'intestazione YAML (`id`, `anchor`, `fen`, `user_color`, `source`, `status: raw_v0`, `validated: false`, `corrections`, `needs_review`) e ogni titolo di sezione porta il commento con l'ID di destinazione. Le correzioni di contenuto rispetto agli originali sono elencate in `corrections` (dati di Stockfish invariati).

**Stato dei raw.** Dati di Stockfish 16 reali (profondità ≈ 17–22); campi `[MAIA]` come segnaposto; punteggi del radar illustrativi; contenuto tematico (piani, arrocco, obiettivi dei pezzi) scritto da conoscenza scacchistica e **non validato**. I raw **non vanno mai usati come few-shot**.

### 8-bis.2 Come sono stati creati (procedimento originale)

Stockfish 16 via UCI con `python-chess` (4 thread, Hash 1 GB), quattro analisi: radice MultiPV 12 (40 s); mossa nulla (15 s); risposte del Nero ai sistemi principali MultiPV 8 (25 s); test di move order MultiPV 5–6 (22 s). Valori in pedoni dal punto di vista del Bianco. Il contenuto tematico è stato rivisto dall'utente: l'arrocco dipende dal sistema; il fianchetto è tipico del Dragon; `...Be6` e `...Nc6` sono mosse del Nero da valutare per contesto; `...Nc6` è stato **verificato col motore** (costa ≈ 0,5 dopo 6.Be3 e5 7.Nb3, ≈ 0,1 contro 6.Be2, ≈ 0 contro 6.f4). Questo ciclo «umano → motore» è ciò che l'app automatizza (§3-ter.6).

### 8-bis.3 Regola: ogni output deve essere così

1. **Struttura:** sezioni del SectionPlan (§8.4), nell'ordine di §8.1; omissioni solo per matrice, ancora, modalità o milestone.
2. **Ogni numero è tracciabile** a un token risolto dal pacchetto (D-08).
3. **Ogni paragrafo dichiara la fonte** (`engine`, `feature`, `maia`, `theory`, `mixed`) con le regole di V10.
4. **Densità e tono** come §7.
5. **Il contesto decide:** la stessa mossa è buona o cattiva a seconda del sistema; l'output riporta il costo contestuale (T3, token `loss:SAN@N`), non giudizi assoluti.
6. **Onestà sui limiti:** confidenza di Maia-2, profondità instabili, sezioni e nodi omessi.
7. **Distinzione eval/policy:** valutazione di Stockfish e probabilità di Maia-2 non si mescolano senza dirlo.

### 8-bis.4 Procedimento golden in due tempi (D-49)

**M0 — `chessanalyst golden --data`** (richiede solo gli adattatori dei motori e la primitiva di §3.1.3):

1. Esegue sulla posizione d'esempio le quattro analisi del §8-bis.2 con i parametri del profilo `deep` (radice `MultiPV` 16, nodi `MultiPV` 8, profondità minime `deep`): radice; mossa nulla; nodi dopo `6.Be3`, `6.Be2`, `6.Bg5`, `6.f4`; nodi dei test di move order citati nei raw (`6.Be3 Ng4`, `6.Be3 e5 7.Nb3`, `6.Be3 e5 7.Nb3 Be6`, `6.Be3 e6`, `6.Bg5 e6 7.f4`, `6.Be2 e5 7.Nb3`, `6.Be2 e5 7.Nb3 Be7`, `6.f4 e5 7.Nb3`). Salva i risultati in `fixtures/golden_nodes.json`.
2. Interroga Maia-2 alla radice e in quei nodi per 1500, 1900 e 2400 dichiarati (con la conversione di §3-bis) e salva in `fixtures/golden_maia.json`.
3. Scrive `docs/golden_diff.md`: per ogni valore numerico dei raw il valore nuovo e la differenza; segnala ogni scostamento > 0,25 pedoni e ogni candidata delle prime 3 dei raw che esce dalle prime 6 (AC-09).
4. Misura le parole di prosa per sezione dei raw (regola di §9-bis.8, escludendo tabelle numeriche e righe `[MAIA]`) e le riporta in `docs/golden_diff.md` come prima stima.
5. Copia `calibration_levels.md` in `docs/CALIBRATION_GUIDE.md` con un'introduzione: «Guida qualitativa per chi scrive prompt ed esempi; non normativa oltre §7».

**M1b — `chessanalyst golden --packs` e `--render`** (richiede pacchetto, verifica e render):

1. `--packs` esegue la pipeline completa (M1a, profilo `deep` limitato a ℓ1) sulla posizione d'esempio per le tre ancore (utente Bianco; Elo 1500, 1900, 2400 FIDE) e salva `examples/golden/packs/najdorf_w_<ancora>.pack.json`. **Questi file sono congelati nel repository**: i loro ID sono quelli usati dai fewshot. Si rigenerano solo intenzionalmente (opzione `--force`), e allora i fewshot vanno riallineati.
2. Claude Code scrive **una volta** `examples/golden/fewshot/najdorf_w_<ancora>.json` nel formato di §9-bis.6, a partire dal raw della stessa ancora: stesse idee, struttura del SectionPlan del pacchetto congelato, ogni numero e ogni mossa sostituiti con il token corrispondente del pacchetto, testo adattato dove i dati nuovi differiscono dal raw, raccomandazione = quella calcolata. Sezioni nuove o riscritte in modo sostanziale sono elencate in `examples/golden/fewshot/najdorf_w_<ancora>.meta.yaml` (`needs_review: [S..]`, `validated: false`).
3. `--render` esegue V01–V10 su ogni fewshot contro il proprio pacchetto (deve passare senza errori, AC-27) e produce `examples/golden/rendered/najdorf_w_<ancora>.md` con il render normale. `rendered` è quindi sempre **derivato**: non si modifica a mano.
4. Scrive `examples/golden/fewshot/_terms.txt` (§10, V09) con almeno: `Najdorf|Najdorf`, `Scheveningen|Scheveningen`, `Dragon|Dragon`, `attacco inglese|English Attack`, `Pedone Avvelenato|Poisoned Pawn`, `Sozin|Sozin`, più ogni altro nome di apertura, variante o struttura presente nei fewshot.
5. Scrive `examples/golden/fewshot/_s07_alt.json`: un frammento con la sola S07 alternativa, scritto sul pacchetto della fixture AC-21, usato come secondo esempio di forma in modalità avversario (§9.2).
6. Misura le parole dei fewshot e aggiorna `prose_words`, `section_budget.yaml` e `theory_max_share` se la misura si discosta di oltre il 15% (§0.5), annotando in `docs/golden_diff.md`.

**M2:** rigenera il pacchetto 2400 (e 1900) con ℓ2–ℓ3 e completa T2/T3 nei fewshot; da quel momento `rendered` è il **target completo**.

### 8-bis.5 Validazione umana

Ogni fewshot va rivisto da un giocatore del livello corrispondente (l'esempio 2400 da un giocatore di quel livello) e poi marcato `validated: true` nel suo `meta.yaml`. Finché un esempio non è validato, l'output dell'app che lo usa riporta in testata l'avviso `references_not_validated`.

### 8-bis.6 Espansione

Obiettivo: 5–8 posizioni × 3 livelli, per tipo di profilo: apertura chiusa, mediogioco tattico, struttura pedonale (isolato/arretrato), finale di torri, attacco al re, finale con tablebase. Fino a M2 l'accettazione contenutistica vale **solo per la Najdorf**; da M2 ogni nuova posizione ha una checklist in `fixtures/checklists/<id>.yaml` (sezioni attese secondo la matrice, 3 mosse che devono comparire nei token, 2 errori tipici che il testo deve citare). Il rischio di «trascinamento» dei temi Najdorf in altre posizioni è coperto da V09.

---

## 9. Prompt e chiamata al modello

### 9.1 Chiamata

- SDK `anthropic` (Python). Modello `llm.model` (default `claude-sonnet-5-5`). `max_tokens = llm.max_tokens` (16000). `temperature = llm.temperature` (0,3): se l'API rifiuta il parametro per il modello scelto si ripete la richiesta senza, una sola volta, e lo si annota nel log.
- **Output forzato tramite strumento:** `tools = [submit_analysis]` (schema in Appendice F, generato da `llm/schema.py` con `model_json_schema()` di `pydantic` e confrontato con l'appendice da un test) e `tool_choice = {"type": "tool", "name": "submit_analysis"}`. Nessun «extended thinking» (non compatibile con lo strumento forzato). La risposta valida è l'`input` del blocco `tool_use`.
- **System prompt:** testo dell'Appendice E.1 (con le parti variabili sostituite), in un blocco con `cache_control: {"type": "ephemeral"}`.
- **Messaggio utente:** modello dell'Appendice E.2: esempio few-shot con legenda, vista ridotta del pacchetto (§6.1), istruzioni dell'analisi.
- Stima: 8–14k token in ingresso, 3–6k in uscita.

### 9.2 Scelta dell'esempio few-shot

| `elo_ref_fide` | Ancora | Esempio |
| --- | --- | --- |
| < 1750 | 1500 | `fewshot/najdorf_w_1500.json` |
| 1750 – 2149 | 1900 | `fewshot/najdorf_w_1900.json` |
| ≥ 2150 | 2400 | `fewshot/najdorf_w_2400.json` |

Un solo esempio per chiamata. In modalità avversario al tratto si aggiunge `fewshot/_s07_alt.json` (solo S07). Quando esisteranno esempi su posizioni diverse (§8-bis.6) si sceglie prima per `matrix_column`, poi per ancora.

**Legenda dei token dell'esempio.** Il codice risolve ogni token del fewshot contro il suo pacchetto congelato e produce righe `{{ev:C1}} → +0,37`, in ordine di prima comparsa, così il modello vede come un token diventa testo senza ricevere il pacchetto dell'esempio. Legenda ed esempio sono preceduti dall'avviso: «Questo esempio riguarda un'altra posizione (o la stessa con dati diversi): imita struttura, densità e tono, non il contenuto».

### 9.3 Errori di rete e retry di verifica (D-61)

**Rete.** Client con `max_retries = 0`. Su errori di connessione, `429`, `500`, `502`, `503`, `504`, `529`: fino a 3 tentativi con attese di 2, 4, 8 secondi (più `retry-after` se presente). Dopo il terzo fallimento: codice di uscita 5, pacchetto già salvato, messaggio con `chessanalyst rerun <cartella>`. Errori `400`, `401`, `403`: nessun tentativo, codice 5 (401/403: «Chiave API non valida o non autorizzata»).

**Verifica.** Dopo ogni risposta si eseguono V01–V10 (§10). Se ci sono errori «retry» e i retry usati sono meno di `llm.max_retries` (2) (se gli unici errori sono di V07(d), parole fuori budget, si fa al massimo **un** retry):

1. si aggiunge ai messaggi la risposta del modello così come ricevuta (blocco `tool_use` compreso);
2. si aggiunge un messaggio utente con un blocco `tool_result` (`tool_use_id` del blocco precedente, `is_error: true`) il cui testo è l'elenco degli errori nel formato `V03 · S06 · blocco 2 · «...Nc6» · <suggerimento>` (suggerimenti in `config/wording.yaml: verify_hints`), seguito dalla frase «Correggi solo questi punti e richiama submit_analysis con l'analisi completa»;
3. si richiama l'API con lo stesso `tool_choice`.

`stop_reason = "max_tokens"` o assenza del blocco `tool_use` equivalgono a un errore V01. Tutte le risposte sono salvate in `llm_raw.json`. Dopo l'ultimo retry si applica la modalità degradata (§10.2) sull'ultima risposta che ha superato V01; se nessuna lo ha superato: codice 5.

**`rerun`.** Legge `pack.json`, ricostruisce SectionPlan e tabelle **dal pacchetto** (non dalla configurazione corrente), usa la configurazione corrente per modello, prompt, verifica e render, scrive nella stessa cartella `analysis.md`, `llm_raw.json`, `verification.json` (i precedenti diventano `*.prev.*`). Se `config_hash` differisce da quello corrente lo segnala come avviso, senza bloccare.

---

## 9-bis. Schema di output e token

### 9-bis.1 Principi

Il LLM produce una struttura, non una pagina: il codice sostituisce i token con i dati, costruisce le tabelle, scrive titoli, testata, frasi fisse e rapporto, e verifica tutto. «Coerenza numerica» e «mosse legali» sono garantite per costruzione.

### 9-bis.2 Grammatica dei token (D-41)

```
token     = "{{" kind ":" arg "}}"                       ; nessuno spazio dentro le graffe
NID       = "N" INT        CID = "C" INT        RID = "R" INT
RUID      = RID ".u" INT   PVID = "PV" INT     INT = [1-9][0-9]*
SAN       = mossa SAN di python-chess, senza "+" "#" "!" "?" (si accettano e si ignorano)
MOVE_AT   = SAN "@" NID
SQ        = [a-h][1-8]
```

| Token | Argomenti ammessi | Si risolve in | Esempio di resa |
| --- | --- | --- | --- |
| `{{mv:X}}` | `CID`, `RID`, `RUID` | Mossa numerata | `6.Be3`, `6...e5`, `7.Nb3` |
| `{{mv:X:bare}}` | idem | SAN senza numero né puntini | `Be3`, `e5` |
| `{{m:MOVE_AT}}` | — | SAN, con `...` davanti se nel nodo muove il Nero | `Nb3`, `...Nc6` |
| `{{m:MOVE_AT:num}}` | — | Mossa numerata dal nodo | `7.Nb3`, `7...Nc6` |
| `{{ev:X}}` | `CID`, `RID`, `RUID`, `NID`, `MOVE_AT` | Valutazione, pedoni, punto di vista dell'utente (§9-bis.7) | `+0,37` |
| `{{loss:X}}` | `CID`, `RUID`, `MOVE_AT` | Perdita di chi muove rispetto alla migliore in quel punto, pedoni, senza segno | `0,15` |
| `{{pct:X}}` | `CID.p_user`, `CID.p_up`, `RID.p_opp`, `RUID.p_user`, `root.win`, `root.draw`, `root.loss`, `MOVE_AT` | Probabilità (Maia-2) o quota WDL (Stockfish, `root.*`, punto di vista dell'utente) | `18%` |
| `{{pv:PVID:n}}` | `n` ≥ 1 | Prime `n` semimosse della PV dal suo nodo di partenza, numerate | `6.Be3 e5 7.Nb3 Be7 8.f3 Be6` |
| `{{plan:S:SAN,…@NID}}` | `S` = `w` \| `b` | Sequenza di piano (§9-bis.3) | `Be2 → Be3 → O-O` |
| `{{diag:SQ-SQ}}` | due case allineate (stessa diagonale, colonna o traversa) | Linea geometrica | `a7–g1` |
| `{{elo:user}}` / `{{elo:opp}}` | suffisso facoltativo `:full` | Elo dichiarato (con la scala se `:full`) | `1900`, `1900 FIDE` |
| `{{opening:name}}` / `{{opening:eco}}` | — | Nome (dalla fonte, in inglese) o codice ECO | `B90` |
| `{{txt:opp}}` / `{{txt:me}}` | — | Colore dell'avversario / dell'utente con articolo | `il Nero` |
| `{{txt:p_up_group}}` | — | Etichetta del gruppo di `p_up` (`config/wording.yaml`) | `giocatori della fascia più forte del modello` |
| `{{sc:CAT.T}}` / `{{sc:CAT.R}}` | categoria di §5-bis (M3) | Punteggio | `88` |

**Risoluzione e significato preciso:**

- `ev:CID` = valore della candidata alla radice (E0 o E4); `ev:NID` = prima riga dell'analisi del nodo; `ev:SAN@NID` = valore della riga di quella mossa nel nodo (deve comparire nel `multipv` del nodo o in una ricerca `root_moves` registrata nel nodo). I due primi possono differire (D-40).
- `loss:SAN@NID` = `eval(migliore) − eval(SAN)` dal punto di vista di chi muove nel nodo, ≥ 0. `loss:RUID` è rispetto a `RID.u1`.
- `pct:SAN@NID` = probabilità di Maia-2 nel nodo (nodo con `maia` non nullo; una mossa legale assente dalla policy salvata vale `< 1%`).
- `mv:RID` e `mv:RUID` esistono solo in modalità avversario; `mv:CID` solo con l'utente al tratto.
- **Errori V02:** sintassi non valida; ID inesistente; tipo di argomento non ammesso per quel token; valore `null` (per esempio `pct:C1.p_up` con `p_up = null`, `opening:name` senza apertura, `txt:p_up_group` senza `p_up`); `pv` con `n` maggiore della lunghezza della PV; `ev`/`loss` su una mossa senza valutazione nel nodo; `pct` su un nodo senza Maia-2.
- **Errori V04:** `SAN` illegale nel nodo; `plan` non valido; `diag` con case non allineate o uguali.
- **Errori V05:** `pv` con `n` > `max_pv_plies` della sezione.

### 9-bis.3 Token `plan` (D-26)

Serve a nominare idee e piani che non sono mosse analizzate: «g4-g5», «Be2 → Be3 → O-O», «...b5 → ...b4».

- **Sintassi:** `{{plan:<w|b>:<SAN1>,<SAN2>,…@<NID>}}`; da 1 a `plan_max_moves` (6) mosse dello **stesso lato**.
- **Validazione (V04):** dal FEN del nodo; se il lato indicato non è al tratto si applica una mossa nulla (sequenza rifiutata se il lato al tratto è sotto scacco); ogni SAN deve essere legale per il lato; dopo ogni mossa non finale si applica una mossa nulla (rifiutata se la mossa appena giocata dà scacco: lo scacco è ammesso solo come ultima mossa).
- **Resa:** mosse unite da « → », senza numeri; per il Nero ogni mossa è preceduta da `...` (`...b5 → ...b4`); arrocchi `O-O` / `O-O-O`.
- **Natura:** un `plan` non porta valutazione e non garantisce che la sequenza sia buona. Ammesso solo in paragrafi `theory` o `mixed` (V10).

### 9-bis.4 Che cosa si può scrivere in chiaro

Nel testo libero sono ammessi: parole italiane (nomi dei pezzi: «cavallo», «alfiere in e3»), **case isolate** (`d5`), colonne e traverse a parole («colonna c», «settima traversa»), nomi di apertura e di strutture (soggetti a V09), i letterali di `v03_allowed_literals` (`Maia-2`), grassetto `**…**` e corsivo `*…*`. Non sono ammessi (V03): mosse SAN, arrocchi scritti (`O-O`: si scrive «arrocco corto»), catene di case (`g4-g5`, `a7–g1`), puntini davanti a una mossa (`...b5`), numeri di mossa, **qualunque cifra** al di fuori delle case isolate (i conteggi si scrivono in lettere: «tre sistemi»; l'Elo con `{{elo}}`), «cp», figurine Unicode. Altro markup (titoli `#`, link, codice, HTML, tabelle in Markdown) è vietato (V01).

### 9-bis.5 Asserzioni tipizzate

Ogni paragrafo può portare `assertions`, verificate contro il pacchetto (V06):

| `kind` | Campi | Verifica |
| --- | --- | --- |
| `feature` | `key` (catalogo §5.1), `side` (`w` \| `b` \| `null`), `squares` (facoltativo) | Esiste nel pacchetto una feature con stessa `key` e stesso `side` e le `squares` indicate sono un sottoinsieme del suo testimone |
| `eval_band` | `ref` (`CID`, `RID`, `RUID`, `NID`, `MOVE_AT`), `band` (§6.4) | La valutazione cade nella banda |
| `maia_band` | `ref` (come gli argomenti di `pct`, escluso `root.*`), `band` (§6.4) | La probabilità cade nella banda |
| `classification` | `ref` (`CID`), `category` (§4.2) | La candidata ha quella categoria |
| `category_advice` (M3) | `id`, `advice` | Coerente con `T`/`R` |

Il testo libero non viene interpretato: la corrispondenza fra frase e asserzione è controllata solo dal «critico» opzionale (M4). Il limite è dichiarato nel rapporto.

### 9-bis.6 Schema di output (D-47, Appendice F)

```
AnalysisOutput
  schema_version: "1"
  sections: [Section]                  # esattamente le sezioni required, nell'ordine del piano
  notes: [str]                         # incoerenze rilevate nel pacchetto (vanno nel rapporto)

Section       { id: "S01".."S13", blocks: [Block] (almeno 1) }
Block         uno tra:
  Paragraph   { type: "p",  text: str, source: Source, assertions?: [Assertion] }
  List        { type: "ul" | "ol", items: [ParagraphLite] (almeno 1) }
  Line        { type: "line", pv: PVID, plies: int, caption?: ParagraphLite }
  DataTable   { type: "table", ref: "T1".."T4", text_cells?: { rowId: { column: ParagraphLite } } }
  TextTable   { type: "text_table", columns: [str] (2-6, intestazioni senza cifre), rows: [[ParagraphLite]] }
ParagraphLite { text: str, source: Source, assertions?: [Assertion] }
Source        "engine" | "feature" | "maia" | "theory" | "mixed"
```

- Le intestazioni di `TextTable` contano nelle parole e seguono V03.
- Le chiavi `column` di `text_cells` sono quelle di testo della tabella (§8.5: `per_chi`, `idea`, `nota`, `prepare`); `rowId` deve esistere nella tabella.
- `Line.plies` segue le stesse regole di `{{pv}}`.

### 9-bis.7 Formati numerici (render, `render/format_it.py`)

| Grandezza | Regola | Esempi (ingresso → resa) |
| --- | --- | --- |
| Valutazione (`ev`) | `cp / 100` arrotondato a 2 decimali (metà lontano da zero), virgola decimale, segno sempre esplicito (`+`, `-` ASCII) salvo `0,00` | 37 → `+0,37`; −15 → `-0,15`; 0 → `0,00`; 4 → `+0,04`; 250 → `+2,50` |
| Matto (`ev` con `mate_user`) | In prosa: «matto in {n} per te» / «matto in {n} per {opp}»; in tabella `#3` / `-#3` | `mate_user = 3` → `matto in 3 per te` |
| Perdita (`loss`) | come la valutazione ma senza segno; se una delle due è matto: «decisiva» | 15 → `0,15` |
| Probabilità (`pct`) | `round(p × 100)` intero con `%`; `0 < p < 0,005` → `<1%`; `p = 0` → `0%`; arrotondamento a 100 con `p < 1` → `>99%` | 0,183 → `18%`; 0,004 → `<1%` |
| WDL (`pct:root.*`) | per mille / 10 arrotondato | 920 → `92%` |
| Mossa numerata | Bianco `N.SAN`, Nero `N...SAN`; una sequenza prosegue `6.Be3 e5 7.Nb3`; se inizia col Nero `6...e5 7.Nb3` | |
| Elo | intero senza separatori | `1900` |

AC-28 verifica la tabella.

### 9-bis.8 Conteggio delle parole (D-45)

Per ogni testo scritto dal LLM (paragrafi, voci di elenco, didascalie, celle di testo, intestazioni di `TextTable`): ogni token `{{…}}` è sostituito da una parola fittizia; si tolgono `*`; il numero di parole è il numero di corrispondenze dell'espressione `[A-Za-zÀ-ÖØ-öø-ÿ0-9]+` (l'apostrofo separa: «l'alfiere» vale due). Le parole di una sezione sono la somma dei suoi testi. Lo stesso conteggio serve per V07, V08 e per la misura dei golden.

### 9-bis.9 Politica del contenuto `theory`

- Ammesso solo nelle sezioni con `theory_allowed: true` (§8.1, D-48).
- In un paragrafo `theory` sono vietati i token `ev`, `loss`, `pct`, `pv`, `sc`; ammessi `m`, `mv`, `plan`, `diag`, `elo`, `opening`, `txt`.
- **Quota:** parole dei blocchi `theory` / parole di prosa totali ≤ `theory_max_share[ancora]` (1500: 0,70; 1900: 0,50; 2400: 0,35).
- Il render marca ogni blocco `theory` con † e aggiunge una sola nota a piè di pagina: «† contenuto teorico, non verificato dai motori». `verification.json` elenca i blocchi `theory` con sezione e testo.
- Un'affermazione che può essere un fatto del motore **non** va dichiarata `theory`: se il pacchetto contiene il dato, si usa il token.

---

## 10. Verifica e anti-allucinazione (modulo critico)

### 10.1 Controlli

Eseguiti su ogni risposta, nell'ordine; gli errori sono raccolti tutti (non ci si ferma al primo), ciascuno con codice, sezione, indice del blocco (e riga/colonna se cella), testo incriminato.

| Codice | Controllo | Esito se fallisce |
| --- | --- | --- |
| V01 | JSON valido secondo lo schema (`pydantic`); presenza del blocco `tool_use`; testo senza markup vietato (§9-bis.4: righe che iniziano con `#`, `[testo](`, backtick, `<`) | retry |
| V02 | Ogni token è sintatticamente valido e si risolve (§9-bis.2) | retry |
| V03 | Testo libero (token sostituiti da `§`, letterali ammessi rimossi). Le espressioni esatte sono in `config/verify.yaml` (Appendice D.10). **Passo 1**, nessuna corrispondenza per: mosse di pezzo `(?<![A-Za-z])[KQRBN][a-h]?[1-8]?x?[a-h][1-8]`; catture di pedone `(?<![A-Za-z])[a-h]x[a-h][1-8]`; arrocchi `\b[O0]-[O0]`; promozioni `=[QRBN]`; catene di case `[a-h][1-8]\s*[-–—→]\s*[a-h][1-8]`; puntini (tre punti o «…» davanti a una lettera di mossa); numeri di mossa `(?<![a-h0-9])\d+\s*\.(?!\d)` (una casa a fine frase, «d5.», non è un numero di mossa); `\bcp\b`; figurine `[\u2654-\u265F]`. **Passo 2**, tolte le case isolate `(?<![A-Za-z])[a-h][1-8](?![0-9])`, non resta alcuna cifra `\d` | retry |
| V04 | Legalità di `m:SAN@N`; validità di `plan` e `diag` | retry |
| V05 | `pv` e blocchi `line` entro `max_pv_plies` | retry |
| V06 | Asserzioni tipizzate coerenti con il pacchetto | retry; dopo i retry: blocco marcato «⚠ non verificato» |
| V07 | Struttura: (a) sezioni = quelle `required` del piano, nell'ordine, senza extra; (b) ogni tabella di `tables` compare una e una sola volta nella sua sezione e in nessun'altra; (c) ogni ID di `must_cover` compare in almeno un token della sezione; (d) parole della sezione entro `word_budget ± max(25%, 15)` | (a)–(c) retry; (d) un retry, poi solo avviso |
| V08 | `theory`: solo in sezioni ammesse, token vietati assenti, quota entro il tetto | retry |
| V09 | Contaminazione, solo se l'EPD analizzata ≠ EPD dell'esempio few-shot (D-52): nessun termine di `_terms.txt` nel testo (confronto senza maiuscole, parola intera) a meno che uno dei suoi alias compaia in `opening.name` del pacchetto | retry |
| V10 | Coerenza `source`/token (tabella sotto) | retry |
| V11 | Controllo deterministico del documento finale: frase di bassa confidenza presente dove previsto (D-46), nodi `unstable_depth` elencati nel rapporto, nessun token non risolto rimasto | eccezione (è un bug del render), codice 1 |

**Regole di V10 (D-47):**

| `source` | Deve contenere | Non può contenere |
| --- | --- | --- |
| `engine` | almeno un token `ev`, `loss`, `pv`, `pct:root.*` oppure un blocco `line` | `pct` di Maia-2, `plan`, `sc` |
| `maia` | almeno un `pct` di Maia-2 (`p_user`, `p_up`, `p_opp`, `pct:SAN@N`) | `ev`, `loss`, `pv`, `plan` |
| `feature` | almeno un'asserzione `feature` | `ev`, `loss`, `pct`, `pv`, `plan` |
| `theory` | — | `ev`, `loss`, `pct`, `pv`, `sc` (§9-bis.9) |
| `mixed` | almeno un token `ev`, `loss`, `pv`, `pct` oppure un'asserzione | — |

### 10.2 Retry e modalità degradata

Politica di retry in §9.3 (massimo 2). Dopo l'ultimo tentativo (`llm.on_fail = mark`):

- errori V02, V03, V04, V05, V08, V09, V10 in un blocco → il blocco (o la cella, o la voce di elenco) è **rimosso**; se una sezione resta vuota vale la regola della sezione mancante;
- errori V06 → blocco mantenuto con «⚠ non verificato»;
- V07 (a) sezione mancante → il render la inserisce con il testo fisso `section_unavailable`; sezione extra → eliminata; ordine sbagliato → riordinato; (b) tabella mancante → aggiunta in coda alla sezione, tabella doppia → tenuta la prima; (c) `must_cover` mancante → avviso; (d) budget → avviso;
- con `on_fail = drop` le sezioni con errori sono eliminate per intero e sostituite dal testo fisso.

L'analisi non viene mai consegnata con un errore non segnalato: ogni rimozione o marcatura è elencata nel rapporto.

**Opzionale (M4):** seconda chiamata «critico» che cerca incoerenze logiche tra frasi e dati e controlla la corrispondenza testo↔asserzioni.

### 10.3 `verification.json`

```
{ "attempts": [ { "n": 1, "errors": [ {"code", "section", "block", "cell", "text", "hint"} ] } ],
  "final": { "passed": [codici], "warnings": [...], "removed": [...], "marked": [...] },
  "theory_blocks": [ {"section", "text", "words"} ], "theory_share": float,
  "words_by_section": { "S01": {"budget", "actual"} } }
```

---

## 11. Stack, struttura del progetto, configurazione

### 11.1 Stack

Python 3.12 (3.11 se `maia2` lo richiede, §0.5) · `chess` (ex `python-chess`) · `anthropic` · `pydantic` v2 · `pyyaml` · `platformdirs` · `psutil` · `rich` · `torch` + `maia2` · `sqlite3` (libreria standard) · `argparse` (libreria standard) · `pytest`. Gestione del progetto con `pyproject.toml` (backend `hatchling`), punto d'ingresso `chessanalyst = "chessanalyst.cli:main"`, extra `dev` con `pytest`. Ambiente virtuale `.venv`. Le versioni delle dipendenze si fissano in M0 (`pip freeze > requirements.lock`). Interfaccia: CLI in M0–M5; UI locale in M6. Multipiattaforma (D-22): solo `pathlib`, nessun comando di shell, `subprocess` solo per Stockfish tramite `python-chess`.

### 11.2 Struttura del repository

```
chessanalyst/
  CLAUDE.md                       # Appendice A
  pyproject.toml  requirements.lock
  config/                         # Appendice D: default.yaml exploration.yaml thresholds.yaml wording.yaml
                                  # elo_conversion.yaml maia2_limits.yaml section_titles.yaml
                                  # section_budget.yaml tables.yaml verify.yaml  (local.yaml generato, non versionato)
  data/                           # openings_index.json (generato), aperture scaricate (non versionati)
  examples/
    example.fen
    golden/raw/                   # najdorf_w_1500.md najdorf_w_1900.md najdorf_w_2400.md calibration_levels.md
    golden/packs/                 # M1b: pacchetti congelati
    golden/fewshot/               # M1b: *.json, *.meta.yaml, _terms.txt, _s07_alt.json
    golden/rendered/              # M1b: generati
  fixtures/                       # positions/*.fen, pgn/*.pgn, recorded/{engine,maia,llm}/*.json,
                                  # golden_nodes.json, golden_maia.json, checklists/
  docs/                           # questa documentazione, OPEN_QUESTIONS.md, MAIA2_NOTES.md,
                                  # golden_diff.md, CALIBRATION_GUIDE.md
  scripts/setup_engines.py
  src/chessanalyst/
    cli.py  config.py  profile.py  errors.py  exit_codes.py
    inputs/      read_source.py  detect.py  fen.py  pgn.py  example.py  confirm.py
    engines/     stockfish.py  maia2.py  syzygy.py  openings.py  cache.py  fake.py
    explore/     plan.py  runner.py  tree.py  select.py  pvwalk.py  context.py
    features/    material.py  pawns.py  king.py  activity.py  tactics.py  see.py  profile.py
    scoring/     classify.py  recommend.py  categories.py  filter.py  radar.py     # gli ultimi tre da M3
    pack/        builder.py  schema.py  section_plan.py  tables.py  ids.py  llm_view.py
    llm/         prompt.py  client.py  fewshot.py  schema.py  legend.py
    verify/      tokens.py  resolve.py  scan.py  assertions.py  plan_check.py  structure.py
                 theory.py  contamination.py  wordcount.py  report.py
    render/      markdown.py  tables.py  format_it.py  header.py
    golden/      data.py  packs.py  render.py
  tests/                          # specchio di src/, più tests/acceptance/ con un file per AC
```

### 11.3 Setup e `doctor`

`scripts/setup_engines.py` (idempotente): scarica Stockfish (versione del pin), scarica i pesi di Maia-2 chiamando `from_pretrained` una volta, scarica le tablebase 3-4-5 e i file delle aperture, costruisce `data/openings_index.json`, scrive i percorsi in `config/local.yaml`. Ogni download mostra la dimensione prevista e chiede conferma (salvo `--yes`).

`chessanalyst doctor` stampa una riga per controllo con `OK` / `AVVISO` / `ERRORE` e la correzione suggerita in italiano: sistema operativo; Python; PyTorch e dispositivo (CPU/CUDA); Stockfish (percorso, versione, confronto con il pin, `Threads`/`Hash` che userebbe); Maia-2 (versione del pacchetto, modello caricato, tabella fasce Elo letta, test di una chiamata); tabella `elo_declared → elo_maia → bucket → saturated` per le ancore; Syzygy (pezzi disponibili); indice delle aperture (numero di voci); `ANTHROPIC_API_KEY` presente (mai stampata); permessi di scrittura su output, cache e configurazione; benchmark con stima dei tempi per profilo. Codice di uscita 0 se non ci sono `ERRORE`, altrimenti 4.

### 11.4 Configurazione

Il contenuto iniziale di tutti i file di `config/` è nell'Appendice D. `config.py` carica i file con `yaml.safe_load`, li valida con modelli `pydantic` (chiavi sconosciute = errore) e applica la precedenza di §2-bis.1. `config_hash` = sha1 della serializzazione canonica di `exploration.yaml`, `thresholds.yaml`, `maia2_limits.yaml`, `elo_conversion.yaml`.

### 11.5 Riservatezza

Alla API vengono inviati solo la vista ridotta del pacchetto (FEN, linee, punteggi, Elo), il prompt e l'esempio. Il PGN, i nomi dei giocatori, i tag e i percorsi dei file non fanno parte del pacchetto. La chiave API si legge solo da `ANTHROPIC_API_KEY` e non è mai scritta su disco né nei log (D-18).

---

## 12. Test e metriche di qualità

### 12.1 Fixture e test senza motori né rete

- `FakeEngine` (`engines/fake.py`) risponde da `fixtures/recorded/engine/*.json` indicizzati per chiave di cache; `FakeUCI` è un piccolo processo Python che parla UCI e rigioca righe registrate (per AC-29); `FakeMaia` legge `fixtures/recorded/maia/*.json`; `FakeLLM` restituisce JSON registrati, anche difettosi (fault injection).
- Le fixture registrate si producono con `pytest -m engines --record` (motori veri) e si versionano. La suite predefinita (`pytest`) non le rigenera mai.
- Elenco delle fixture: Appendice G.

### 12.2 Metriche

- **Automatiche:** legalità 100%; token risolti 100%; nessun numero «libero» 100%; presenza della migliore di Stockfish tra le `explained`; tasso di retry; tempo per profilo.
- **Umane:** utilità percepita per fascia, correttezza concettuale, assenza di banalità ai livelli alti, validazione degli esempi (§8-bis.5).
- **Regressione:** ogni modifica a prompt o schema si rilancia sulle fixture e si confrontano i rapporti.

### 12.3 Criteri di accettazione

| ID | Verifica | Milestone |
| --- | --- | --- |
| AC-01 | Con la posizione d'esempio, `FakeEngine`, `FakeMaia` e `FakeLLM` (`good_najdorf_1900.json`, valida contro il pacchetto congelato), `analyze --yes --elo 1900 --budget deep` produce `analysis.md`, `pack.json`, `llm_raw.json`, `verification.json`, `run.log` e termina con codice 0 | M1c |
| AC-02 | Le 12 FEN non valide dell'Appendice G producono il messaggio atteso; nessun ritorno all'esempio; nel flusso interattivo uscita con codice 3 dopo `max_attempts` | M1a |
| AC-03 | I casi PGN dell'Appendice G: testo incollato e file, BOM, più partite (`--game`), `[SetUp]`/`[FEN]`, commenti e varianti, mossa illegale (indice e testo), posizione terminale, `--at`/`--ply` (validi e fuori intervallo), riconoscimento FEN/PGN, contraddizione col metodo | M1a |
| AC-04 | Tutti i token dell'output sono validi e risolti (V02 su risposte registrate valide e difettose) | M1b |
| AC-05 | V03: tutte le stringhe della tabella dell'Appendice G.4 hanno l'esito atteso | M1b |
| AC-06 | Le sezioni del documento coincidono con il SectionPlan; omissioni e fusioni registrate con motivo | M1b |
| AC-07 | V07(d) calcola correttamente le parole (casi dell'Appendice G.5) e segnala gli sforamenti; i tre fewshot rispettano tutti i budget | M1b |
| AC-08 | Nessuna linea supera `max_pv_plies` (V05 su risposte difettose) | M1b |
| AC-09 | Najdorf: l'eval radice delle prime 3 candidate dei raw differisce ≤ 0,25 pedoni e quelle 3 mosse sono tra le prime 6 della nuova esecuzione | M0 |
| AC-10 | Najdorf: per le ancore 1500 e 1900 il documento contiene le sezioni attese dopo matrice, milestone e §8.2-bis, con i titoli di `section_titles.yaml` nell'ordine di §8.1; S08 secondo c8 (sempre all'ancora 1500); sezioni assorbite e omesse registrate. Verificato sui `rendered` (M1b) e su una risposta registrata del modello reale (M1c); per 2400 in M2 | M1b, M1c (1500, 1900); M2 (2400) |
| AC-11 | Il numero di candidate `explained` è tra `explained_min` e `K` della fascia; con avversario al tratto il numero di `R<n>` è ≤ `K` | M1a |
| AC-12 | Calibrazione: stessa posizione a 1200 / 1900 / 2500 → output che differiscono per almeno due di: insieme di sezioni, candidate spiegate, lunghezza massima delle linee, parole (≥ 25%) | M4 |
| AC-13 | Contaminazione: su ≥ 2 fixture non-Najdorf nessun termine di `_terms.txt` compare nell'output | M2 |
| AC-14 | Cache: seconda esecuzione identica senza chiamate ai motori e con lo stesso `pack.json` (salvo `created_utc`); un nodo con `MultiPV` e profondità ≥ richiesti è riusato; un risultato meno profondo non sostituisce uno più profondo | M1a |
| AC-15 | `rerun` rigenera analisi e verifica dallo stesso `pack.json` senza motori; i file precedenti diventano `*.prev.*` | M1c |
| AC-16 | Fault injection (Appendice G.6): ogni risposta difettosa produce gli errori attesi (M1b) e, nel ciclo completo, retry e poi correzione o marcatura/rimozione registrata (M1c); mai un errore non segnalato | M1b, M1c |
| AC-17 | Finale con tablebase: S12 con esito esatto, nessuna valutazione numerica nel testo | M2 |
| AC-18 | Elo nella fascia satura (fixture a 2400 e l'ancora 1900 con il limite 2000): `maia.confidence = low`, `p_up = null`, nessuna `improbable_error`; il documento contiene la frase fissa all'inizio di S06 e di S08 (dove presenti) e la nota sotto T1 | M1a (pacchetto), M1b (documento) |
| AC-19 | `doctor` segnala motore mancante, versione diversa dal pin, chiave API assente, dispositivo, e stampa la tabella `elo_maia`/`saturated` per ancora | M0 |
| AC-20 | Modalità *entrambi*: Stockfish chiamato una sola volta per nodo, due analisi nello stesso file | M4 |
| AC-21 | Avversario al tratto (fixture: Najdorf dopo `6.Be3`, utente Bianco): `replies` con ID `R<n>` e `R<n>.u<k>` secondo §2-bis.6, nessuna raccomandazione, S03 e S08 omesse con motivo, E2b ed E3 in `omitted_phases` (E2 sostituita dalla fase R), S07 col titolo alternativo e T1 alternativa | M1a (pacchetto), M1b (documento), M1c (modello) |
| AC-22 | Opzioni non disponibili (`--color both`, `--detail` ≠ 4, `--elo-white`, `--elo-black`, `--elo-scale chesscom` con tabella vuota) → messaggio esplicito e codice 2 | M1a |
| AC-23 | Token `plan`: sequenza valida resa come in §9-bis.3; mossa illegale, scacco non finale, lato sotto scacco, oltre `plan_max_moves` → V04; `plan` in un paragrafo `engine` → V10 | M1b |
| AC-24 | `rec_score` e `complexity` con i numeri di §4.3 (5,4; −11,4; −19,6), parità entro 5 punti, caso senza candidabili | M1a |
| AC-25 | `matrix_column()` e definizioni di `tactical`, `quiet`, `hanging_piece`, `unresolved_capture` sulle posizioni dell'Appendice G.1, più le feature di §5.1 verificate sulla Najdorf (radice e dopo `6.Be3 e5 7.Nb3`) | M1a |
| AC-26 | SectionPlan per le ancore 1500, 1900, 2400 (utente Bianco e Nero): `absorbed_into`, `omitted`, titoli con `{opp}`, `tables`, `must_cover`, `word_budget` come da §8.2-bis, §8.4, §8.5 | M1a |
| AC-27 | Ogni `fewshot/*.json` supera V01–V10 contro il proprio pacchetto congelato e `golden --render` produce `rendered/*.md` identici a quelli versionati | M1b |
| AC-28 | Formati numerici: tutti gli esempi di §9-bis.7; bande di valutazione sui confini ±14, ±15, ±49, ±50, ±99, ±100, ±199, ±200 cp (senza buchi né sovrapposizioni) e matto | M1b |
| AC-29 | Primitiva di §3.1.3 con `FakeUCI`: arresto per tempo e profondità, tetto con `unstable_depth`, righe `lowerbound`/`upperbound` ignorate, istantanea coerente su iterazione completa | M0 |
| AC-30 | Conversione Elo, fasce e ancore: valori di §3-bis e confini (1199/1200, 1599/1600, 1749/1750, 2149/2150, 2399/2400) | M1a |
| AC-31 | Selezione delle candidate (§3-ter.3): `mt` dentro le prime `K` per `pre`; `mt` fuori dalle prime `K` ma entro `L_max`; `mt` oltre `L_max`; `mt` senza valutazione; riempimento fino a `explained_min`; una mossa naturale ma settima per valutazione che entra a fascia `1200_1600` (`A` = 0,5) e **non** entra a fascia `ge2400` (`A` = 0); parità su `pre`; assegnazione degli ID `C<n>` per valutazione | M1a |
| AC-32 | Mossa di contesto (§3-ter.6) su nodi sintetici e, in M2, sui nodi di `fixtures/golden_nodes.json` (quelli di ℓ2 che riproducono le righe del raw 1900): sceglie `...Nc6` con `spread` ≈ 50; soglia di 30 cp rispettata. Nota: la pipeline sceglie le candidate per `pre`, quindi i sistemi confrontati in T3 possono essere diversi da quelli dei raw | M1a (sintetico), M2 (registrato) |
| AC-33 | Pianificazione: tetto di nodi e scadenza scartano nell'ordine di §3-ter.2; E2b riusa i nodi di E3-ℓ1; `complexity_partial` impostato quando servono | M1a |
| AC-34 | Codici di uscita e precedenza della configurazione (§2-bis.1) | M1a |
| AC-35 | Vista ridotta del pacchetto (§6.1): nessun nodo `citable: false`, nessuna tabella, al massimo 5 righe per nodo | M1c |

---

## 13. Roadmap (milestone)

Ogni milestone inizia solo quando la precedente ha superato i suoi criteri. «M1» indica l'insieme M1a + M1b + M1c (D-50).

| Milestone | Contenuto | Criteri di uscita |
| --- | --- | --- |
| **M0 Fondamenta e dati** | Struttura del repository, `pyproject.toml`, caricamento e validazione della configurazione (Appendice D), `setup_engines.py`, `doctor`, adattatori `StockfishEngine` (con la primitiva di §3.1.3) e `MaiaEngine`, cache SQLite, `FakeEngine`/`FakeUCI`/`FakeMaia`, indice delle aperture, copia dei raw in `examples/golden/raw/`, `golden --data`, `docs/MAIA2_NOTES.md`, `config/maia2_limits.yaml` reale, `docs/CALIBRATION_GUIDE.md`, benchmark, `version_pin` | AC-09, AC-19, AC-29; checklist dell'Appendice B completa |
| **M1a Pacchetto** | Ingresso (esempio/FEN/PGN, conferma, codici di uscita), rifiuto delle opzioni non disponibili, conversione Elo, esplorazione E0–E4 con E2b ed E2c (E3 solo ℓ1), selezione, feature «M1», profilo e `matrix_column`, classificazione, `complexity` e raccomandazione, mossa di contesto, modalità avversario, ID canonici, tabelle, SectionPlan, `pack.json`. **Nessuna chiamata al modello** | AC-02, 03, 11, 14, 18 (pacchetto), 21 (pacchetto), 22, 24, 25, 26, 30, 31, 32 (sintetico), 33, 34 |
| **M1b Verifica, render e golden** | Risoluzione dei token, V01–V11, modalità degradata, render Markdown (testata, tabelle, frasi fisse, rapporto, formati), `golden --packs`, scrittura dei tre fewshot e di `_s07_alt.json`, `_terms.txt`, `golden --render`, misura delle parole e aggiornamento dei valori di §0.5, consegna dei `rendered` per la revisione umana | AC-04, 05, 06, 07, 08, 10 (1500, 1900 sui rendered), 16 (verifica), 18 (documento), 21 (documento), 23, 27, 28 |
| **M1c Modello** | Client Anthropic, prompt (Appendice E), schema dello strumento (Appendice F), legenda dei token, vista ridotta, retry di verifica e di rete, `rerun` | AC-01, 10 (risposta registrata), 15, 16 (ciclo completo), 21 (modello), 35 |
| **M2 Completezza delle posizioni** | E3 ℓ2–ℓ3, Syzygy (Stockfish e sonda), aperture per sequenza, matrice completa, S12 e S13, pacchetti e fewshot 1900/2400 completati, 2 fixture non-Najdorf con checklist | AC-10 (2400), 13, 17, 32 (registrato) |
| **M3 Category Scoring Engine** | §5-bis completo, feature «M3», radar S02, S09, confidenza | Ogni `T`/`R` tracciabile a feature o linee; test unitari delle formule |
| **M4 Calibrazione e modalità** | Dettaglio 1–5, S11, modalità *entrambi*, Elo dai tag PGN, critico opzionale | AC-12, AC-20 |
| **M5 Calibrazione dei numeri** | 50–100 posizioni annotate; calibrazione di `k_c`, `w_c`, `θ`, `A`, `B`, `L_max` su partite del database aperto Lichess; regressione del prompt | Relazione di calibrazione; soglie aggiornate |
| **M6 UI e v1.0** | UI con scacchiera, varianti cliccabili, esportazione; ottimizzazione dei costi | Rilascio v1.0 |

---

## 14. Rischi

- **Allucinazione di varianti e numeri:** mitigata da token, schema e verifica (§9-bis, §10).
- **Contenuto `theory` non verificabile:** rischio residuo accettato e dichiarato; limitato da tetto, divieto di cifre, marcatura †; la revisione umana degli esempi lo riduce.
- **Maia-2 sopra ~2000:** una sola fascia alta, meno differenziazione; confidenza bassa e segnalata (D-06). Con la conversione segnaposto anche l'ancora 1900 (→ 2025) ricade in questa fascia se il limite è 2000 (D-24): è previsto, dichiarato negli esempi e non richiede modifiche al codice.
- **Costo di E2b:** una fase in più (fino a una decina di nodi a `MultiPV` 2 per candidata); mitigata da profondità minima ridotta, riuso della cache (D-36) e tetto di nodi con ordine di scarto definito (§3-ter.2).
- **Raccomandazione sensibile a `complexity`:** pochi punti di `B` cambiano la mossa raccomandata (esempio in §4.3); mitigata da AC-24, dal tie-break e dalla marcatura «debole» con `no_unique_best`.
- **Interfaccia di Maia-2 diversa da quella attesa:** isolata nell'adattatore; verifica in M0.
- **Conversione Elo imprecisa:** visibile in testata; segnaposto da sostituire con fonte (O-1).
- **Esempi tutti Najdorf:** rischio di trascinamento; V09, esempio singolo per chiamata, espansione in §8-bis.6.
- **Posizioni quiete senza mossa «giusta»:** il sistema lo sa dire (`no_unique_best`).
- **Instabilità dei motori:** profondità minima, registro dei parametri, `unstable_depth`.
- **Costo/latenza:** profilo `fast` per iterare, `deep` per la qualità massima; pacchetto salvato per ripetere solo l'LLM.
- **Installazione pesante (PyTorch, pesi):** `doctor` e `setup_engines.py`; CPU sufficiente.
- **Quota `theory` e scrittura dei fewshot:** gli esempi a 1500 sono quasi solo principi; la quota per ancora (D-48) e la misura in M1b evitano che V08 blocchi l'esempio stesso. Scrivere tre fewshot che passano la verifica è lavoro reale di M1b: è pianificato, non è un effetto collaterale.
- **Non determinismo di Stockfish con più thread:** risultati diversi tra esecuzioni; la riproducibilità viene da cache e fixture (D-60), i pacchetti golden sono congelati (D-49).
- **Schema dello strumento rifiutato dall'API** (`$defs`, `oneOf`): il generatore espande i riferimenti in linea senza cambiare semantica (Appendice F).
- **Primitiva di analisi dipendente dall'API di `python-chess`:** isolata in `engines/stockfish.py`, verificata in M0 (AC-29).

---

## 15. Questioni aperte e stato delle precedenti

### 15.1 Stato delle questioni della v0.7

| Q | Tema | Stato |
| --- | --- | --- |
| 1 | Interfaccia MVP | Deciso: CLI |
| 2 | Lingua dell'output | Deciso: solo italiano (D-15) |
| 3 | Scala Elo | Deciso: interna Lichess, input in scala dichiarata (D-05); tabella segnaposto → O-1 |
| 4 | Profondità vs velocità | Deciso: profili con profondità minima e tetto di tempo (D-20) |
| 5 | Maia-2 o Maia-1 | Deciso: Maia-2 (D-03) |
| 6 | Punto di vista dei punteggi | Deciso: utente (D-07) |
| 7 | Calibrazione delle costanti | Rimandata a M5 (D-21) |
| 8 | FEN di esempio | Deciso: Najdorf |
| 9 | Elo nella modalità *entrambi* | Deciso: distinti per colore (D-16) |
| 10 | «PNG» o PGN | Chiarito: era la notazione PGN delle mosse; l'ingresso da immagine non è previsto (D-01, D-02) |
| 11 | Altre posizioni per gli esempi | Piano in §8-bis.6 |

### 15.2 Questioni residue (con default)

| ID | Questione | Default finché non risolta |
| --- | --- | --- |
| O-1 | Fonte documentata per la conversione FIDE→Lichess | Tabella segnaposto di §3-bis, mostrata in testata |
| O-2 | Limiti esatti di Maia-2 (fasce Elo, API, lato di `win_prob`) | Regola D-24; adattatore; M0 scrive `config/maia2_limits.yaml` e `docs/MAIA2_NOTES.md` |
| O-3 | Sistema operativo e hardware dell'utente (GPU?) | CPU, multipiattaforma; `doctor` misura e stima |
| O-4 | Quali posizioni aggiungere agli esempi e chi le valida | Elenco di §8-bis.6; validazione umana per livello |
| O-5 | Mostrare la `T` dell'avversario di default | No (solo dettaglio 5) |
| O-6 | Output multilingua e notazione italiana delle mosse (C, A, T, D) | Fuori v1: SAN inglese in testo italiano (D-14) |
| O-7 | Modello usato dal «critico» | Lo stesso della chiamata principale |
| O-8 | Fonte di download delle tablebase Syzygy | Scelta in M0 tra i mirror pubblici noti, annotata in `setup_engines.py` |
| O-9 | Nomi delle aperture in italiano | Nome della fonte (inglese) tramite `{{opening:name}}`; una tabella di traduzione è fuori v1 |

---

## Appendice A. `CLAUDE.md` per il repository

```
# Chess Position Analyst — regole per Claude Code
- Fonte di verità: docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md. La v0.9.1 è CONGELATA:
  il registro decisioni (§0.3, D-01…D-63) prevale e non si riapre; tra due decisioni vale l'ID più alto.
- Le Appendici D–G sono normative: i file di config/ partono esattamente da quei contenuti.
- Lavora per milestone nell'ordine M0, M1a, M1b, M1c, M2… (§13). Non implementare funzioni di milestone
  successive. Opzioni non ancora disponibili: rifiuto esplicito, codice di uscita 2 (D-30).
- Non inventare versioni/API: verifica Stockfish, python-chess, Maia-2, Anthropic dalle fonti ufficiali.
  Maia-2 si importa solo in engines/maia2.py; Stockfish solo in engines/stockfish.py.
- Nessuna costante numerica nel codice: tutto in config/*.yaml (§0.5 dice chi può cambiare che cosa).
- Il LLM non scrive mai numeri o mosse in chiaro: token di §9-bis. Tabelle, titoli, testata, frasi fisse
  e rapporto li scrive il render.
- Testi per l'utente in italiano; codice, commenti, chiavi in inglese; multipiattaforma (pathlib, niente
  shell); nomi di file solo ASCII (D-34).
- Test senza motori né rete (fixture registrate, Appendice G). Ogni bug di verifica diventa un test di
  fault injection. Un file di test per ogni criterio AC in tests/acceptance/.
- Se una premessa del documento è falsa e non è tra i parametri di §0.5: FERMATI, scrivi problema, prova
  e proposta in docs/OPEN_QUESTIONS.md e chiedi all'utente.
- Dubbi minori: default di §15.2, annotati in docs/OPEN_QUESTIONS.md.
- Mai salvare o stampare la chiave API; mai inviare PGN, nomi o percorsi all'API.
```

## Appendice B. Checklist della Fase M0

1. Repository, `pyproject.toml`, `config/` con i contenuti dell'Appendice D, caricamento e validazione della configurazione.
2. `scripts/setup_engines.py` e `chessanalyst doctor` verdi su Stockfish, Maia-2, Syzygy 3-4-5, indice delle aperture, chiave API.
3. `docs/MAIA2_NOTES.md`: funzioni di inferenza usate (singola e a lotti), tipo di modello, fasce Elo lette dal codice, lato a cui si riferisce `win_prob`, comportamento oltre il limite alto, i test di §3.2, tempo per posizione su CPU/GPU.
4. `config/maia2_limits.yaml` con i valori reali e tabella `elo_maia` / `bucket` / `saturated` per le ancore 1500, 1900, 2400. **Nessuna decisione da prendere**: la regola è D-24.
5. Primitiva di §3.1.3 con `FakeUCI` (AC-29); verifica dell'API reale di `engine.analysis()` e annotazione delle differenze nel codice dell'adattatore.
6. Copia dei quattro raw (v0.9.1) in `examples/golden/raw/`.
7. `chessanalyst golden --data` (§8-bis.4): `fixtures/golden_nodes.json`, `fixtures/golden_maia.json`, `docs/golden_diff.md`.
8. AC-09; se fallisce, aumentare le profondità minime di `deep` (§0.5) e annotare la causa.
9. Misura dei tempi; aggiornamento di `exploration.yaml` (`B`, profondità, nodi, `reference_time_s`).
10. `version_pin` di Stockfish e Maia-2; `requirements.lock`.
11. `docs/CALIBRATION_GUIDE.md` da `calibration_levels.md`.
12. `docs/OPEN_QUESTIONS.md` creato (anche vuoto).

## Appendice C. Glossario

| Termine | Significato |
| --- | --- |
| Nodo | Posizione analizzata (FEN) con i risultati dei motori; ID `N<n>` |
| Candidata | Mossa dell'utente considerata e valutata; ID `C<n>` |
| PV | Variante principale di Stockfish da un nodo; ID `PV<n>` |
| Token | Segnaposto `{{…}}` nel testo del LLM, sostituito dal codice con un dato del pacchetto |
| Asserzione | Dichiarazione tipizzata (feature, banda di eval, ecc.) verificata contro il pacchetto |
| `theory` | Contenuto discorsivo non derivato dal motore, senza cifre, marcato † |
| SectionPlan | Elenco deterministico di sezioni, ordine e budget che il LLM deve rispettare |
| Saturazione | Elo nella fascia più alta di Maia-2: poca differenziazione, confidenza bassa |
| `human_expected_score` | Risultato atteso stimato da Maia-2 a quell'Elo; non è una valutazione oggettiva |
| Ancora | Esempio di riferimento (1500, 1900, 2400) scelto come few-shot |
| Risposta (`R<n>`) | Mossa dell'avversario considerata quando tocca a lui (D-31); `R<n>.u<k>` sono le migliori risposte dell'utente |
| `plan` | Token che nomina una sequenza di idee di un lato, validata come realizzabile ma non valutata (§9-bis.3) |
| E2b | Fase che analizza i nodi «tocca all'utente» lungo la PV per calcolare `complexity` (D-29) |
| ℓ1, ℓ2, ℓ3 | Livelli dei test di move order (E3), D-28 |
| `elo_ref_fide` | Elo dichiarato riportato in scala FIDE: decide fascia e ancora (D-38) |
| Fascia | Intervallo di `elo_ref_fide` che decide i parametri numerici (§7.1) |
| E2c | Ricerche brevi che completano i valori della mossa di contesto nei nodi di T3 (§3-ter.6) |
| Mossa di contesto | Mossa dell'avversario il cui costo cambia di più tra i sistemi dell'utente (T3) |
| `must_cover` | ID che una sezione deve citare con almeno un token (§8.4) |
| Vista ridotta | Parte del pacchetto inviata al modello (§6.1) |
| Pacchetto golden | Pacchetto congelato nel repository su cui sono scritti i fewshot (D-49) |

## Appendice D. Contenuto iniziale dei file di configurazione

I percorsi relativi sono risolti rispetto alla cartella del progetto (quella che contiene `config/`). Le chiavi sconosciute sono un errore di caricamento. **Regola YAML:** ogni chiave che inizia con una cifra o contiene un underscore tra cifre (`"1200_1600"`, `"1500"`, `"1"`) va scritta tra virgolette: PyYAML legge `1200_1600` come l'intero 12001600. Il caricatore rifiuta qualunque chiave non stringa (AC-34).

### D.1 `config/default.yaml`

```yaml
user:
  color: white            # white | black | both (both da M4)  (D-53)
  elo: 1900
  elo_scale: fide         # fide | lichess | chesscom (chesscom quando configurata)
  opp_elo: null           # null = uguale a elo
  elo_white: null         # solo color: both (M4)
  elo_black: null
  detail_level: 4         # M1-M3: solo 4 (D-30)
  language: it
input:
  method: null            # null = chiede | example | fen | pgn
  example_fen_file: examples/example.fen
  pgn_default_position: end
  max_attempts: 3
  confirm: true
engines:
  stockfish: {path: null, version_pin: null, hash_mb: 4096, poll_s: 0.05}
  maia2: {model_type: rapid, device: auto, version_pin: null, up_delta: 300}
  syzygy: {path: null, max_pieces: 5}
  openings: {index_file: data/openings_index.json}
exploration:
  profile: standard       # fast | standard | deep
llm:
  model: claude-sonnet-5-5
  max_tokens: 16000
  temperature: 0.3
  max_retries: 2
  network_attempts: 3
  network_backoff_s: [2, 4, 8]
  on_fail: mark           # mark | drop
  critic: false           # da M4
  plan_max_moves: 6
render:
  mark_theory: footnote
output:
  dir: output
```

### D.2 `config/exploration.yaml`

```yaml
reference_time_s: null          # scritto da M0 (benchmark di doctor)
phase_shares: {E0: 0.30, E4: 0.10, E1: 0.08, E2: 0.26, E3: 0.20, E2b: 0.06}
e2c_time_factor: 0.5            # t_target di E2c rispetto a E3
e4_min_p: 0.03
profiles:
  fast:
    B_s: 60
    dmin: {root: 16, nodes: 14, pvwalk: 12}
    node_cap_factor: 2.0
    deadline_factor: 2.0
    multipv: {root: 8, nodes: 5, pvwalk: 2}
    e3_levels: 1
    e3_M: 1
    e3_R: 2
    e4_max_moves: 4
    max_nodes: 16
  standard:
    B_s: 300
    dmin: {root: 18, nodes: 16, pvwalk: 14}
    node_cap_factor: 2.0
    deadline_factor: 2.0
    multipv: {root: 12, nodes: 8, pvwalk: 2}
    e3_levels: 2
    e3_M: 2
    e3_R: 3
    e4_max_moves: 6
    max_nodes: 40
  deep:
    B_s: 900
    dmin: {root: 20, nodes: 18, pvwalk: 14}
    node_cap_factor: 1.5
    deadline_factor: 1.5
    multipv: {root: 16, nodes: 8, pvwalk: 2}
    e3_levels: 3
    e3_M: 3
    e3_R: 3
    e4_max_moves: 6
    max_nodes: 80
milestone_max_e3_level: 1       # M1: 1; da M2: 3
```

### D.3 `config/thresholds.yaml`

```yaml
elo_input: {min: 400, max: 3000}
bands:                          # [lo, hi) su elo_ref_fide; chiavi SEMPRE tra virgolette
  "lt1200":    {lo: null, hi: 1200}
  "1200_1600": {lo: 1200, hi: 1600}
  "1600_2000": {lo: 1600, hi: 2000}
  "2000_2400": {lo: 2000, hi: 2400}
  "ge2400":    {lo: 2400, hi: null}
anchors:                        # [lo, hi) su elo_ref_fide
  "1500": {lo: null, hi: 1750}
  "1900": {lo: 1750, hi: 2150}
  "2400": {lo: 2150, hi: null}
band_params:
  "lt1200":    {plies_max: 3,  explained_min: 1, K: 2, listed_max: 3,  L_max: 40, prose_words: 450,  A: 0.6, B: 1.2}
  "1200_1600": {plies_max: 4,  explained_min: 2, K: 3, listed_max: 4,  L_max: 40, prose_words: 650,  A: 0.5, B: 1.0}
  "1600_2000": {plies_max: 8,  explained_min: 3, K: 5, listed_max: 12, L_max: 35, prose_words: 1400, A: 0.3, B: 0.5}
  "2000_2400": {plies_max: 10, explained_min: 3, K: 4, listed_max: 12, L_max: 30, prose_words: 1100, A: 0.1, B: 0.2}
  "ge2400":    {plies_max: 12, explained_min: 4, K: 5, listed_max: 12, L_max: 25, prose_words: 800,  A: 0.0, B: 0.0}
detail:                         # usato da M4
  "1": {words: 0.35, plies_delta: -2}
  "2": {words: 0.6,  plies_delta: -1}
  "3": {words: 0.8,  plies_delta: 0}
  "4": {words: 1.0,  plies_delta: 0}
  "5": {words: 1.4,  plies_delta: 2}
classification:
  natural_trap:     {p_user_min: 0.20, loss_min: 80, loss_min_low_bands: 60, low_bands: ["lt1200", "1200_1600"]}
  hard_move:        {p_user_max: 0.05, loss_max: 10}
  solid:            {p_user_min: 0.15, loss_max: 25}
  practical_alt:    {loss_gt: 25, max_loss: 60, complexity_max: 1}
  improbable_error: {p_user_max: 0.05, loss_min: 80, p_up_min: 0.08}
selection:
  quiet_spread_cp: 25
  forced_gap_cp: 100
  rec_tie_points: 5
  replies_min_p: 0.05
  replies_best_sf: 2
  context_spread_cp: 30
  context_candidates: 3
profile:
  endgame_nonpawn_total_max: 24
  endgame_no_queens_max_minors_per_side: 2
  opening_fullmove_max: 15
  tactical: {gap_cp: 150, mate_plies: 8}
  closed_min_blocked_pairs: 3
  unresolved_capture_see_min: 3
elo_rules:
  e3_mandatory_from: 2150
  s11_from: 2000
theory_max_share: {"1500": 0.70, "1900": 0.50, "2400": 0.35}
```

### D.4 `config/elo_conversion.yaml`

```yaml
# PLACEHOLDER: ipotesi iniziale, da sostituire con una fonte documentata (O-1)
fide_to_lichess: [[1000, 1300], [1200, 1450], [1500, 1700], [1800, 1950], [2000, 2100], [2200, 2250], [2400, 2400], [2600, 2600]]
chesscom_to_lichess: []   # finché è vuota, --elo-scale chesscom è rifiutato
```

### D.5 `config/maia2_limits.yaml`

```yaml
# PLACEHOLDER scritto da M0 dopo la lettura del codice di maia2 (valori attesi)
elo_max_model: 3000            # clamp di sicurezza per elo_up
bucket_width: 100
first_bucket_upper: 1100       # fascia 0 = elo < 1100
top_bucket_lower: 2000         # fascia più alta = elo >= 2000
models: [rapid, blitz]
# bucket(elo) = 0 se elo < 1100; indice_massimo se elo >= 2000; altrimenti 1 + (elo - 1100) // 100
```

### D.6 `config/section_titles.yaml`

```yaml
S01: {"1500": "In una frase", "1900": "Sintesi", "2400": "Sintesi"}
S02: {"1500": "Radar semplificato", "1900": "Radar delle categorie", "2400": "Fattori decisivi"}
S03: {"1500": "Le tre cose da fare adesso", "1900": "I sistemi che puoi scegliere", "2400": "Piani per struttura"}
S04: {"1500": null, "1900": "Dove ti arrocchi", "2400": null}
S05: {"1500": "Cosa vuole ogni pezzo", "1900": "Cosa vuole ogni pezzo", "2400": null}
S06: {"1500": "Cosa fa {opp}", "1900": "Cosa cerca {opp}", "2400": "Cosa cerca {opp}"}
S07: {"1500": "Mosse candidate", "1900": "Mosse candidate", "2400": "Mosse candidate e test di move order"}
S07_alt: {"1500": "Risposte probabili di {opp} e come prepararsi", "1900": "Risposte probabili di {opp} e come prepararsi", "2400": "Risposte probabili di {opp} e come prepararsi"}
S08: {"1500": "Attenzione a questi errori tipici", "1900": "Trappole naturali e mosse difficili", "2400": "Imprecisioni sottili"}
S09: {"1500": "Minacce invisibili al tuo livello", "1900": "Minacce invisibili al tuo livello", "2400": "Minacce invisibili al tuo livello"}
S10: {"1500": "Prima di ogni mossa, controlla", "1900": "Come ragionare", "2400": null}
S11: {"1500": null, "1900": "Note da maestro", "2400": "Note da maestro"}
S12: {"1500": "Finale: tecnica e tablebase", "1900": "Finale: tecnica e tablebase", "2400": "Finale: tecnica e tablebase"}
S13: {"1500": "Tattica forzata", "1900": "Tattica forzata", "2400": "Tattica forzata"}
```

Un titolo `null` significa sezione assorbita (S04 all'ancora 1500 e 2400, in S03) oppure omessa (S05, S10 all'ancora 2400; S11 all'ancora 1500). Fino al dettaglio 5 (M4) le esclusioni non hanno eccezioni.

### D.7 `config/section_budget.yaml`

```yaml
# Pesi relativi; rinormalizzati sulle sezioni required (§8.4). Aggiornati in M1b (§0.5).
"1500": {S01: 0.08, S02: 0.06, S03: 0.25, S05: 0.15, S06: 0.10, S07: 0.10, S08: 0.14, S09: 0.06, S10: 0.12, S12: 0.25, S13: 0.25}
"1900": {S01: 0.07, S02: 0.05, S03: 0.13, S04: 0.10, S05: 0.16, S06: 0.24, S07: 0.13, S08: 0.07, S09: 0.06, S10: 0.08, S11: 0.08, S12: 0.25, S13: 0.25}
"2400": {S01: 0.15, S02: 0.06, S03: 0.30, S05: 0.12, S06: 0.22, S07: 0.20, S08: 0.10, S09: 0.06, S10: 0.08, S11: 0.10, S12: 0.25, S13: 0.25}
```

S04 assente nelle ancore 1500 e 2400 perché sempre assorbita; S05 e S10 a 2400 servono solo con dettaglio 5.

### D.8 `config/tables.yaml`

```yaml
T1:
  "1500": {data: [move, eval, p_user], text: [per_chi]}
  "1900": {data: [move, eval, p_user, line], text: [idea]}
  "2400": {data: [move, eval, p_user, line], text: [nota]}
T1_alt: {data: [reply, p_opp, eval, user_best], text: [prepare]}
T2: {anchors: ["2400"], detail5_anchors: ["1900"], moves_per_cell: 3, text: [nota]}
T3: {anchors: ["1900", "2400"], text: []}
T4: {data: [category, T, R], text: [nota]}
t1_line_plies: {"1900": 6, "2400": 8}
headers:
  move: "Mossa"
  eval: "Valutazione"
  p_user: "Scelta a {elo}"
  line: "Linea del motore"
  per_chi: "Per chi"
  idea: "Idea"
  nota: "Nota"
  reply: "Risposta"
  p_opp: "Probabilità a {opp_elo}"
  user_best: "La tua risposta migliore"
  prepare: "Come prepararsi"
  t2_after: "Dopo"
  t2_moves: "Mosse (dalla migliore)"
  t3_after: "Dopo…"
  t3_best: "Migliore di {opp}"
  t3_cost: "Costo"
  category: "Categoria"
  T: "T (tu)"
  R: "R"
empty_text_cell: "—"
recommended_marker: "★"
```

### D.9 `config/wording.yaml`

```yaml
v03_allowed_literals: ["Maia-2"]
eval_bands:                      # sul MODULO |e| in pedoni, [abs_lo, abs_hi); il segno sceglie _plus/_minus
  equal:    {abs_lo: 0.0, abs_hi: 0.15, text: "equilibrata"}
  slight:   {abs_lo: 0.15, abs_hi: 0.5, text_plus: "vantaggio minimo per te", text_minus: "svantaggio minimo"}
  small:    {abs_lo: 0.5, abs_hi: 1.0,  text_plus: "leggero vantaggio per te", text_minus: "leggero svantaggio"}
  clear:    {abs_lo: 1.0, abs_hi: 2.0,  text_plus: "vantaggio netto per te", text_minus: "svantaggio netto"}
  decisive: {abs_lo: 2.0, abs_hi: null, text_plus: "vantaggio decisivo per te", text_minus: "svantaggio decisivo"}
  mate:     {text_plus: "matto forzato a tuo favore", text_minus: "matto forzato contro di te"}
# ID di banda = chiave + "_plus" / "_minus" (es. slight_plus); `equal` non ha suffisso.
maia_bands:
  very_unlikely: {lo: 0.0,  hi: 0.03, text: "molto improbabile"}
  unlikely:      {lo: 0.03, hi: 0.10, text: "poco probabile"}
  possible:      {lo: 0.10, hi: 0.25, text: "possibile"}
  frequent:      {lo: 0.25, hi: 0.45, text: "frequente"}
  very_frequent: {lo: 0.45, hi: null, text: "molto frequente"}
categories:
  natural_trap: "trappola naturale"
  hard_move: "mossa difficile"
  solid: "mossa solida"
  practical_alt: "alternativa pratica"
  improbable_error: "errore improbabile"
p_up_group:
  higher: "giocatori di circa trecento punti più forti"     # da aggiornare se cambia up_delta
  top: "giocatori della fascia più forte del modello"
colors: {w: "il Bianco", b: "il Nero"}
fixed:
  maia_low_confidence: "A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore."
  maia_low_confidence_table: "* Probabilità di Maia-2 poco affidabili a questo livello."
  section_unavailable: "Questa sezione non è disponibile: il testo prodotto non ha superato i controlli."
  unverified_mark: "⚠ non verificato"
  theory_footnote: "† contenuto teorico, non verificato dai motori"
header:
  convention: "Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te)."
  references_not_validated: "Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore."
  profile_unsupported: "Profilo di posizione non ancora supportato: analisi limitata a sintesi, idee dell'avversario, mosse candidate e metodo."
  move_order_limited: "Test di move order limitati al primo livello: l'analisi completa a questo livello arriva in una versione successiva."
  maia_low_confidence_header: "Maia-2 è poco affidabile a questo livello (vedi le sezioni sull'avversario)."
  unstable_nodes: "Alcune analisi non hanno raggiunto la profondità minima: vedi il rapporto tecnico."
errors: {}                        # messaggi di §2-bis.3 e §2-bis.4, chiavi = nomi degli stati
verify_hints:
  V01: "Rispetta lo schema di submit_analysis; nel testo solo **grassetto** e *corsivo*."
  V02: "Usa solo token della grammatica con ID presenti nel pacchetto e valori non nulli."
  V03: "Niente mosse, cifre, catene di case o puntini in chiaro: usa {{m:SAN@N}}, {{plan:…}}, {{diag:…}}, numeri in lettere."
  V04: "La mossa o la sequenza non è legale nel nodo indicato."
  V05: "La linea supera max_pv_plies della sezione."
  V06: "L'asserzione non corrisponde al pacchetto."
  V07: "Scrivi esattamente le sezioni required nell'ordine, con le tabelle indicate, gli ID di must_cover e circa il budget di parole."
  V08: "Contenuto theory fuori posto, con token di dati o oltre la quota."
  V09: "Il termine appartiene a un'altra apertura: non usarlo."
  V10: "La fonte (source) non corrisponde ai token usati."
```

### D.10 `config/verify.yaml`

```yaml
v03:
  token: "\\{\\{[^{}]*\\}\\}"
  pass1:
    piece_move: "(?<![A-Za-z])[KQRBN][a-h]?[1-8]?x?[a-h][1-8]"
    pawn_capture: "(?<![A-Za-z])[a-h]x[a-h][1-8]"
    castling: "\\b[O0]-[O0]"
    promotion: "=[QRBN]"
    square_chain: "[a-h][1-8]\\s*[-–—→]\\s*[a-h][1-8]"
    dots: "(?:\\.\\.\\.|…)\\s*[a-hKQRBNO]"
    move_number: "(?<![a-h0-9])\\d+\\s*\\.(?!\\d)"
    cp: "\\bcp\\b"
    figurine: "[\\u2654-\\u265F]"
  square: "(?<![A-Za-z])[a-h][1-8](?![0-9])"
  digit: "\\d"
v01_markup: ["^\\s*#", "\\]\\(", "`", "<[A-Za-z/]"]
word: "[A-Za-zÀ-ÖØ-öø-ÿ0-9]+"
word_tolerance: {relative: 0.25, absolute: 15}
```

## Appendice E. Prompt

### E.1 System prompt (`llm/prompt.py: SYSTEM_PROMPT`, statico, in cache)

```
Sei l'autore delle analisi di Chess Position Analyst. Scrivi in italiano l'analisi di una posizione di scacchi
per un giocatore di un livello Elo dato. Non calcoli e non valuti nulla da solo: spieghi i dati prodotti da
Stockfish (verità oggettiva) e da Maia-2 (comportamento umano a un dato Elo), che trovi nel pacchetto di
evidenze. Consegni il risultato solo chiamando lo strumento submit_analysis.

DATI
- Il pacchetto (<pacchetto>) contiene posizione, profilo, candidate (C1, C2, …), varianti (PV1, …), nodi
  (N1, …), risposte dell'avversario (R1, …, solo quando tocca a lui), feature, raccomandazione e il piano delle
  sezioni (section_plan).
- I campi *_user_* sono dal punto di vista dell'utente: positivo = meglio per lui. p_user, p_up e p_opp sono
  probabilità di Maia-2; nei nodi c'è la policy di Maia-2 per chi muove.
- Se maia.confidence è "low", le probabilità umane sono poco affidabili: basati soprattutto sul motore e non
  costruire ragionamenti su piccole differenze di probabilità. La frase di avviso la inserisce il programma:
  non scriverla tu.

REGOLE INDEROGABILI
1. Scrivi esattamente le sezioni del section_plan con required=true, nell'ordine dato, vicino al word_budget
   (±25%). Non scrivere titoli di sezione: li inserisce il programma.
2. Ogni mossa, numero, valutazione, percentuale, variante, sequenza di piano ed Elo si scrive SOLO con i token.
   Nel testo libero: nessuna cifra (i conteggi in lettere: «tre sistemi»), nessuna mossa in notazione (Be3,
   exd5, O-O, ...b5), nessuna catena di case (g4-g5, a7-g1), nessun numero di mossa, nessuna percentuale.
   Ammessi: case isolate (d5), nomi dei pezzi in italiano, «arrocco corto/lungo», il nome Maia-2.
3. Usa solo ID presenti nel pacchetto. Non usare token che puntano a valori null (per esempio p_up quando è
   null, opening quando non c'è apertura).
4. Ogni blocco ha un source:
   - engine: fatti del motore; contiene almeno un token ev, loss, pv o pct:root.*; niente probabilità di
     Maia-2 e niente plan;
   - maia: probabilità umane; contiene almeno un pct di Maia-2; niente ev, loss, pv, plan;
   - feature: fatti strutturali; contiene almeno un'asserzione feature;
   - theory: conoscenza scacchistica generale; niente ev, loss, pct, pv; ammessi m, mv, plan, diag;
   - mixed: combinazione; almeno un token di dati o un'asserzione.
   Il token plan solo in theory o mixed.
5. Le affermazioni su fatti strutturali (pedone arretrato in d6, casa debole d5, avamposto, inchiodatura)
   vanno anche come assertions di tipo feature, con le chiavi del pacchetto.
6. Tieni distinte la valutazione del motore e la probabilità umana; non scrivere che una mossa è «buona»
   perché è frequente.
7. La mossa consigliata è recommendation.id: non sceglierne un'altra. Se recommendation.no_unique_best è vero,
   dì chiaramente che non esiste una mossa unica e proponi sistemi tra cui scegliere.
8. Rispetta fascia e ancora (istruzioni sotto): niente spiegazioni sotto o sopra il livello; nessuna linea più
   lunga di max_pv_plies.
9. Il contenuto theory solo nelle sezioni con theory_allowed=true. Se il pacchetto contiene il dato, usa il
   token, non la teoria.
10. L'esempio mostra forma, densità e tono: non copiarne contenuti, temi, mosse o nomi di aperture.
11. Inserisci ogni tabella elencata in tables della sezione con un blocco {"type": "table", "ref": "T…"}; puoi
    riempire solo le colonne di testo indicate nelle istruzioni. Ogni ID in must_cover deve comparire in
    almeno un token della sezione.
12. Non ricalcolare né correggere i dati. Se qualcosa ti sembra incoerente, scrivilo in notes.
13. Nel testo solo **grassetto** e *corsivo*: niente titoli, link, codice, tabelle in Markdown.

TOKEN (scrivili esattamente così, senza spazi dentro le graffe)
{{mv:C1}} mossa candidata numerata · {{mv:C1:bare}} senza numero · {{mv:R1}} {{mv:R1.u1}} in modalità avversario
{{m:Nb3@N4}} mossa legale nel nodo N4 (con «...» se muove il Nero) · {{m:Nb3@N4:num}} numerata
{{ev:C1}} {{ev:N4}} {{ev:Nc6@N4}} valutazione per l'utente · {{loss:C2}} {{loss:Nc6@N4}} perdita di chi muove
{{pct:C1.p_user}} {{pct:C1.p_up}} {{pct:R1.p_opp}} {{pct:R1.u1.p_user}} {{pct:Nc6@N4}} probabilità di Maia-2
{{pct:root.win}} {{pct:root.draw}} {{pct:root.loss}} esito secondo Stockfish
{{pv:PV1:6}} prime sei semimosse della variante · {{plan:w:f3,Qd2,O-O-O@N3}} piano di un lato, senza valutazione
{{diag:a7-g1}} diagonale o linea · {{elo:user}} {{elo:opp}} {{elo:user:full}} · {{opening:name}} {{opening:eco}}
{{txt:opp}} {{txt:me}} colore con articolo · {{txt:p_up_group}} chi sono i giocatori di p_up

CONTENUTO DELLE SEZIONI
S01 chi sta meglio e di quanto (parole + ev o pct:root.*), in una frase, poi due o tre frasi.
S03 raggruppa le candidate spiegate in sistemi o piani: idea, lato di arrocco, per chi è adatto. Quando S04 è
    assorbita, nomina il lato di arrocco di ogni sistema. All'ancora 1500 include la mossa consigliata e un
    piano semplice con plan.
S04 per sistema: lato di arrocco, corse di pedoni, diagonali critiche.
S05 per pezzo: obiettivo tipico e attenzione (spesso una text_table con colonne Pezzo, Obiettivo, Attenzione);
    in posizioni tattiche solo i pezzi delle focus_squares.
S06 le idee dell'avversario: mossa nulla (nodo null_move), risposte nei nodi dopo le candidate con ev e pct,
    la mossa di contesto della tabella T3 e il suo costo nei diversi sistemi.
S07 la tabella T1 (e T2 se indicata); per ogni candidata spiegata idea e rischio. In modalità avversario, per
    ogni risposta R come prepararsi, usando R.u1.
S08 le mosse classificate: trappole naturali, mosse difficili, alternative pratiche, errori improbabili.
    All'ancora 1500 anche gli errori tipici di principio (theory).
S10 un procedimento concreto in pochi passi (elenco numerato) per pensare in questa posizione.
S11 alternative sottili e preferenze tra linee quasi equivalenti. S12 esito, piano e tecnica del finale.
S13 la linea forzata, le difese e perché non si evita.

LIVELLO
- Fasce lt1200 e 1200_1600: frasi brevi, istruzioni dirette, idee prima del calcolo, linee corte.
- Fascia 1600_2000: tecnico; strutture pedonali, piani, perché funzionano.
- Fasce 2000_2400 e ge2400: sintetico e preciso; move order, sottigliezze; non spiegare l'ovvio.
```

### E.2 Messaggio utente (`llm/prompt.py: build_user_message`)

```
<esempio ancora="{anchor}">
Questo esempio riguarda un'altra posizione (o la stessa con dati diversi): imita struttura, densità e tono,
non il contenuto.
<legenda>
{una riga per token dell'esempio: "{{ev:C1}} → +0,37"}
</legenda>
<analisi>{fewshot JSON}</analisi>
{se modalità avversario: <analisi_s07_alternativa>{_s07_alt.json}</analisi_s07_alternativa>}
</esempio>

<pacchetto>
{vista ridotta del pacchetto, JSON compatto}
</pacchetto>

<istruzioni>
Modalità: {tocca a te | tocca all'avversario}. Fascia: {band}. Ancora: {anchor}. Giochi con {il Bianco|il Nero}.
Sezioni da scrivere, in ordine:
{per ogni sezione required: "- {id} «{title}»: circa {word_budget} parole; linee al massimo {max_pv_plies}
  semimosse; theory {ammessa|non ammessa}; tabelle {T…, con colonne di testo …}; deve citare {must_cover}"}
Quota massima di contenuto theory: {percentuale in lettere} delle parole.
Chiama submit_analysis con l'analisi completa.
</istruzioni>
```

### E.3 Messaggio di retry (`tool_result` con `is_error: true`)

```
La consegna contiene errori. Correggi solo questi punti e richiama submit_analysis con l'analisi completa.
{una riga per errore: "V03 · S06 · blocco 2 · «...Nc6» · Niente mosse … in chiaro: usa {{m:SAN@N}} …"}
```

## Appendice F. Schema dello strumento `submit_analysis`

Generato da `llm/schema.py` (`pydantic`); un test verifica che lo schema generato e questo testo accettino e rifiutino le stesse risposte (le fixture di G.6 e le risposte valide): non si confrontano i testi, perché `pydantic` produce `anyOf` dove qui c'è `oneOf`. Se l'API rifiuta `$defs`/`$ref`, il generatore li espande in linea (stessa semantica): non è un cambio di progetto.

```json
{
  "name": "submit_analysis",
  "description": "Consegna l'analisi strutturata della posizione.",
  "input_schema": {
    "type": "object",
    "additionalProperties": false,
    "required": ["schema_version", "sections", "notes"],
    "properties": {
      "schema_version": {"type": "string", "enum": ["1"]},
      "sections": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Section"}},
      "notes": {"type": "array", "items": {"type": "string"}}
    },
    "$defs": {
      "Source": {"type": "string", "enum": ["engine", "feature", "maia", "theory", "mixed"]},
      "Assertion": {
        "oneOf": [
          {"type": "object", "additionalProperties": false, "required": ["kind", "key", "side"],
           "properties": {"kind": {"const": "feature"}, "key": {"type": "string"},
                          "side": {"type": ["string", "null"], "enum": ["w", "b", null]},
                          "squares": {"type": "array", "items": {"type": "string", "pattern": "^[a-h][1-8]$"}}}},
          {"type": "object", "additionalProperties": false, "required": ["kind", "ref", "band"],
           "properties": {"kind": {"const": "eval_band"}, "ref": {"type": "string"}, "band": {"type": "string"}}},
          {"type": "object", "additionalProperties": false, "required": ["kind", "ref", "band"],
           "properties": {"kind": {"const": "maia_band"}, "ref": {"type": "string"}, "band": {"type": "string"}}},
          {"type": "object", "additionalProperties": false, "required": ["kind", "ref", "category"],
           "properties": {"kind": {"const": "classification"}, "ref": {"type": "string"},
                          "category": {"type": "string", "enum": ["natural_trap", "hard_move", "solid", "practical_alt", "improbable_error"]}}}
        ]
      },
      "ParagraphLite": {
        "type": "object", "additionalProperties": false, "required": ["text", "source"],
        "properties": {"text": {"type": "string", "minLength": 1}, "source": {"$ref": "#/$defs/Source"},
                       "assertions": {"type": "array", "items": {"$ref": "#/$defs/Assertion"}}}
      },
      "Paragraph": {
        "type": "object", "additionalProperties": false, "required": ["type", "text", "source"],
        "properties": {"type": {"const": "p"}, "text": {"type": "string", "minLength": 1},
                       "source": {"$ref": "#/$defs/Source"},
                       "assertions": {"type": "array", "items": {"$ref": "#/$defs/Assertion"}}}
      },
      "List": {
        "type": "object", "additionalProperties": false, "required": ["type", "items"],
        "properties": {"type": {"type": "string", "enum": ["ul", "ol"]},
                       "items": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/ParagraphLite"}}}
      },
      "Line": {
        "type": "object", "additionalProperties": false, "required": ["type", "pv", "plies"],
        "properties": {"type": {"const": "line"}, "pv": {"type": "string", "pattern": "^PV[1-9][0-9]*$"},
                       "plies": {"type": "integer", "minimum": 1}, "caption": {"$ref": "#/$defs/ParagraphLite"}}
      },
      "DataTable": {
        "type": "object", "additionalProperties": false, "required": ["type", "ref"],
        "properties": {"type": {"const": "table"}, "ref": {"type": "string", "enum": ["T1", "T2", "T3", "T4"]},
                       "text_cells": {"type": "object",
                                      "additionalProperties": {"type": "object",
                                                               "additionalProperties": {"$ref": "#/$defs/ParagraphLite"}}}}
      },
      "TextTable": {
        "type": "object", "additionalProperties": false, "required": ["type", "columns", "rows"],
        "properties": {"type": {"const": "text_table"},
                       "columns": {"type": "array", "minItems": 2, "maxItems": 6, "items": {"type": "string"}},
                       "rows": {"type": "array", "minItems": 1,
                                "items": {"type": "array", "items": {"$ref": "#/$defs/ParagraphLite"}}}}
      },
      "Block": {"oneOf": [{"$ref": "#/$defs/Paragraph"}, {"$ref": "#/$defs/List"}, {"$ref": "#/$defs/Line"},
                          {"$ref": "#/$defs/DataTable"}, {"$ref": "#/$defs/TextTable"}]},
      "Section": {
        "type": "object", "additionalProperties": false, "required": ["id", "blocks"],
        "properties": {"id": {"type": "string", "pattern": "^S(0[1-9]|1[0-3])$"},
                       "blocks": {"type": "array", "minItems": 1, "items": {"$ref": "#/$defs/Block"}}}
      }
    }
  }
}
```

Controlli che lo schema non esprime e che fa `pydantic` (V01): ogni riga di `TextTable.rows` ha tanti elementi quante `columns`.

## Appendice G. Fixture dei test

**Registrazioni dei motori.** `fixtures/recorded/engine` e `fixtures/recorded/maia` si producono in M1a con `pytest -m engines --record` sulla posizione d'esempio con profilo `deep` (E3 limitata a ℓ1), con il motore e Maia-2 veri, e coprono tutti i nodi che la pipeline richiede. `FakeEngine` applica la regola di soddisfazione della cache (§3.3): una registrazione con `MultiPV` e profondità maggiori serve anche le richieste dei profili `standard` e `fast`. Per l'avversario al tratto si registra anche la fixture `najdorf_after_be3`.

### G.1 Posizioni (`fixtures/positions/`)

| File | FEN | Uso |
| --- | --- | --- |
| `najdorf.fen` | `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` (43 mosse legali) | Esempio, golden |
| `najdorf_after_be3.fen` | `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N1B3/PPP2PPP/R2QKB1R b KQkq - 1 6` | AC-21 (utente Bianco, tocca al Nero) |
| `opening_pawn_attacked.fen` | `rnbqkbnr/ppp1pppp/8/3p4/4P3/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2` | AC-25: pedoni attaccati, non tattica |
| `knight_attacked_by_pawn.fen` | `rnbqkbnr/ppp2ppp/3p4/4N3/4P3/8/PPPP1PPP/RNBQKB1R b KQkq - 0 3` | AC-25: `hanging_piece` w e5, `unresolved_capture` d6→e5 (SEE 3), colonna 2 |
| `in_check.fen` | `rnbqkbnr/ppp2ppp/3p4/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 1 3` | AC-25: `tactical` per scacco, colonna 2 |
| `rook_endgame.fen` | `8/5pk1/6p1/r7/8/6P1/5PK1/3R4 w - - 0 40` | AC-25: `endgame`, colonna 3 |
| `kpk.fen` | `8/8/8/4k3/8/8/4P3/4K3 w - - 0 1` | AC-25: colonna 4 se tablebase disponibile (M2), altrimenti 3 |

Per `quiet` e per il mediogioco né quieto né tattico i test usano valori di motore sintetici (`FakeEngine` con righe costruite a mano): `spread` 12 → `quiet`; `spread` 40 e divario 60 → colonna 1 non quieta; divario 200 → `tactical`.

### G.2 FEN non valide (AC-02)

| # | Testo | Esito atteso |
| --- | --- | --- |
| 1 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP` | malformata (righe mancanti) |
| 2 | `rnbqkbnr/pppppppp/9/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1` | malformata (carattere non valido) |
| 3 | `rnbq1bnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQ - 0 1` | manca il re nero |
| 4 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1` | malformata (lato al tratto) |
| 5 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKPNR w KQkq - 0 1` | pedone in prima traversa |
| 6 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e3 0 1` | en passant non valido |
| 7 | `rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQkq - 0 1` | diritti di arrocco incoerenti |
| 8 | `4k3/8/8/8/8/8/8/r3K3 b - - 0 1` | lato che non muove sotto scacco |
| 9 | `rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3` | terminale: matto |
| 10 | `7k/5Q2/6K1/8/8/8/8/8 b - - 0 1` | terminale: stallo |
| 11 | `8/8/4k3/8/8/4K3/8/8 w - - 0 1` | terminale: materiale insufficiente |
| 12 | `4k3/8/8/8/8/8/8/3KK3 w - - 0 1` | troppi re (lo stato si controlla prima della posizione terminale) |

### G.3 Casi PGN (AC-03, `fixtures/pgn/`)

| File | Contenuto | Esito atteso |
| --- | --- | --- |
| `single.pgn` | Una partita con tag, `1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 *` | Posizione finale = Najdorf; nessuna domanda |
| `single_bom.pgn` | Come sopra con BOM UTF-8 | Idem |
| `two_games.pgn` | Due partite | Elenco; con `analyze` senza `--game` codice 2; `--game 2` sceglie la seconda |
| `setup_fen.pgn` | `[SetUp "1"] [FEN "8/8/8/4k3/8/8/4P3/4K3 w - - 0 1"]` `1.Kd2 Kd5 *` | Partenza dal FEN; `--ply 0` = posizione del tag |
| `annotated.pgn` | La partita di `single.pgn` con commenti `{…}`, NAG `$1`, varianti `( … )` | Stessa posizione di `single.pgn` |
| `illegal.pgn` | `1.e4 e5 2.Nf6 Nc6 *` | «semimossa 3 (mossa 2 del Bianco): `Nf6` non è legale» |
| `mate.pgn` | `1.f3 e5 2.g4 Qh4# 0-1` | Fine terminale → errore con invito a `--at`; `--at 2w` valido (tocca al Nero) |
| `at_cases` | Su `single.pgn`: `--at 3w`, `--at 5b`, `--ply 0`, `--at 6w` | Validi i primi tre; l'ultimo «La partita ha solo 10 semimosse» |
| `fen_as_pgn.txt` | Il FEN della Najdorf con `--input pgn` | Contraddizione: interattivo chiede, `analyze` codice 2 |
| `garbage.txt` | `ciao mondo` | «Formato non riconosciuto» |

### G.4 Stringhe per V03 (AC-05)

| Testo (dopo la sostituzione dei token) | Esito |
| --- | --- |
| `Il cavallo punta alla casa d5.` | ammesso (la casa a fine frase non è un numero di mossa) |
| `Le case d4 ed e5 sono il centro.` | ammesso |
| `Maia-2 è poco affidabile qui.` | ammesso (letterale) |
| `Hai tre sistemi tra cui scegliere.` | ammesso |
| `{{m:Nb3@N4}} prepara {{plan:w:f3,Qd2@N3}}` | ammesso (token rimossi) |
| `Hai 3 sistemi.` | V03 (cifra) |
| `Gioca Be3 subito.` | V03 (mossa di pezzo) |
| `Dopo exd5 il centro si apre.` | V03 (cattura di pedone) |
| `Arrocca con O-O.` | V03 (arrocco) |
| `La spinta g4-g5 è il piano.` | V03 (catena di case) |
| `Attento alla diagonale a7–g1.` | V03 (catena: usare `{{diag:a7-g1}}`) |
| `Il Nero gioca ...b5.` | V03 (puntini) |
| `Succede nel 50% dei casi.` | V03 (cifra) |
| `Il motore dà +0,37.` | V03 (cifra) |
| `Dopo 6.Be3 la posizione è tesa.` | V03 (numero di mossa e mossa) |
| `Il ♘ va in d5.` | V03 (figurina) |
| `Promuove con =Q.` | V03 (promozione) |

### G.5 Conteggio delle parole (AC-07)

| Testo | Parole |
| --- | --- |
| `Il cavallo va in d5.` | 5 |
| `l'alfiere {{m:Nb3@N4}} è **forte**` | 5 |
| `{{pv:PV1:6}}` | 1 |
| `Tre sistemi: Inglese, Classico.` | 4 |

### G.6 Risposte difettose del modello (AC-16, `fixtures/recorded/llm/`)

| File | Difetto | Errore atteso |
| --- | --- | --- |
| `bad_illegal_san.json` | `{{m:Nf6@N1}}` (illegale per il Bianco) | V04 |
| `bad_unknown_id.json` | `{{ev:C99}}` | V02 |
| `bad_null_value.json` | `{{pct:C1.p_up}}` con `p_up` nullo | V02 |
| `bad_free_digit.json` | «tre» scritto `3` | V03 |
| `bad_chain.json` | `g4-g5` in chiaro | V03 |
| `bad_plan.json` | `{{plan:w:Be3,Qd2,Qxd8@N1}}` (illegale) e un `plan` con scacco non finale | V04 |
| `bad_plan_engine.json` | `plan` in un paragrafo `engine` | V10 |
| `bad_theory_tokens.json` | `{{ev:C1}}` in un paragrafo `theory` | V08 e V10 |
| `bad_extra_section.json` | S11 non prevista | V07(a) |
| `bad_missing_table.json` | S07 senza blocco T1 | V07(b) |
| `bad_must_cover.json` | S07 non cita una candidata `explained` | V07(c) |
| `bad_contamination.json` | «Najdorf» nel testo su `rook_endgame.fen` | V09 |
| `bad_markup.json` | Paragrafo che inizia con `## ` | V01 |
| `bad_assertion.json` | Asserzione `feature` `backward_pawn` w `d4` inesistente | V06 |
| `max_tokens.json` | `stop_reason = max_tokens` | V01 |
| `good_najdorf_1900.json` | Risposta valida: copia di `examples/golden/fewshot/najdorf_w_1900.json` (che supera V01–V10 sul pacchetto congelato), prodotta in M1b | nessuno |

