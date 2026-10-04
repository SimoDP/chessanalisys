# Chess Position Analyst

App locale che, data una posizione e un livello Elo, produce un'analisi testuale calibrata sul livello.
Fonte di verità: [`docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md`](docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md).

**Stato: milestone M1a (pacchetto di evidenze).** Disponibili il flusso interattivo `chessanalyst`,
`chessanalyst analyze` (fino a `pack.json`, senza modello di linguaggio), `chessanalyst doctor` e
`chessanalyst golden --data`; `rerun` e `golden --packs/--render` rispondono «disponibile da M1…» con codice 2.

## Installazione

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"          # oppure: pip install -r requirements.lock
.venv/bin/python scripts/setup_engines.py  # Stockfish, pesi di Maia-2, Syzygy 3-4-5, aperture
.venv/bin/chessanalyst doctor
```

## Test

```bash
.venv/bin/pytest                 # senza motori né rete
.venv/bin/pytest -m engines      # con Stockfish (e Maia-2) veri
```

## Uso

```bash
.venv/bin/chessanalyst                                    # flusso interattivo
.venv/bin/chessanalyst analyze --yes --elo 1900           # posizione d'esempio
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --at 17b --budget fast --yes
```

Rapporti: `docs/M0_REPORT.md`, `docs/M1A_REPORT.md`; questioni aperte: `docs/OPEN_QUESTIONS.md`.
Registrazioni dei motori per i test: `pytest -m engines --record`.
