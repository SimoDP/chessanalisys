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

### OQ-M0-2 · Versione di Stockfish fissata a 16

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

### OQ-M1a-13 · Costanti numeriche rimaste nel codice
La regola è «nessuna costante numerica nel codice» (istruzione 5). Restano nel codice solo valori che la
documentazione fissa nel testo normativo e che l'Appendice D non mette in configurazione: `loss_cp ≤ 30`
della condizione c3 (§8.2, matrice fissa per §0.5), la soglia `p ≥ 0,001` della policy nei nodi (§6.2),
i 40 caratteri dello slug della cartella (§2-bis.5), le soglie di AC-09 (0,25 pedoni, prime 6) e i limiti di
formato della scacchiera (colonne c–f, ali). Se si preferisce averli in `config/`, va aggiunta una chiave
all'Appendice D: è una decisione dell'utente.

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
