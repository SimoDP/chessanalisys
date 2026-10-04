# Rapporto della milestone M0 — Fondamenta e dati

Criteri di uscita (§13): AC-09, AC-19, AC-29 e checklist dell'Appendice B.

## Criteri di accettazione

| AC | Esito | Dove |
| --- | --- | --- |
| AC-09 | **Superato**: 6.Be3 +0,32 (raw +0,37), 6.f3 +0,38 (+0,37), 6.h3 +0,32 (+0,35); ranghi 3, 1, 2 | `docs/golden_diff.md`, `tests/acceptance/test_ac09_golden.py` |
| AC-19 | **Superato** (motore mancante, versione ≠ pin, chiave API assente, dispositivo, tabella `elo_maia`/`saturated`) | `tests/acceptance/test_ac19_doctor.py` |
| AC-29 | **Superato** con `FakeUCI` (arresto per tempo e profondità, tetto con `unstable_depth`, righe `lowerbound`/`upperbound` ignorate, istantanea solo su iterazione completa) | `tests/acceptance/test_ac29_analysis_primitive.py` |

Suite: `pytest` → 69 test senza motori né rete; `pytest -m engines` → 2 test con Stockfish vero superati,
2 test con Maia-2 vero saltati (pesi assenti, vedi sotto).

## Checklist dell'Appendice B

| # | Voce | Stato |
| --- | --- | --- |
| 1 | Repository, `pyproject.toml`, `config/` dall'Appendice D, caricamento e validazione | Fatto. Unica modifica ai valori: i `version_pin` e `reference_time_s` (§0.5) |
| 2 | `setup_engines.py` e `doctor` verdi | Parziale: verdi Stockfish, aperture (3864 posizioni), cartelle, benchmark. **Maia-2 e Syzygy non scaricabili** in questo ambiente (OQ-M0-1); chiave API assente (serve da M1c) |
| 3 | `docs/MAIA2_NOTES.md` | Fatto sul codice di `maia2` 0.11.0; **mancano** i test sul modello vero e i tempi per posizione (OQ-M0-1) |
| 4 | `config/maia2_limits.yaml` reale + tabella per ancore | Fatto: i valori del codice coincidono con il segnaposto; tabella in `MAIA2_NOTES.md` e in `doctor` |
| 5 | Primitiva §3.1.3 con `FakeUCI` e verifica dell'API reale di `engine.analysis()` | Fatto (`chess` 1.11.2, Stockfish 16) |
| 6 | Copia dei quattro raw in `examples/golden/raw/` | Fatto |
| 7 | `golden --data` → `golden_nodes.json`, `golden_maia.json`, `golden_diff.md` | `golden_nodes.json` e `golden_diff.md` fatti (14 nodi, profilo `deep`, tempi normativi); **`golden_maia.json` mancante** (OQ-M0-1) |
| 8 | AC-09 | Superato senza modificare le profondità di `deep` |
| 9 | Misura dei tempi, aggiornamento di `exploration.yaml` | `reference_time_s: 7.9`. Con `deep` tutti i nodi hanno superato la profondità minima entro `t_target` (radice 29 contro 20, nodi 22–25 contro 18): `B`, profondità e nodi restano invariati |
| 10 | `version_pin` e `requirements.lock` | `Stockfish 16` (OQ-M0-2), `maia2` `0.11.0`; lock con Python 3.12 |
| 11 | `docs/CALIBRATION_GUIDE.md` | Fatto (generato da `golden --data`) |
| 12 | `docs/OPEN_QUESTIONS.md` | Fatto (OQ-M0-1…8) |

## Risultati dei dati golden in sintesi

- 49 dei 51 valori numerici dei raw sono entro 0,25 pedoni. Oltre la soglia: `6.Be3 e6 7.g4` (raw +0,40,
  ora 0,00 con ricerca ristretta) e `6.Bg5 e6 7.f4 h6` (raw +0,20, ora +0,48).
- Cambia la migliore in quattro nodi, sempre fra mosse vicine: dopo `6.Be3` ora `...e5` (+0,34) davanti a
  `...Ng4` (+0,39); dopo `6.Be3 e5 7.Nb3 Be6` `8.Qd2` (+0,31) a pari merito con `8.h3`; dopo `6.Be2 e5 7.Nb3`
  `...Be6` (+0,25) davanti a `...Be7` (+0,26); dopo `6.f4 e5 7.Nb3` `...Nc6` (+0,02) davanti a `...Nbd7`
  (+0,22). Quest'ultimo cambia il costo di `...Nc6` contro `6.f4` (≈ 0 resta vero) e va tenuto presente
  nei fewshot di M1b, che usano comunque i pacchetti congelati e non i numeri dei raw.
- Le parole di prosa misurate sui raw sono molto sotto `prose_words` (1500: 319 contro 650; 1900: 654
  contro 1400; 2400: 228 contro 800). È una prima stima: la misura che conta è quella dei fewshot in M1b (§0.5).

## Da completare sulla macchina dell'utente

```bash
.venv/bin/python scripts/setup_engines.py          # pesi di Maia-2 e Syzygy 3-4-5
.venv/bin/chessanalyst doctor                      # deve risultare senza ERRORE
.venv/bin/pytest -m engines                        # test di §3.2 sul modello vero
.venv/bin/chessanalyst golden --data --reuse-nodes # produce fixtures/golden_maia.json
```

Poi aggiornare in `docs/MAIA2_NOTES.md` i tempi di Maia-2 per posizione.
