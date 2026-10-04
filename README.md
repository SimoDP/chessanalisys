# Chess Position Analyst

App locale che, data una posizione e un livello Elo, produce un'analisi testuale calibrata sul livello.
Fonte di verità: [`docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md`](docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md).

**Stato: milestone M3 (Category Scoring Engine).** Radar delle categorie (S02, tabella T4) con tranquillità T
e rilevanza R, linee del motore filtrate da Maia-2 per Elo e «Minacce invisibili al tuo livello» (S09), feature
«M3» (§5-bis). Da M2: Stockfish 19 (D-66), move order E3 fino a ℓ3, tablebase Syzygy, aperture per sequenza,
matrice completa delle sezioni (S12 finale, S13 tattica forzata). Disponibili il flusso interattivo `chessanalyst` e
`chessanalyst analyze` (motori → `pack.json` → modello, verifica e render → `analysis.md`),
`chessanalyst rerun <cartella>`, `chessanalyst doctor`, `chessanalyst golden --data/--packs/--render`.
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
.venv/bin/chessanalyst                                    # flusso interattivo
.venv/bin/chessanalyst analyze --yes --elo 1900           # posizione d'esempio
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --at 17b --budget fast --yes
```

Rapporti: `docs/M0_REPORT.md`, `docs/M1A_REPORT.md`, `docs/M1B_REPORT.md`, `docs/M1C_REPORT.md`,
`docs/M2_REPORT.md`, `docs/M3_REPORT.md`; questioni aperte: `docs/OPEN_QUESTIONS.md`.
Registrazioni dei motori per i test: `pytest -m engines --record` (solo le risposte di Maia-2 che mancano:
`CHESSANALYST_RECORD_MAIA_ONLY=1 pytest -m engines --record`); risposte difettose del modello
(Appendice G.6): `python -m tests.fault_fixtures`.
