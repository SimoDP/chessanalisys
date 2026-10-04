# Questioni aperte

Formato: problema, prova, proposta o default adottato. Nessuna voce riapre D-01…D-63 né tocca architettura,
schema, token o criteri di accettazione.

## M0

### OQ-M0-1 · Rete dell'ambiente cloud: pesi di Maia-2 e Syzygy non scaricabili

- **Problema.** M0 è stato eseguito in una sessione cloud la cui politica di rete blocca `drive.google.com`
  (pesi di Maia-2), `tablebase.lichess.ovh` (Syzygy) e i download delle release su `github.com`.
- **Prova.** `scripts/setup_engines.py --yes`: «Tunnel connection failed: 403 Forbidden» per i tre host;
  `raw.githubusercontent.com` (aperture) e PyPI sono raggiungibili.
- **Effetto.** Non sono stati prodotti `fixtures/golden_maia.json` né la misura dei tempi di Maia-2; i test
  di §3.2 sul modello vero (`pytest -m engines`) si saltano; `doctor` riporta `ERRORE` su Maia-2 e `AVVISO`
  su Syzygy. Tutto il codice relativo è scritto e testato con i fake.
- **Proposta.** Sulla macchina dell'utente (o abilitando i tre host nell'ambiente cloud):
  `python scripts/setup_engines.py`, `chessanalyst doctor`, `pytest -m engines`,
  `chessanalyst golden --data --reuse-nodes`. Nessuna modifica di progetto.

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

- **Problema.** Da PyPI `torch` 2.8 su Linux è la build CUDA (pacchetti `nvidia-*`, diversi GB); l'indice
  CPU di `download.pytorch.org` era bloccato. `requirements.lock` riflette quindi la build CUDA.
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
