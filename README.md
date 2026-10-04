# Chess Position Analyst

App locale che, data una posizione e un livello Elo, produce un'analisi testuale calibrata sul livello.
Fonte di verità: [`docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md`](docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md).

**Stato: milestone M0 (fondamenta e dati).** Disponibili `chessanalyst doctor` e `chessanalyst golden --data`;
gli altri comandi rispondono «disponibile da M1…» con codice di uscita 2.

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

Stato di M0 e problemi aperti: `docs/M0_REPORT.md`, `docs/OPEN_QUESTIONS.md`.
