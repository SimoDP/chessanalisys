# Chess Position Analyst

App locale che, data una posizione e un livello Elo, produce un'analisi testuale calibrata sul livello.
Fonte di verità: [`docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md`](docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md).

**Stato: v1.0 (milestone M6).** Interfaccia nel browser (`chessanalyst ui`), pagina `analysis.html` con mosse e
varianti cliccabili su una scacchiera, esportazione in HTML, Markdown e PGN (`chessanalyst export`), uso e costo del
modello nel rapporto di ogni analisi. Da M5: costanti della tranquillità T calibrate su partite di Lichess
(`docs/CALIBRATION_REPORT.md`), `chessanalyst calibrate` e `chessanalyst regression`. Da M4: dettaglio 1–5,
modalità *entrambi* (due prospettive in un solo documento), «Note da maestro», Elo dai tag PGN, critico opzionale.
Da M3: radar delle categorie e «Minacce invisibili al tuo livello». Da M2: Stockfish 19, tablebase Syzygy, aperture
per sequenza, matrice completa delle sezioni. Note di rilascio: [`docs/RELEASE_NOTES_v1.0.md`](docs/RELEASE_NOTES_v1.0.md).
Serve la chiave API del fornitore del modello: per default OpenRouter, variabile d'ambiente
`OPENROUTER_API_KEY` (oppure Anthropic con `ANTHROPIC_API_KEY`, D-64); mai scritta su disco.
Decisioni prese dopo il congelamento della documentazione: `docs/DECISIONI_POST_CONGELAMENTO.md`.

## Installazione

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"          # oppure: pip install -r requirements.lock
.venv/bin/python scripts/setup_engines.py  # Stockfish 19, pesi di Maia-2, Syzygy 3-4-5, aperture
.venv/bin/chessanalyst doctor
```

## Test

```bash
.venv/bin/pytest                 # senza motori né rete
.venv/bin/pytest -m engines      # con Stockfish (e Maia-2) veri
.venv/bin/pytest -m llm --record # registra risposte del modello reale (serve la chiave API)
```

## Uso

```bash
.venv/bin/chessanalyst ui                                 # nel browser, su questo computer (127.0.0.1)
.venv/bin/chessanalyst                                    # flusso interattivo nel terminale
.venv/bin/chessanalyst analyze --yes --elo 1900           # posizione d'esempio
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --at 17b --budget fast --yes
.venv/bin/chessanalyst analyze --yes --color both --elo-white 1900 --elo-black 1600 --detail 3
.venv/bin/chessanalyst export output/<cartella> --format pgn   # oppure html, md
```

Ogni analisi è una cartella in `output/`:
- `analysis.md`, il documento;
- `analysis.html`, lo stesso documento con la scacchiera: un clic su una mossa mostra la posizione, le frecce
  scorrono la variante. La pagina funziona senza rete.
- `pack.json` (i dati dei motori), `llm_raw.json` e `verification.json` (risposte e controlli del modello),
  `render.json` e `run.log`.

Rapporti: `docs/M0_REPORT.md`, `docs/M1A_REPORT.md`, `docs/M1B_REPORT.md`, `docs/M1C_REPORT.md`,
`docs/M2_REPORT.md`, `docs/M3_REPORT.md`, `docs/M4_REPORT.md`, `docs/M5_REPORT.md`,
`docs/M6_REPORT.md`; questioni aperte: `docs/OPEN_QUESTIONS.md`.
Registrazioni dei motori per i test: `pytest -m engines --record` (solo le risposte di Maia-2 che mancano:
`CHESSANALYST_RECORD_MAIA_ONLY=1 pytest -m engines --record`); risposte difettose del modello
(Appendice G.6): `python -m tests.fault_fixtures`.
