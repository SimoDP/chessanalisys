# Rapporto della milestone M1a — Pacchetto

Contenuto (§13): ingresso, conferma, codici di uscita, rifiuto delle opzioni non disponibili, conversione Elo,
esplorazione E0–E4 con E2b ed E2c (E3 solo ℓ1), selezione, feature «M1», profilo e `matrix_column`,
classificazione, `complexity` e raccomandazione, mossa di contesto, modalità avversario, ID canonici,
tabelle, SectionPlan, `pack.json`. **Nessuna chiamata al modello.**

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-02 | Superato: le 12 FEN dell'Appendice G.2 danno il messaggio atteso; nessun ritorno all'esempio; codice 3 | `test_ac02_invalid_fen.py` |
| AC-03 | Superato: casi PGN dell'Appendice G.3 (testo e file, BOM, `--game`, `[SetUp]`, annotazioni, mossa illegale, matto, `--at`/`--ply`, contraddizione col metodo, formato non riconosciuto) | `test_ac03_pgn.py` |
| AC-11 | Superato sulle registrazioni (1500, 1900, 2400; avversario al tratto) | `test_ac11_explained_count.py` |
| AC-14 | Superato: seconda esecuzione senza chiamate a Stockfish né a Maia-2 e stesso `pack.json`; un profilo più leggero riusa i risultati di `deep` | `test_ac14_cache.py`, `tests/engines/test_cache.py` |
| AC-18 (pacchetto) | Superato: a 1900 e 2400 confidenza bassa, `p_up` nullo, nessun `improbable_error`, nota sotto T1, `maia_low_confidence` su S06 e S08; a 1500 `p_up` calcolato (fascia «top») | `test_ac18_maia_saturation.py` |
| AC-21 (pacchetto) | Superato: `R<n>` e `R<n>.u<k>`, nessuna raccomandazione, S03 e S08 omesse con `opponent_to_move`, E2b ed E3 in `omitted_phases`, fase R, titolo e T1 alternativi | `test_ac21_opponent_to_move.py` |
| AC-22 | Superato: `--color both`, `--detail` ≠ 4, `--elo-white`, `--elo-black`, `--elo-scale chesscom` → messaggio e codice 2 | `test_ac22_unavailable_options.py` |
| AC-24 | Superato: 5,4; −11,4; −19,6; parità entro 5 punti; nessuna candidabile → C1 | `test_ac24_recommendation.py` |
| AC-25 | Superato: posizioni dell'Appendice G.1 e feature della Najdorf (radice e dopo `6.Be3 e5 7.Nb3`) | `test_ac25_profile.py` |
| AC-26 | Superato: ancore 1500, 1900, 2400, utente Bianco e Nero, avversario al tratto, colonne non supportate | `test_ac26_section_plan.py` |
| AC-30 | Superato: valori di §3-bis e confini | `test_ac30_elo.py` |
| AC-31 | Superato: tutti i casi elencati | `test_ac31_selection.py` |
| AC-32 (sintetico) | Superato: sceglie `...Nc6` (costi 8, 53, 10 → `spread` 45), soglia 30 rispettata, E2c | `test_ac32_context_move.py` |
| AC-33 | Superato: tetto di nodi e scadenza nell'ordine di §3-ter.2, riuso di E3-ℓ1 in E2b, `complexity_partial` | `test_ac33_planning.py` |
| AC-34 | Superato: codici 0, 1, 2, 3, 4 e precedenza riga di comando > `profile.yaml` > `local.yaml` > `default.yaml` | `test_ac34_exit_codes_config.py` |

Suite: `pytest` → 191 test in circa 20 s, senza motori né rete; `pytest -m engines` → 4 test con Stockfish e
Maia-2 veri superati (più la registrazione, che parte solo con `--record`).

## Registrazioni dei motori (Appendice G)

`pytest -m engines --record` ha prodotto `fixtures/recorded/engine/` e `fixtures/recorded/maia/` (200 KB):
Najdorf con utente Bianco a 1500, 1900 e 2400 FIDE (profilo `deep`, E3 a ℓ1) e `najdorf_after_be3`
(avversario al tratto), in circa 18 minuti, nessun nodo instabile.

## Che cosa dice il pacchetto sulla posizione d'esempio (registrazioni)

| Ancora | Candidate spiegate | Raccomandata | Sezioni |
| --- | --- | --- | --- |
| 1500 | 6.f3, 6.Be3, 6.Bg5 | 6.f3 (debole: posizione quieta, nessuna mossa unica) | S01 S03 S05 S06 S07 S08 S10 |
| 1900 | 6.f3, 6.Be3, 6.h3, 6.Bd3, 6.Bg5 | 6.f3 (debole) | S01 S03 S04 S05 S06 S07 S08 S10 |
| 2400 | come 1900 | 6.f3 (debole) | S01 S03 S06 S07 S08 |

6.Bg5 entra a tutti i livelli perché è la mossa più probabile per Maia-2 (29–32%), anche se è decima per
valutazione (D-42, D-63). La mossa di contesto scelta dall'algoritmo è `...e5` (non `...Nc6` come nel raw):
con le candidate selezionate dalla pipeline i sistemi confrontati sono diversi da quelli del raw, come
prevede la nota di AC-32; la verifica su `...Nc6` con i nodi registrati è in M2.

## Uso

```bash
.venv/bin/chessanalyst                                   # flusso interattivo
.venv/bin/chessanalyst analyze --yes --elo 1900          # esempio, profilo dalla configurazione
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --at 17b --budget fast --yes
```

Il risultato è `output/<data>_<apertura>/pack.json` con `run.log` (e `game.pgn` per un PGN). Il testo
dell'analisi arriva con M1b (verifica e render) e M1c (modello).

## Scelte annotate

Vedi `docs/OPEN_QUESTIONS.md`, sezione M1a (OQ-M1a-1…12).
