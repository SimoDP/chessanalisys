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
