# Questioni aperte

Formato: problema, prova, proposta o default adottato. Nessuna voce riapre D-01…D-63 né tocca architettura,
schema, token o criteri di accettazione.

## M0

### OQ-M0-1 · Rete dell'ambiente cloud (risolta)

- **Problema.** Alla prima esecuzione di M0 la rete dell'ambiente cloud bloccava `drive.google.com`
  (pesi di Maia-2) e `tablebase.lichess.ovh` (Syzygy).
- **Soluzione.** L'utente ha impostato l'accesso di rete completo; pesi, Syzygy 3-4-5 e
  `fixtures/golden_maia.json` sono stati prodotti. Resta bloccato il download delle release di Stockfish da
  `github.com` (403), non necessario perché Stockfish 16 è installato dal sistema (OQ-M0-2).
- **Nota.** Le Syzygy sono in due cartelle (`3-4-5-wdl/` e `3-4-5-dtz/`); `setup_engines.py` le legge entrambe.

### OQ-M0-2 · Versione di Stockfish fissata a 16 (fino a M2: D-66)

- **Default adottato.** `version_pin: "Stockfish 16"`. È la versione con cui sono stati prodotti i raw
  (§8-bis.2), quindi AC-09 confronta valori omogenei; in questo ambiente è installata dal pacchetto Ubuntu
  (`stockfish 16-1build1`), che `setup_engines.py` riusa perché la versione coincide col pin.
- **Nota.** §3.1.1 parla di «ultima release stabile». Passare a una versione più recente cambia solo il pin
  (§0.5) e richiede di rieseguire `golden --data` e rivedere `docs/golden_diff.md`.
- **Non verificato.** I nomi degli asset di release usati da `setup_engines.py` per scaricare Stockfish
  (`stockfish-ubuntu-x86-64-avx2.tar`, `stockfish-windows-x86-64-avx2.zip`,
  `stockfish-macos-m1-apple-silicon.tar`, …) seguono lo schema delle release da Stockfish 16 ma non sono
  stati controllati: GitHub era bloccato.

### OQ-M0-3 · Gravità dei controlli di `doctor`

- **Default adottato.** `ERRORE` (codice 4) per Stockfish, Maia-2, indice delle aperture, PyTorch e cartelle
  non scrivibili; `AVVISO` per chiave API assente (serve da M1c), Syzygy incomplete (servono da M2),
  `version_pin` diverso o mancante, `reference_time_s` non impostato.

### OQ-M0-4 · Parametri del benchmark di `doctor`

- **Default adottato.** E0 sulla posizione d'esempio con profondità minima `profiles.fast.dmin.root` (16,
  come §3-ter.5) e `MultiPV` `profiles.standard.multipv.root` (12), senza aggiungere chiavi alla
  configurazione dell'Appendice D. `reference_time_s` è il tempo misurato in M0 su questa macchina:
  le stime per profilo sono quindi `B × tempo_misurato / reference_time_s`.

### OQ-M0-5 · PyTorch con CUDA su Linux

- **Problema.** Da PyPI `torch` 2.8 su Linux è la build CUDA (pacchetti `nvidia-*`, diversi GB).
  `requirements.lock` riflette quindi la build CUDA.
- **Proposta.** Su macchine senza GPU installare prima `torch==2.8.0` dall'indice CPU
  (`--index-url https://download.pytorch.org/whl/cpu`), poi il resto. CPU è sufficiente (§3.2).

### OQ-M0-6 · Mossa nulla e Stockfish

- **Problema.** `python-chess` invia a Stockfish la posizione iniziale più le mosse; una mossa nulla
  (`0000`) dentro la lista non è un'istruzione UCI affidabile.
- **Soluzione (confinata nell'adattatore).** Se lo storico contiene una mossa nulla, `analyse_node`
  analizza la posizione risultante dal suo FEN. Per il nodo E1 la storia non serve (D-43).

### OQ-M0-7 · Probabilità di Maia-2 arrotondate dal pacchetto

- **Problema.** `maia2` arrotonda le probabilità a 4 decimali: probabilità < 0,00005 diventano 0.
- **Effetto.** Nessuno sulle regole (soglie ≥ 0,001); `{{pct}}` di una mossa a probabilità 0 si rende «0%»
  invece di «<1%». Da tenere presente in M1b (formati, §9-bis.7).

### OQ-M0-8 · Conteggio delle parole dei raw

- **Default adottato.** Per la prima stima (§8-bis.4 punto 4) una riga che contiene `[MAIA]` è esclusa
  per intero anche se contiene altro testo (1900, S03: «Alternative pratiche…»); le tabelle di solo
  testo (1900, S05) contano cella per cella; una tabella con almeno un valore `±d,dd` è numerica ed esclusa
  (anche le sue colonne di testo). La misura definitiva è quella dei fewshot in M1b.

### OQ-M0-9 · Variabilità del benchmark

- **Osservazione.** Sulla stessa macchina il benchmark di `doctor` ha misurato 7,9 s, 7,4 s e 4,7 s.
- **Default adottato.** `reference_time_s: 7.9` (prima misura, in condizioni di carico simili a quelle di
  `golden --data`). Le stime per profilo sono indicative; si ricalibra in M1a con i tempi reali della pipeline.

## M1a

Dubbi minori risolti con un default (istruzione 9); nessuno tocca architettura, schema, token o criteri.

### OQ-M1a-1 · Risultati di E4 nel pacchetto
Lo schema dei nodi (§6.2) non ha una fase E4. Le mosse valutate da E4 entrano tra le candidate
(`source: "e4"`, con valutazione e PV), ma la ricerca ristretta non diventa un nodo. In M1b
`{{ev:SAN@N1}}` per una mossa di E4 si risolve dalla candidata corrispondente.

### OQ-M1a-2 · `PV<n>` con l'avversario al tratto
§3-ter.3 definisce `PV<n>` come la PV di `C<n>`. Con l'avversario al tratto non ci sono `C<n>`:
`PV<n>` è la PV della riga alla radice di `R<n>` (stesso numero), così i blocchi `line` restano disponibili.

### OQ-M1a-3 · `eval_end_user_cp`
È la valutazione della riga da cui viene la PV (la PV non viene rianalizzata alla fine).

### OQ-M1a-4 · «di {opp}» nei titoli e nelle intestazioni
`config/section_titles.yaml` e `config/tables.yaml` contengono «di {opp}»: con «il Nero» darebbe
«di il Nero». Il codice scrive la preposizione articolata («del Nero», «del Bianco»).

### OQ-M1a-5 · Riserva per E3-ℓ1 (§3-ter.2)
La pianificazione procede nell'ordine di esecuzione e, dentro ogni fase scartabile, taglia dagli elementi
di rango peggiore. Poiché E3-ℓ1 è la prima fase scartabile, l'ordine di scarto di §3-ter.2
(ℓ3, ℓ2, E2c, E2b, ℓ1) si ottiene senza una riserva esplicita; AC-33 lo verifica.

### OQ-M1a-6 · Nodi E2c ed E2b nel pacchetto
Un nodo E2c ha lo stesso percorso del nodo di E2 che completa, `root_moves` = la mossa di contesto,
`parent` = quel nodo E2, `citable: false`. Un nodo E2b ha come `parent` l'antenato analizzato più vicino.

### OQ-M1a-7 · Elo fuori intervallo con `analyze`
È un valore di opzione: uscita con codice 2 (uso scorretto). Nel flusso interattivo la domanda si ripete.

### OQ-M1a-8 · FEN scelta ma testo non riconosciuto
Con il metodo FEN, un testo che non supera `detect_format` viene comunque validato come FEN, così la FEN
n. 1 dell'Appendice G.2 dà «FEN malformata» come previsto. Nel flusso interattivo la FEN si legge su una
sola riga (il PGN fino alla riga con il solo punto).

### OQ-M1a-9 · Ordine dei messaggi di stato della FEN
Un pedone in prima traversa fa scattare anche «troppi pedoni»: si controlla prima la traversa
(Appendice G.2, n. 5).

### OQ-M1a-10 · Registrazioni dei motori
`pytest -m engines --record` usa il profilo `deep` con i tempi dimezzati (`time_scale` 0,5): le
profondità minime restano quelle del profilo, ma qualche nodo può risultare `unstable_depth`.
`FakeEngine` rigioca esattamente ciò che è stato registrato (anche se instabile) e risponde a una ricerca
ristretta (`root_moves`) da una registrazione della stessa posizione che contiene tutte le mosse richieste.

### OQ-M1a-11 · Righe di T2 «Dopo c»
Per una risposta di `Rset(c)` assente dal `MultiPV` del nodo E2 (la mossa più probabile di Maia-2) la
valutazione è la prima riga del nodo ℓ1 corrispondente; se manca anche quello la mossa compare senza valore.

### OQ-M1a-12 · Testimoni ordinati
Per `pin` e `unresolved_capture` le case sono una coppia ordinata (inchiodato, inchiodatore; da, a), non in
ordine alfabetico, come indicano le definizioni di §5.1.

### OQ-M1a-13 · Costanti numeriche rimaste nel codice (risolta: D-65)
La regola è «nessuna costante numerica nel codice» (istruzione 5). Restano nel codice solo valori che la
documentazione fissa nel testo normativo e che l'Appendice D non mette in configurazione: `loss_cp ≤ 30`
della condizione c3 (§8.2, matrice fissa per §0.5), la soglia `p ≥ 0,001` della policy nei nodi (§6.2),
i 40 caratteri dello slug della cartella (§2-bis.5), le soglie di AC-09 (0,25 pedoni, prime 6), i limiti di
formato della scacchiera (colonne c–f, ali) e, da M1c, le dimensioni della vista ridotta (5 righe, PV di 6
semimosse, 5 mosse di Maia-2, §6.1). Se si preferisce averli in `config/`, va aggiunta una chiave
all'Appendice D: è una decisione dell'utente.
**Risolta (D-65):** l'utente ha scelto di spostarle in configurazione; vedi `docs/DECISIONI_POST_CONGELAMENTO.md`.

## M1b

Dubbi minori risolti con un default (istruzione 9); nessuno tocca architettura, schema, token o criteri.

### OQ-M1b-1 · Pacchetti golden costruiti dalle registrazioni
`golden --packs` usa per default i motori veri (con una cache nuova). I pacchetti congelati sono stati
prodotti con `golden --packs --recorded`, cioè la stessa pipeline sulle registrazioni di M1a: così in M1c
`analyze --elo 1900 --budget deep` con `FakeEngine` (AC-01) ricostruisce esattamente il pacchetto su cui è
scritto `good_najdorf_1900.json`. Se si rigenerano i pacchetti con i motori veri vanno rifatte anche le
registrazioni, e i fewshot riallineati. Il pacchetto della fixture AC-21 (`najdorf_after_be3_w_1900`) è
congelato accanto ai tre, per `_s07_alt.json`.

### OQ-M1b-2 · Token su nodi non citabili
Un token che cita un nodo con `citable: false` è un errore V02 (il modello non riceve quei nodi, §6.1).
`ev:SAN@N` cerca la mossa nel `multipv` del nodo e poi nelle ricerche ristrette (`root_moves`) della stessa
posizione (§9-bis.2).

### OQ-M1b-3 · Segni di scacco nella resa
In ingresso `+ # ! ?` si accettano e si ignorano; in uscita `m`, `mv`, `pv` e `plan` usano la SAN di
python-chess, con `+`/`#` (come le PV del pacchetto).

### OQ-M1b-4 · `must_cover`
Un ID è «citato» se è l'argomento di un token della sezione (`mv:C1`, `ev:C1`, `pct:C1.p_user`…);
`R1.u1` non cita `R1`. Le righe di una tabella non contano: servono token nel testo, anche nelle celle.

### OQ-M1b-5 · Token non risolto e V08/V10
Un token sintatticamente valido ma non risolto (V02, V04) conta comunque per la sua classe nelle regole
di V08 e V10, per non generare errori a cascata.

### OQ-M1b-6 · Dettagli della modalità degradata (§10.2)
Un errore V01 di markup in un blocco lo rimuove come un V03; un errore in una cella di `text_table` rimuove
l'intera tabella; un errore nella didascalia di `line` rimuove la didascalia; la quota `theory` oltre il
tetto (errore senza blocco) diventa un avviso.

### OQ-M1b-7 · Marca † e nota
La † segue ogni paragrafo, voce e cella `theory`; nelle `text_table` una sola † per riga. La nota «† contenuto
teorico…» chiude il documento, dopo il rapporto.

### OQ-M1b-8 · Testata e rapporto
I modelli delle righe sono quelli di §8.6 (in `render/report.py`); da `config/wording.yaml` vengono gli
avvisi. «Avversario: {Elo} {scala} → {Elo Maia}». Il pacchetto non registra il tempo totale dell'esecuzione:
il rapporto riporta il «tempo dei motori», somma dei `time_s` dei nodi, così il documento è riproducibile
(AC-27).

### OQ-M1b-9 · Esito di `golden --render`
Se un fewshot non supera la verifica il comando elenca gli errori, non scrive il suo `rendered` e termina
con codice 3. `_s07_alt.json` si verifica sul pacchetto AC-21 con il piano ristretto a S07; ha anche un
`_s07_alt.meta.yaml`.

### OQ-M1b-10 · Formato delle risposte registrate (Appendice G.6)
`fixtures/recorded/llm/*.json` contengono i campi della risposta dell'API letti dalla verifica
(`stop_reason`, `content` con il blocco `tool_use`). Ogni file difettoso è `good_najdorf_1900.json` con un
solo difetto, generato da `python -m tests.fault_fixtures`. `bad_contamination.json` è scritto sul
pacchetto sintetico del finale di torri (`rook_endgame.pack.json`, congelato accanto) e, essendo corto,
produce anche V07(d). In più c'è `bad_long_line.json` per AC-08.

### OQ-M1b-11 · Misura delle parole e valori di §0.5
Regola e decisioni in `docs/golden_diff.md`: `prose_words` di `1200_1600` 650 → 500 e di `ge2400`
800 → 610, pesi dell'ancora 1500 aggiornati; 1900 e i tetti `theory_max_share` invariati.

### OQ-M1b-12 · `_terms.txt`
Una riga per gruppo di alias, commenti con `#`. Oltre ai termini richiesti c'è `Siciliana|Sicilian`.

### OQ-M1b-13 · Articoli davanti alle percentuali
Il token produce solo il numero («8%»): frasi come «il {{pct}}» danno «il 8%». I fewshot sono scritti per
evitarlo; per le risposte del modello non c'è un controllo (sarebbe una regola di stile, non di verifica).

## M1c

### OQ-M1c-1 · `temperature` e SDK
Nell'SDK `anthropic` 1.11.0 (quello fissato in `requirements.lock`) `messages.create` non ha il parametro
`temperature`. Il client lo invia con `extra_body`; se l'API lo rifiuta (400 che cita `temperature`) la
richiesta si ripete una sola volta senza, lo si annota nel log e non lo si invia più (§9.1).

### OQ-M1c-2 · Tentativi di rete
`network_attempts: 3` = tre tentativi in tutto; tra un tentativo e il successivo si attendono 2 e 4 secondi
(`network_backoff_s`, più `retry-after`). Il terzo valore (8 s) servirebbe solo con un quarto tentativo.

### OQ-M1c-3 · Chiave API assente
I motori girano comunque: `pack.json` viene salvato e poi l'uscita è con codice 4 e l'invito a usare
`chessanalyst rerun <cartella>` dopo aver impostato `ANTHROPIC_API_KEY`. `doctor` continua a segnalarla come
AVVISO (è un controllo d'ambiente; il codice 4 lo dà `analyze` quando serve).

### OQ-M1c-4 · Messaggio di retry
Segue l'Appendice E.3 (frase iniziale, poi una riga per errore); §9.3 descrive gli stessi elementi in ordine
inverso. Se la risposta non contiene un blocco `tool_use` (per esempio `max_tokens` senza strumento) gli errori
vanno in un normale messaggio utente, perché un `tool_result` richiede `tool_use_id`.

### OQ-M1c-5 · Legenda
I token di `_s07_alt.json` sono aggiunti alla stessa legenda (risolti sul pacchetto AC-21), senza ripetere
quelli già presenti; anche i blocchi `line` hanno una riga di legenda.

### OQ-M1c-6 · Schema dello strumento
Generato dai modelli `pydantic` (`llm/schema.py`), senza le chiavi `discriminator` e `title`; i campi
facoltativi sono assenti, mai `null`, come nell'Appendice F. Il test di equivalenza con l'Appendice F usa
`jsonschema` (aggiunto all'extra `dev`).

### OQ-M1c-7 · Log
I logger dell'SDK e di `httpx` sono portati a WARNING: `run.log` non contiene le richieste. La chiave non è
mai scritta né stampata; la suite normale nasconde `ANTHROPIC_API_KEY` ai test (solo i test `llm` la vedono).

### OQ-M1c-8 · Risposte registrate del modello reale (AC-10, AC-21 «modello»)
`pytest -m llm --record` esegue il ciclo completo con l'API del fornitore configurato (D-64) sui pacchetti congelati (1500, 1900, AC-21) e salva
`fixtures/recorded/llm/real_*.json`; i test di accettazione li rigiocano con `FakeLLM`. Senza la chiave i
test sono saltati con un messaggio esplicito.

### OQ-M1c-9 · Fornitore OpenRouter (D-64)
Il client OpenRouter usa la libreria standard (`urllib`), senza dipendenze nuove. Converte i messaggi:
blocchi `tool_use` → `tool_calls` (argomenti in JSON), `tool_result` → messaggio `role: tool` (OpenAI non ha
`is_error`: l'errore è nel testo, che inizia con «La consegna contiene errori»), `tool_choice` forzato con
`{"type": "function", "function": {"name": "submit_analysis"}}`, `cache_control` mantenuto nel messaggio di
sistema (caching dei modelli Claude via OpenRouter). `finish_reason`: `tool_calls` → `tool_use`, `length` →
`max_tokens`. Argomenti non in JSON valido → V01. Un errore riportato dentro una risposta 200 è trattato con il
suo codice. `llm_raw.json` conserva anche la risposta originale (`provider_response`). Verificato in rete con
una chiave volutamente non valida: 401 → «Chiave API non valida o non autorizzata».

### OQ-M1c-10 · Token dentro `notes` (RISOLTA: proposta approvata dall'utente il 4 ottobre 2026)
**Problema.** La v0.9.1 non dice come si verifica il campo `notes`: §10.1 non lo nomina e il rapporto (§9.4)
lo copia così com'è. V11 invece vieta qualunque `{{…}}` nel documento finale.
**Prova.** Registrazione reale `real_najdorf_after_be3_w_1900.json` (DeepSeek, 4 ottobre 2026): l'ultima
risposta passa V01–V10 a parte V07(d), ma una nota contiene `{{pct:root.draw}}`. Il render la copia nel rapporto
e V11 solleva `RenderBug`: l'analisi si interrompe e AC-21 («modello») fallisce. Le note contengono anche
`C1, C2` in chiaro, che nessun controllo vede.
**Proposta.** Si estende V03 a `notes`: niente token, mosse, cifre o catene in chiaro, come nel testo. Una nota
che viola V03 provoca un retry. In modalità degradata la nota viene tolta e la rimozione finisce nel rapporto.
Poi `bad_notes_token.json` diventa un test di fault injection (G.6). Prompt ed esempi non cambiano.
**Implementazione.** `Checker._check_notes` applica V03 a ogni nota, con errore nella cella «nota k» e senza
sezione né blocco. Il messaggio di retry dice al modello quale nota correggere. `degrade` toglie la nota in
entrambe le modalità (`mark` e `drop`) e la elenca in «Rimossi in modalità degradata» («nota k del modello
(V03)»). Test: `bad_notes_token.json` (G.6) e due test in `test_ac16_fault_injection.py`.

## M2

### OQ-M2-1 · Stockfish 19 (D-66): nomi dei file della release
Da Stockfish 19 le release hanno binari «universali», che riconoscono da soli le istruzioni della CPU.
I nomi sono stati verificati sulla pagina ufficiale `stockfishchess.org/download` (ottobre 2026):
`stockfish-linux-x86-64-universal.tar.gz`, `stockfish-linux-arm64-universal.tar.gz`,
`stockfish-macos-universal.tar.gz`, `stockfish-windows-x86-64-universal.zip`,
`stockfish-windows-arm64-universal.zip`. `setup_engines.py` sceglie lo schema in base al numero di versione:
da 19 i binari universali, prima quelli per insieme di istruzioni. In questo ambiente cloud lo scaricamento
diretto del file da GitHub funziona (la pagina delle release e l'API restano bloccate, 403). Pin:
`version_pin: "Stockfish 19"`. `FakeEngine.from_dir` legge la versione dalle registrazioni, perché la versione
fa parte della chiave di cache.

### OQ-M2-2 · E2c e nodi di ℓ2 in T3
§3-ter.2 mette E2c prima di E3-ℓ2, ma da M2 i nodi di T3 comprendono anche quelli di ℓ2 (§3-ter.6), che in
quel momento non esistono ancora. **Default:** E2c gira al suo posto sui nodi di E2; dopo E3-ℓ2 le candidate di
contesto si ricalcolano su E2 + ℓ2 e una seconda passata di E2c completa i valori mancanti (stessa fase E2c,
stesso tempo per nodo). L'ordine di scarto resta quello di §3-ter.2 per tutto ciò che precede ℓ2. Il tempo per
nodo di E3 (`quota × B / nodi pianificati`) usa i nodi di tutti i livelli: ℓ1 × numero di livelli, perché ℓ2 e
ℓ3 aggiungono un nodo per ogni nodo del livello sopra.

### OQ-M2-3 · Aperture per sequenza
L'indice per EPD (`data/openings_index.json`) non conserva l'ordine delle mosse, quindi `setup_engines.py`
scrive accanto un secondo file, `data/openings_sequences.json`: sequenza UCI dalla posizione iniziale → voce.
Con una partita PGN che parte dalla posizione iniziale si cerca la riga più lunga che è prefisso delle mosse
(`matched_by: "sequence"`). Senza storia, o con un `[FEN]` iniziale, si cerca per EPD come in M1. `in_book` resta
«EPD nell'indice» (§3.3), anche quando il nome viene dalla sequenza.

### OQ-M2-4 · Esito delle tablebase «espresso a parole»
§3.3 dice che con la tablebase l'esito esatto prevale sulla valutazione ed è espresso a parole. AC-17 vuole
«nessuna valutazione numerica nel testo». La grammatica dei token è congelata e non ha un token per la
tablebase. **Default:**
- Il pacchetto ha `tablebase: {wdl, dtz, result_text_key}` dalla sonda diretta alla radice, dal punto di vista
  dell'utente (anche il segno di `dtz`). `result_text_key` vale `win`, `cursed_win`, `draw`, `blessed_loss`
  o `loss`.
- Quando `tablebase` non è nullo:
  - `{{ev:N1}}` si rende con il testo dell'esito esatto (`wording.yaml: tablebase.results`);
  - gli altri `ev` diventano vittoria, patta o sconfitta. Stockfish con `SyzygyPath` dà alle posizioni in
    tablebase punteggi di vittoria (`cp 20000`, quindi ±9999 dopo il limite di D-39) oppure 0;
  - `loss` si rende «nessuna» o «decisiva»;
  - le celle delle tabelle si rendono «vinta», «patta» o «persa»;
  - `pct:root.*` dà V02, perché l'esito esatto prevale.
- S12 ha `must_cover: [N1]`, così l'esito esatto è sempre citato.

Il testo dell'utente non contiene quindi cifre di valutazione.

### OQ-M2-5 · c5: «pezzi coinvolti»
Le case di `focus_squares` sono le case **alla radice** di due gruppi di pezzi:
- quelli nel testimone delle feature tattiche disponibili (`pin`, `hanging_piece`, `unresolved_capture`; da M3
  anche `fork`, `skewer`, `overloaded_piece`);
- quelli che si muovono nelle prime `c5_pv_plies` (4) semimosse delle prime `c5_pvs` (3) PV. Un pezzo che si
  muove due volte conta con la casa di partenza; nell'arrocco si muovono re e torre.

I pedoni non sono «pezzi» e restano fuori. Senza pezzi coinvolti S05 è omessa (`matrix`). Le due costanti sono
in `thresholds.yaml: section_plan` (D-65).

### OQ-M2-6 · Posizioni non Najdorf (§8-bis.6)
Tre fixture con checklist in `fixtures/checklists/`, con i pacchetti congelati in `fixtures/packs/`:
- **Fried Liver** (PGN, utente Bianco, 1500): colonna 2, mediogioco tattico per il cavallo in presa. Il nome
  dell'apertura viene dalla sequenza;
- **finale di torri** (`rook_endgame.fen`, 1900): colonna 3;
- **Lucena** (`lucena.fen`, 1900): colonna 4, tablebase, usata per AC-17.

Il raw 1900 di `golden_nodes.json` (Stockfish 16) resta il dato di M0: AC-32 «registrato» lo usa così com'è,
perché riproduce le righe del raw. D-66 chiede di rifare solo registrazioni, pacchetti e fewshot.

### OQ-M2-7 · Registrazioni dei motori con E3 fino a ℓ3
Con ℓ2 e ℓ3 l'albero del profilo `deep` arriva al tetto di 80 nodi. Il metodo di M1a (tempo dimezzato, orologio
vero) dava registrazioni che i test non riuscivano a rigiocare:
- la scadenza globale scartava nodi che il replay (motori finti istantanei) chiede comunque;
- un nodo sotto la profondità minima veniva ricercato da un'esecuzione successiva dello stesso gruppo (un'altra
  ancora) e sovrascritto; la prima mossa poteva cambiare, e con lei i figli richiesti nel replay.

**Default:** `golden/record.py` registra con tempo pieno (`time_scale` 1) e un orologio fermo per la sola
scadenza globale. Salva **tutte** le ricerche, non solo quelle della cache: la stessa posizione può essere un nodo
di E2b (MultiPV 2) e di ℓ3 (MultiPV 8), e la cache tiene solo la più profonda. `FakeEngine` conserva tutti i
risultati di una posizione e dà il migliore che soddisfa la richiesta (regola della cache, §3.3); se nessuno la
soddisfa, rigioca esattamente una ricerca con abbastanza righe. Nei gruppi con più esecuzioni sulla stessa cache
(la Najdorf: tre ancore più `standard`) ogni ricerca aspetta la profondità minima, fino alla scadenza globale del
profilo. Senza questa attesa un nodo instabile verrebbe rifatto dall'esecuzione successiva e il replay della prima
chiederebbe un altro albero. Gli altri gruppi usano i tempi normali: un nodo instabile resta registrato e compare
come `unstable_depth`. Esempio: la radice di Lucena con MultiPV 16 arriva a profondità 14 in 60 secondi, contro
una minima di 20, perché Stockfish rallenta molto con le tablebase alla radice. Le regole di tempo e scadenza di
§3-ter.2 restano invariate nell'uso normale.

### OQ-M2-8 · Mossa di contesto con i nodi di ℓ2 (RISOLTA con D-68: filtro al 3% ed esclusione degli errori tattici)
**Problema.** §3-ter.6 vuole riprodurre il ragionamento «`...Nc6` costa poco contro un sistema e molto contro
un altro». Da M2 i nodi di T3 comprendono tutti i nodi di ℓ2, cioè 9 nodi in più oltre ai 5 di E2 a 1900. Con
quel numero di nodi l'algoritmo congelato sceglie mosse che nessun avversario gioca: la loro differenza di
costo viene da una sola linea tattica.

**Prova** (pacchetti `deep` con Stockfish 19, registrazioni del 4 ottobre 2026):

| Ancora | Regola v0.9.1 (E2 + ℓ2) | Righe di T3 | Con la sola condizione «p_opp medio ≥ 3%» |
| --- | --- | --- | --- |
| 1500 | `...h5`, spread 138 | 12 | `...e5`, spread 104 |
| 1900, 2400 | `...Bd7` (p 0,1–0,7%), spread 132 (1,41 dopo `6.h3 e6 7.g4`) | 14 | `...e5`, spread 104: costo 0 contro ogni sistema, 1,04 contro `6.Bg5` |

**Proposta.** Tra le candidate di contesto (passo 2 di §3-ter.6) entrano solo le mosse con `p_opp` medio sui nodi
di T3 almeno `e4_min_p` (3%), la stessa soglia che definisce una mossa «umana» per E4. Il risultato riproduce
l'insegnamento del raw: `...e5` va bene contro tutto tranne `6.Bg5`. Il resto dell'algoritmo resta invariato,
così come i nodi di T3 (E2 + ℓ2). La soglia sarebbe una nuova chiave
`thresholds.yaml: selection.context_min_p` (D-65).

**Seconda registrazione (dopo la prima risposta dell'utente).** Stockfish con più thread non è deterministico
(D-60): il nuovo albero ha portato con il solo filtro al 3% a `...e6`, con spread 971. Lo spread nasceva da un
nodo (`6.Be3 Ng4 7.Bg5`) in cui `...e6` lascia la donna. Sono state misurate due alternative:
- escludere le righe con p < 3%: rompe AC-32, perché sui nodi del raw `...Nc6` ha p 0,5–1%;
- escludere le righe con costo ≥ `tactical.gap_cp`: dà `...g6` (1900, 2400, spread 117), `...h6` (1500,
  spread 79) e AC-32 resta `...Nc6` con spread 53.

L'utente ha scelto la seconda (D-68 aggiornata).

### OQ-M2-9 · Argomenti dello strumento non in JSON valido (bug di verifica, corretto)
Una risposta reale di DeepSeek sul finale di torri aveva gli argomenti di `submit_analysis` non validi: una
parentesi chiusa di troppo alla fine e niente `notes`. Il client li converte in `input: null`, come previsto da
OQ-M1c-9, ma `extract_output` non segnalava alcun errore. Il ciclo si fermava come se la risposta fosse buona e
usciva con il codice 5, senza retry. Ora `input` che non è un oggetto dà V01 («argomenti di submit_analysis ·
non sono un oggetto JSON valido») e provoca il retry. Fault injection: `bad_tool_arguments.json` (G.6) e
`test_invalid_tool_arguments_are_retried`.

### OQ-M2-10 · Checklist sulle risposte del modello (RISOLTA: decisione dell'utente)
Le checklist (§8-bis.6) chiedono sezioni, tre mosse e due errori tipici. Sulle risposte di DeepSeek sezioni e
mosse ci sono sempre, gli errori tipici no:
- Fried Liver: manca `d3`;
- finale di torri: mancano «torre passiva» e lo scambio delle torri;
- Lucena: manca «costruire il ponte».

**Decisione dell'utente:** sezioni e mosse sono un requisito (il test fallisce), gli errori tipici una misura di
qualità (`ChecklistQualityWarning` nel riepilogo di pytest, il test non fallisce). Prompt, esempi e checklist
restano invariati.

## M3 — Category Scoring Engine

§5-bis dà le formule ma lascia aperti l'insieme delle linee, il significato di `P_dif`, lo schema di
`categories` e `filtered_lines`, il modo di citare le linee nel testo e tutte le costanti. Le costanti sono «ipotesi
iniziali» da calibrare in M5 (§0.5, D-21): stanno in `thresholds.yaml: scoring`. Le scelte qui sotto sono
default (§15.2); nessuna cambia una decisione del registro.

### OQ-M3-1 · Quali linee e che cosa significa `1 − P_dif`
**Problema.** «Per ogni linea ℓ» non dice quali linee. Inoltre la linea principale di Stockfish contiene già la
miglior difesa: se `P_dif` fosse il prodotto delle mosse del difensore lungo la PV, il danno `impatto` (la perdita
della linea) si avrebbe anche quando il difensore trova tutte le mosse.
**Default.** La linea ℓ è la prima riga di un nodo analizzato, letta come attacco di chi muove lì (A) contro
l'altro (D). Due tipi:
- `threat`: le prime `null_lines` (3) righe della mossa nulla (E1). L'impatto è quanto A guadagna con il tempo in
  più rispetto alla radice. `1 − P_dif` è la probabilità che D alla radice giochi una mossa che non para: somma
  della policy di D sulle mosse con perdita ≥ metà dell'impatto (`parry_share`) e sulle mosse non valutate;
- `refutation`: il nodo X (E2, E3 ℓ1–ℓ3, R) è stato raggiunto con una mossa `m` di D. L'impatto è la perdita di
  `m`. `1 − P_dif` è la probabilità che D giochi `m` nel nodo padre, moltiplicata per la probabilità di arrivarci
  (prodotto della policy di Maia-2 sulle mosse del percorso).

`P_att` è il prodotto delle probabilità di Maia-2 delle mosse che A deve trovare nelle prime `att_plies` (6)
semimosse: la prima mossa e le mosse forzanti (catture e scacchi). Le mosse tranquille di seguito non contano:
con tutte le mosse la minaccia `...Qxg5` della Fried Liver (cavallo in presa) aveva `P_att` 0,01 invece di 0,57.
Le linee con impatto < `impact_min_cp` (50) non entrano. `risk = P_att × (1 − P_dif) × impatto` in pedoni.

### OQ-M3-2 · Linee principali e termine «decisione» di R
**Problema.** Con le sole linee di rischio, R non vede di che cosa tratta la scelta. Nella Fried Liver
`6.Nxf7 Kxf7 7.Qf3+` non ha «impatto» (è la valutazione di riferimento), e la sicurezza del re veniva con R 3.
**Default.** Le PV delle candidate spiegate (o delle risposte, in modalità avversario) sono «linee principali».
Ricevono i tag ma non rischio, quindi non cambiano T. In R entrano come quota delle linee principali con quel tag
(`decision`). Pesi di R: preoccupazione 0,4 (`100 − min(T)`), |balance| 0,15, vicinanza 0,2, decisione 0,25. La
vicinanza (`proximity`) è pesata con `min(1, risk/θ)`: una linea quasi impossibile a quel livello non rende urgente
una categoria. R è moltiplicato per il peso della categoria nella fase (`relevance.phase`). La traccia elenca i
`PV<n>`.

### OQ-M3-3 · Tag, foglia e quiescenza
**Default.** La foglia di una linea viene dopo `leaf_plies` (6) semimosse. Poi la linea prosegue finché la mossa
successiva è una cattura o uno scacco (al massimo 4). Se la PV finisce prima, si gioca la cattura con SEE ≥ 1
migliore. Una prima versione giocava catture «golose» per entrambi i lati e produceva foglie false.

Regole dei tag (start = inizio della linea, foglia dopo la quiescenza):

| Tag | Si assegna se |
| --- | --- |
| re | scacchi o matto di A, oppure più attaccanti nella zona del re di D, oppure nuovi `pawn_shield_weakened`, `open_file_to_king` o `castling_lost` di D |
| struttura | nuove debolezze di pedone di D o nuovi passati di A |
| spazio | spostamento del controllo del centro ≥ 3, oppure nuovo `space_advantage` di A |
| attività | spostamento della mobilità ≥ 8, nuovi pezzi inattivi di D, oppure nuovi avamposti, colonne o settima di A |
| iniziativa | ≥ 2 mosse forzanti di A nelle prime 6 semimosse |
| minacce | mossa nulla, oppure un nuovo motivo tattico contro D dopo la prima mossa di A |
| materiale | guadagno ≥ 1 di A |
| transizioni | ingresso nel finale o nel numero di pezzi delle tablebase |

Una linea senza tag va in «minacce». Ogni linea ha anche una categoria principale (`primary`), con questa
priorità: matto → re, materiale guadagnato → materiale, mossa nulla → minacce, altrimenti il primo tag.

### OQ-M3-4 · T statica, override, confidenza
**Default.**
- `T_stat = 100 − punti`, con punti per feature in `scoring.static` (`own` = feature del lato, `opp` =
  dell'avversario).
- Per spazio, attività e iniziativa conta solo l'eccesso rispetto all'avversario (`relative`): nell'apertura
  entrambi hanno pezzi da sviluppare e la sola presenza non preoccupa.
- `practical_complexity` è meta: entropia media della policy e quota di mosse uniche (scarto tra prima e seconda
  riga ≥ 100 cp) nei nodi in cui muove il lato.
- L'override (matto o perdita decisiva con `P_att ≥ 0,10`) porta T a 29, non a 30. Così rispetta «T ≤ 30» e cade
  nella banda «critico» (< 30) di §5-bis.2. Vale solo per la categoria principale della linea: con tutti i tag,
  una sola minaccia della Fried Liver rendeva critiche quattro categorie.
- La confidenza è `low` se Maia-2 è saturo, se la radice è instabile o se lo è il nodo d'inizio di una linea
  della categoria.

### OQ-M3-5 · Schema di `categories` e `filtered_lines`
**Default** (`pack/schema.py`):
- `CategoryScore`: `id`, `T: {w, b}`, `R`, `balance` (T dell'utente − T dell'avversario), `advice` (banda della T
  dell'utente), `confidence`, `components` e `trace` (`features` = indici in `pack.features`, `lines` = `L<n>`,
  `pvs`, `nodes`);
- `FilteredLine`: `id` (`L<n>`, prima le minacce, poi per nodo e rango), tipo, nodo d'inizio, `entry`,
  attaccante e difensore, `against_user`, `plies`, `eval_end_user_cp`, `impact_cp`, `p_att`, `p_walk`, `risk`,
  mosse dell'attaccante con le probabilità, `tags`, `primary`, `visible_at_level`, `reason`
  (`theta` | `mate` | `decisive`).

La vista ridotta per il modello manda solo la T dell'utente (O-5), senza componenti e tracce.

### OQ-M3-6 · Citare le linee: `L<n>` e modifiche del prompt
**Problema.** S09 si basa su `filtered_lines`, ma la grammatica di §9-bis.2 non ha un modo di citarle. `PV<n>`
è riservato alla PV di `C<n>` (§3-ter.3).
**Default.**
- Gli `L<n>` sono ammessi dove serve una linea: `{{pv:L1:n}}` (mosse dal nodo d'inizio, V05 su
  `max_pv_plies`), `{{ev:L1}}` (valutazione alla fine), `{{loss:L1}}` (danno per chi la subisce) e il blocco
  `{"type": "line", "pv": "L1"}`.
- Lo schema dello strumento accetta l'asserzione `category_advice` (§9-bis.5) con `advice` tra `no_worry`,
  `monitor`, `attention` e `critical`.
- Il system prompt è l'Appendice E.1 parola per parola, più sette modifiche elencate in
  `llm/prompt.py: M3_PROMPT_CHANGES`: dati del radar, regola dei token `sc`, `category_advice`, punteggi
  in `notes`, token, S02, S09.
- Il test controlla sia l'Appendice sia le modifiche.
- Nella riga di istruzioni, T4 elenca gli ID delle righe (nomi di categoria).

### OQ-M3-7 · Tabella T4, S02, S09 e budget
**Default.**
- T4 ha al massimo 5 righe all'ancora 1500 («radar semplificato»), 9 a 1900 e 5 a 2400 («fattori decisivi»):
  `tables.yaml: T4.rows_max`.
- Con confidenza bassa l'intestazione T ha un asterisco e c'è la nota `score_low_confidence_table`.
- In colonna 4 T4 non si costruisce.
- `must_cover` di S09 contiene le linee con `visible_at_level: false`. In colonna 1 e 2 S09 è obbligatoria anche
  senza linee: il testo lo dice con i dati.
- `prose_words` è aggiornato come in M1b (§0.5), così le sezioni esistenti tengono il loro budget e S02 e S09
  ricevono la loro quota: 1200_1600 da 500 a 560, 1600_2000 da 1400 a 1560, ge2400 da 610 a 690.

### OQ-M3-8 · Registrazioni di Maia-2 lungo le linee
`P_att` interroga Maia-2 su posizioni che l'esplorazione non visita. Maia-2 è locale e deterministico, quindi le
risposte mancanti si aggiungono rigiocando le ricerche registrate, senza Stockfish:
`CHESSANALYST_RECORD_MAIA_ONLY=1 pytest -m engines --record` (`golden/record.py: record_maia`). Le ricerche di
Stockfish e gli ID dei pacchetti congelati non cambiano.

### OQ-M3-9 · Budget di S02 e note in lettere (RISOLTA: decisione dell'utente)
**Problema.**
- DeepSeek scriveva una nota per ogni riga di T4 e superava il budget di S02 (V07 d): 47–81 parole su 30 a 1500,
  102–108 su 70 a 1900.
- La regola 12 chiede di segnalare in `notes` i punteggi incoerenti. Il modello li commentava con le cifre e le note
  venivano rimosse (V03, OQ-M1c-10).

**Decisione dell'utente:** alzare il budget di S02 e chiedere le note in lettere.
- `section_budget.yaml`, peso di S02: 1500 da 0,06 a 0,12, 1900 da 0,05 a 0,08, 2400 da 0,06 a 0,10.
- `prose_words` aumenta di pari passo (1200_1600 590, 1600_2000 1600, ge2400 720), così le altre sezioni tengono
  il loro budget.
- La regola 12 del prompt aggiunge: «Anche nelle notes valgono le regole del testo libero: niente token, mosse o
  cifre; i numeri in lettere».
- Nei fewshot S02 è allungata con le note della tabella T4.

## M4 — Calibrazione e modalità

### OQ-M4-1 · Titoli delle sezioni riammesse dal dettaglio 5
**Problema.** §8.2-bis esclude S05 e S10 all'ancora 2400 «salvo dettaglio 5», ma i loro titoli a 2400 sono `null`
(Appendice D.6), e un titolo nullo significa «sezione omessa».
**Default.** `section_titles.yaml` ha due chiavi in più, `S05_detail5` e `S10_detail5`, con i titoli dell'ancora
1900 («Cosa vuole ogni pezzo», «Come ragionare»). S11 all'ancora 1500 resta esclusa anche col dettaglio 5:
§8.2-bis non prevede eccezioni e il titolo manca.

### OQ-M4-2 · Dettaglio: sezioni, tabelle, K, E3
**Default** (`thresholds.yaml: detail`, `detail.py`):
- **Sezioni.** Con i dettagli 1–2 restano solo le sezioni obbligatorie (✔) della colonna della matrice; le
  condizionali (◐) sono omesse con motivo `detail`. Col dettaglio 3 si aggiunge S08 (secondo c8). Il 4 è
  invariato. Il 5 aggiunge S11 (c11) e toglie le esclusioni dell'ancora 2400.
- **Tabelle.** T2 c'è solo con i dettagli 4–5 (a 1900 col 5), T3 dal 3.
  - **T4 resta sempre con S02**, anche se §7.2 elenca «solo T1» per i dettagli 1–2: la tabella del radar è il
    contenuto di S02, che la matrice rende obbligatoria.
  - Col dettaglio 5 T4 ha anche la colonna «T (avversario)» e la vista ridotta manda `T_opp` (§5-bis.2, O-5).
- **K effettivo.** `explained_min` (dettagli 1–2), `explained_min + 1` al massimo K (dettaglio 3), K della fascia
  (4–5). Vale per la selezione delle candidate spiegate e per le risposte in modalità avversario.
  - `quiet` e il profilo tattico restano sul K della fascia: sono proprietà della posizione.
- **Linee.** `plies_max` col dettaglio sta tra 2 e 12 (`plies_bounds`).
- **E3.** Sotto `e3_mandatory_from` (2150) si esegue solo con dettaglio ≥ 4 (§7.1). Altrimenti è registrata in
  `omitted_phases` con motivo `detail`.

### OQ-M4-3 · Il critico
§10.2 dice solo «seconda chiamata che cerca incoerenze logiche tra frasi e dati e controlla la corrispondenza
testo↔asserzioni».
**Default** (`llm/critic.py`):
- **Attivazione e modello.** Si attiva con `llm.critic: true` ed è spento per default (Appendice D). Usa lo stesso
  modello della chiamata principale (O-7).
- **Che cosa riceve.** Il testo con i token già risolti, le asserzioni di ogni blocco e la vista ridotta del
  pacchetto.
- **Che cosa consegna.** Con lo strumento `submit_review` consegna `{section, block, kind, explanation}`.
- **Effetto.** Ogni segnalazione marca il blocco «⚠ non verificato», come V06, senza rimuoverlo. Il rapporto conta
  le segnalazioni. Le spiegazioni vanno solo in `verification.json` (testo libero del modello, mai copiato nel
  documento).
- **Errori.** Una chiamata fallita o una risposta non valida è un avviso, mai un errore dell'analisi.

**Prova con il modello di sviluppo.** DeepSeek usa lo strumento correttamente, ma sul fewshot 1900 segnala blocchi
che nella spiegazione stessa definisce «coerenti»:
- prima stesura del prompt: 10 segnalazioni, di cui 4 «coerente» e 2 sbagliate;
- dopo due regole aggiunte (valori sempre dal punto di vista dell'utente; elencare solo i blocchi incoerenti): 5
  segnalazioni, di cui 4 «coerente».

Il critico resta spento: va valutato con il modello di produzione (D-67).

### OQ-M4-4 · Modalità «entrambi»: file e Elo
**Default.**
- **Elo.** Ogni colore ha il suo Elo, `--elo-white` e `--elo-black`, entrambi per default `--elo` (D-16). In ogni
  prospettiva l'Elo dell'altro colore è quello dell'avversario. `--opp-elo` con `--color both` è rifiutato
  (codice 2), come `--elo-white`/`--elo-black` senza `--color both`.
- **File.** Si scrivono `pack_white.json`, `pack_black.json`, `llm_raw_<colore>.json` e
  `verification_<colore>.json`. C'è un solo `analysis.md`: prima il colore al tratto, separato da `---`.
- **Rerun.** `rerun` riconosce la cartella con due pacchetti e rifà entrambe le prospettive.
- **Motori.** Le due esplorazioni usano lo stesso `CachedAnalyzer`, quindi Stockfish analizza ogni nodo una volta
  (AC-20).

### OQ-M4-5 · Elo dai tag PGN
**Default.** Solo nel flusso interattivo, dopo la lettura del PGN.
- Se `WhiteElo` e `BlackElo` sono interi positivi, il programma li propone («Usarli? [s/n]») e chiede sempre la
  scala.
- L'utente prende l'Elo del suo colore, l'avversario l'altro; con «entrambi» valgono per i due colori.
- Gli Elo dei tag valgono per quell'analisi e non entrano nel profilo salvato.
- `analyze` non li usa: la riga di comando è esplicita e non ha domande.

### OQ-M4-6 · AC-12 sulle registrazioni
Il criterio parla di «output». La verifica usa i pacchetti costruiti dalle registrazioni a 1200, 1900 e 2500 FIDE:
- insieme delle sezioni, candidate spiegate e lunghezza massima delle linee vengono dal SectionPlan;
- le parole sono quelle del budget.

Così la differenza viene dal programma e non dal modello. Per il test il gruppo di registrazione `najdorf` ha due
esecuzioni in più (1200, 2500); sono servite solo due ricerche nuove. 1200 FIDE cade nella fascia 1200_1600 (limite
inferiore incluso).

### OQ-M4-7 · Budget delle parole con S11
Come in M1b e M3 (§0.5), `prose_words` di ge2400 sale da 720 a 790, così le sezioni esistenti tengono il loro
budget e S11 (peso 0,10) ne riceve circa settanta parole.

## M5 — Calibrazione dei numeri

### OQ-M5-1 · «50–100 posizioni annotate»: chi annota
**Problema.** §13 non dice chi annota le posizioni. Un'annotazione umana di cento posizioni per cinque fasce non è
disponibile in questo lavoro.
**Default.** L'annotazione è automatica, con Stockfish e Maia-2:
- per ogni posizione, la mossa giocata e le due successive del giocatore, con il loro costo;
- per gli errori (≥ 100 cp), le categorie della confutazione, con gli stessi tag di §5-bis.4.

Le metriche umane di §12.2 (utilità percepita, correttezza concettuale) restano alla validazione degli esempi
(§8-bis.5).

### OQ-M5-2 · Campione
**Default** (`config/calibration.yaml`):
- **Partite.** Rapid valutate di agosto 2026 (il modello di Maia-2 è rapid), lette in streaming dal file `.pgn.zst`
  senza scaricarlo. Giocatori entro 300 punti.
- **Posizioni.** Una posizione per partita, tra la semimossa 16 e la 60, estratta con un seme fisso; 20 posizioni per
  fascia del giocatore al tratto (Elo Lichess → FIDE con la tabella di §3-bis).
- **Dati conservati.** Nessun nome: solo l'ID pubblico della partita, gli Elo e le mosse.
- **Profilo.** L'esplorazione usa il profilo `fast` (circa 75 s per posizione con l'annotazione), perché il profilo
  `deep` avrebbe richiesto una decina di ore.
- **Ricerche dell'annotazione.** Profondità minima 16, tetto di 8 s.
- **Fascia ge2400.** Per riempirla si sono lette 76 mila partite.

### OQ-M5-3 · Regole del fit
**Default.**
- **Obiettivo.** AUC media di 100 − T nel prevedere un errore della categoria.
- **Controllo incrociato.** Due metà, divise per ID. Un valore nuovo si adotta solo se migliora di almeno 0,02 sia
  su tutto il campione sia su ciascuna metà quando è scelto sull'altra.
- **Primo passo (θ, k, w).** Non passa: θ è instabile tra le due metà (× 0,1 contro × 2).
- **Secondo passo (θ fisso, k e w).** Passa in entrambe le metà. Si sceglie la combinazione interna alla griglia con
  la migliore AUC sulla metà peggiore: un ottimo sul bordo è una direzione, non un valore misurato.
- **Risultato.** k × 0,15 e w + 0,15 per tutte le categorie tranne `practical_complexity`.
- **A e L_max.** Si cambiano solo se la copertura della mossa giocata tra le spiegate sale di almeno 10 punti,
  sempre con la migliore di Stockfish tra le spiegate. Nessuna fascia cambia.
- **B.** Nelle partite non c'è una verità per il peso della complessità nella raccomandazione: B non si calibra
  qui.

### OQ-M5-4 · Regressione del prompt
**Default.** `chessanalyst regression` rilancia il modello sui sette pacchetti congelati
(`calibration.yaml: regression`), tre volte ciascuno, perché le risposte variano da un giro all'altro. Scrive
`docs/regression/<data>.json` e un confronto in `.md` con il riepilogo precedente: risposte complete, rimozioni
medie, sezioni fuori budget. Il primo riferimento, a un solo giro, ha mostrato quanto pesa la variabilità: lo
stesso pacchetto passa da completo a 23 rimozioni.

## M6 — UI e v1.0

### OQ-M6-1 · Forma dell'interfaccia
**Problema.** §13 chiede «UI con scacchiera, varianti cliccabili, esportazione» senza dire che forma abbia; §15
dice «UI locale in M6».
**Scelta dell'utente.** Pagina web locale: `chessanalyst ui` apre il browser su un piccolo server su questo
computer. Solo libreria standard (`http.server`) e python-chess, nessuna dipendenza nuova. In rete va solo la
chiamata al modello, come dalla riga di comando.
**Default.**
- **Flusso.** È quello interattivo: posizione (esempio, FEN, PGN con scelta della partita e della mossa),
  impostazioni (colore, Elo, scala, profondità, dettaglio), conferma con la scacchiera (§2-bis.5), analisi con
  l'avanzamento, elenco delle analisi salvate.
- **Profilo.** Si salva dopo la conferma, come nel flusso interattivo.
- **Elo dai tag (§2-bis.4 punto 8).** Si propongono con un pulsante e si chiede sempre la scala.
- **Un'analisi alla volta.** I motori usano tutta la macchina; una seconda richiesta riceve un messaggio.
- **Costanti** in `default.yaml: ui` (porta, apertura del browser, limite della richiesta, intervallo di
  aggiornamento).

### OQ-M6-2 · Sicurezza del server locale
**Default.**
- **Interfaccia.** Il server ascolta solo su 127.0.0.1. L'indirizzo non è configurabile, perché la pagina non ha
  autenticazione.
- **Host.** Si accetta una richiesta solo se l'Host è il server stesso (niente DNS rebinding).
- **POST.** Serve il token della pagina (generato all'avvio, illeggibile da altri siti), un'Origin assente o uguale
  al server, il tipo JSON e un corpo entro `ui.max_request_kb`.
- **File.** Si servono solo `analysis.html`, `analysis.md` e le esportazioni, per nome di cartella confrontato con
  l'elenco della cartella di output, mai per percorso. `pack.json`, `run.log` e le risposte del modello non si
  servono.
- **Intestazioni.** Content-Security-Policy restrittiva, `no-store`, `nosniff`.
- **Log.** Il log non contiene i corpi delle richieste (PGN, nomi).

### OQ-M6-3 · Pagina `analysis.html`
**Problema.** §6 dice «Markdown (poi HTML)» senza dettagli. Gli elenchi dei file di AC-01, AC-15 e AC-34 sono quelli
di M1c.
**Default.**
- **Contenuto.** Lo stesso documento di `analysis.md`: il render Markdown in «modalità collegamento» marca ogni token
  di mossa, linea o nodo con la posizione a cui porta, e un convertitore del sottoinsieme Markdown scrive l'HTML. I
  test confrontano il testo delle due versioni.
- **Scacchiera.** Disegnata nel browser dal FEN, con i pezzi di `chess.svg` (Colin M. L. Burnett, dalla libreria
  python-chess, GPL-3.0+; il credito è sotto la scacchiera). La pagina non scarica nulla e funziona senza rete.
- **Navigazione.** Un clic su una mossa mostra la posizione dopo la mossa, con l'ultima mossa evidenziata. Le
  frecce (anche da tastiera) scorrono la variante. Pulsanti per la posizione analizzata e per girare la scacchiera.
- **Nuovo file `render.json`.** Output finale del modello e informazioni del render, da cui si ricostruiscono la
  pagina e le esportazioni. Gli elenchi dei file dei tre test di accettazione sono estesi con `render.json` e
  `analysis.html`.
- **Errori.** Se la pagina non si può scrivere, l'errore va in `run.log` e l'analisi Markdown resta: la pagina è
  un'aggiunta, non il prodotto.
- **Modalità *entrambi*.** Le due prospettive stanno in una pagina, col colore al tratto per primo.

### OQ-M6-4 · Esportazione
**Default.** `chessanalyst export <cartella> --format html|md|pgn [--to <cartella>]`, file
`<nome della cartella>.<formato>`. Il PGN contiene:
- intestazioni con solo FEN, `SetUp` ed evento: nessun nome, anche se la partita li aveva;
- le candidate elencate (o le risposte, se tocca all'avversario) come varianti, la migliore come linea principale,
  con la valutazione dal punto di vista dell'utente in commento;
- le PV tagliate a `export.pgn_plies` semimosse: quelle del motore arrivano a decine;
- le linee filtrate di §5-bis innestate nella posizione da cui partono, con l'ID (`L4: confutazione di …`) e la
  valutazione finale.

Le linee di minaccia partono da una mossa nulla, che molti programmi non leggono nel PGN: si omettono (sono nella
pagina e nel documento). Un'analisi precedente a M6 non ha `render.json`: l'HTML si rifiuta con l'indicazione di
usare `rerun`, Markdown e PGN funzionano.

### OQ-M6-5 · Ottimizzazione dei costi
**Default.**
- **Misura.** Il rapporto finale (riga «Uso del modello»), `verification.json` e la regressione riportano chiamate,
  token in ingresso (e in cache), token in uscita e costo. OpenRouter dà il costo nella risposta. Con Anthropic il
  costo si calcola solo se `llm.prices` è configurato (non si inventano prezzi).
- **Cache.** Due punti di cache nel primo messaggio: l'esempio, comune a tutti i pacchetti della stessa ancora, e
  l'intero messaggio, riletto da ogni retry. Valgono per i modelli Anthropic. I modelli che non usano
  `cache_control` ricevono lo stesso testo.
- **Che cosa pesa.** I token in uscita e i retry (ogni retry rimanda la conversazione). Non si riducono né
  `max_retries` né i budget delle sezioni: inciderebbero sulla qualità. Le misure sono in `docs/M6_REPORT.md`.

### OQ-M6-6 · Versione 1.0.0
**Default.**
- **Versione.** `pyproject.toml` e `chessanalyst.__version__` sono a 1.0.0; i nuovi pacchetti lo riportano in
  `app_version`.
- **Pacchetti golden.** Restano quelli congelati, con `app_version` 0.1.0: i fewshot sono scritti su di essi (D-49).
- **Tag git.** Non si crea senza il via dell'utente.

## Dopo v1.0 — banco di prova

### OQ-BENCH · Banco di prova e traguardo di uscita (decisione dell'utente)
- **Problema.** Le analisi sono poco utili e a volte false (caso reale `fixtures/user_cases/e4_wins_w_1700`). La
  regressione (§12.2) conta errori e retry ma non dice se l'analisi racconta le cose giuste: serve un banco di
  prova che misuri il contenuto, prima di cambiare scaletta, prompt o modello.
- **Banco.** `fixtures/bench/<id>.yaml`: posizione (FEN, colore, Elo 1700 FIDE), bande attese di N1 (`verdict`),
  da due a quattro punti chiave (`must_say`) e parole vietate nel verdetto (`must_not`). Un punto chiave è un
  elenco di termini che devono comparire nella stessa sezione: `ref` (un ID citato in un token: `R5`, `R1.u3`,
  `C1`), `move` (una mossa citata con qualunque token, per ID o `SAN@N`, eventualmente nella casa `node`) o
  `text` (parole, per i concetti posizionali senza un ID: «isolato» con «e3»). Accanto, il pacchetto congelato
  (`<id>.pack.json`, o `pack:`); `chessanalyst bench --freeze` costruisce con i motori quelli che mancano
  (`calibration.yaml: bench.freeze`, profilo standard e dettaglio 5 come il caso reale). Le sei posizioni sono il
  caso reale e le cinque fornite dall'utente.
- **Misura.** `chessanalyst bench [--model X] [--runs N]` rilancia solo modello, verifica e render sui pacchetti
  congelati e scrive `docs/bench/<data>.json` e `….md` con il confronto col giro precedente. Per ogni giro:
  verdetto corretto (asserzione `eval_band` su N1 con una banda attesa nella sezione del verdetto del documento
  finale, e nessuna parola di `must_not`), punti chiave presenti, errori V12 nell'ultimo tentativo, analisi
  completa (ultimo tentativo senza errori), parole, costo, token in ingresso e tempo.
- **Traguardo di uscita** (`calibration.yaml: bench.goal`). Su **tutte** le posizioni, in almeno **4 giri su 5**:
  verdetto corretto, tutti i punti chiave, zero frasi false finali (V12) e analisi completa; **costo medio per
  analisi sotto 0,01 $**. Quando il traguardo è raggiunto ci si ferma: niente ritocchi oltre.
- **Regola di lavoro.** Ogni modifica si misura col banco prima e dopo, con almeno 3 giri; i numeri vanno in
  `docs/bench/`. Una modifica che non migliora il banco si toglie.
- **Limiti noti.** I punti chiave si riconoscono dai token citati e da parole chiave, non dal senso della frase:
  «R1.u3 perde» conta come presente se R1.u3 è citata. Le frasi false le trova V12; le altre restano un limite
  del banco.
- **Bande (decisione dell'utente, 5 ottobre 2026).** Le soglie di `wording.yaml: eval_bands` restano invariate. Nel
  banco il verdetto atteso è la banda di N1 del pacchetto: «vantaggio netto» a +1,71 (`knight_a4_w_1700`) e
  «vantaggio minimo» a +0,48 (`bogo_c5_w_1700`) sono corretti, quindi i due divieti in contrasto
  («netto vantaggio», «vantaggio») non sono in `must_not`.
- **Fase C, documento per punti chiave (D-72, 5 ottobre 2026).** Banco con `--document keypoints`, 3 giri per
  posizione (`docs/bench/20261005T183048`, `…185243`, `…190331`): giri superati 2, poi 9, poi 12 su 18 (con la
  scaletta v0.9.1: 1 su 18, `…171407`); token in ingresso medi da circa 93 000 a circa 14 000; costo medio da
  0,0094 $ a 0,0018 $; parole da circa 1 980 a circa 460; V12 finali a zero in tutti i giri dell'ultimo banco.
  Una chiamata per sezione in parallelo (`…191009`) è più veloce (circa 21 s contro 32) ma peggiore (4 su 18,
  0,0022 $): scartata e tolta dal codice.
- **Correzione del banco.** Il termine «scacch» di `rook_checks_b_1700` non riconosceva «scacco» (la frase
  dell'utente dice «dare scacco»): ora è `scacc(?:o|hi)`. Nel banco «completa» vuol dire ultimo tentativo senza
  errori, compresi gli sforamenti del budget di parole (V07 d): nell'ultimo banco 3 dei 6 giri non superati
  hanno solo quello, un quarto anche un punto chiave mancante; gli altri due mancano «colonna c inutile».
