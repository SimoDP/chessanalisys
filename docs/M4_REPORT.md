# Rapporto della milestone M4 — Calibrazione e modalità

Contenuto (§13):
- dettaglio 1–5;
- S11;
- modalità *entrambi*;
- Elo dai tag PGN;
- critico opzionale.

Criteri di uscita: AC-12, AC-20.

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-12 | Superato. Sulla Najdorf a 1200, 1900 e 2500 FIDE, dalle registrazioni, ogni coppia differisce per almeno due caratteristiche. 1200 → 1900: sezioni, candidate spiegate (3 → 5), linee (4 → 8 semimosse), parole (580 → 1600). 1900 → 2500: sezioni (S11, S05 e S10 escluse), linee (8 → 12), parole (1600 → 790) | `tests/acceptance/test_ac12_calibration.py` |
| AC-20 | Superato. Con le due prospettive sulla stessa cache Stockfish analizza ogni nodo una volta: il motore sintetico conta le ricerche e nessuna chiave si ripete. Un solo `analysis.md` con prima il colore al tratto, due pacchetti, `rerun` delle due prospettive | `tests/acceptance/test_ac20_both.py` |

Criteri delle milestone precedenti aggiornati a M4:
- AC-22: le opzioni di M4 ora sono accettate. Restano rifiutati la scala chess.com, i dettagli fuori da 1–5 e le
  combinazioni non valide, sempre con codice 2.
- AC-26: dettaglio 1–5 e S11.
- AC-10: S11 a 2400.

**Suite:** `pytest` → 615 superati, nessun fallito, 2 avvisi `ChecklistQualityWarning` (come in M3).

## Che cosa c'è

- **Dettaglio 1–5** (§7.2, OQ-M4-2): il dettaglio cambia queste cose, scritte in `thresholds.yaml: detail`:
  - K effettivo;
  - linee (2–12 semimosse);
  - parole (× 0,35 … × 1,4);
  - sezioni: 1–2 solo le obbligatorie, 3 anche S08, 5 anche S11 e le sezioni escluse a 2400;
  - tabelle: T2 dal 4, T3 dal 3, T4 sempre con S02;
  - T dell'avversario col dettaglio 5;
  - E3 sotto 2150 solo col dettaglio ≥ 4.

  Disponibile con `--detail` e nel flusso interattivo («Dettaglio [1-5, 4]»), salvato nel profilo.
- **S11** «Note da maestro» (c11: Elo ≥ 2000 o dettaglio 5). Il fewshot 2400 ha S11 scritta ex novo
  (`needs_review`):
  - 6.f3 e 6.Be3 traspongono, ma 6.Be3 concede ...Ng4;
  - dopo 6.f3 e5 regge solo 7.Nb3;
  - 6.Be2 e 6.h3 sono scelte di repertorio.

  `prose_words` di ge2400 sale a 790 (OQ-M4-7).
- **Entrambi** (§2-bis.6, D-16, OQ-M4-4):
  - opzioni `--color both`, `--elo-white` e `--elo-black`, oppure «entrambi» nel flusso interattivo con un Elo
    per colore;
  - due analisi indipendenti sulla stessa cache;
  - un solo `analysis.md`, più i file per colore (`pack_white.json`, …).

  Provato anche con motori e modello reali (profilo `fast`, dettaglio 3, Elo 1900/1600): circa 100 secondi per
  le due prospettive.
- **Elo dai tag PGN** (§2-bis.4 punto 8, OQ-M4-5): nel flusso interattivo `WhiteElo`/`BlackElo` vengono proposti
  con conferma, chiedendo la scala. Valgono per quell'analisi e non entrano nel profilo.
- **Critico** (§10.2, OQ-M4-3): `llm.critic: true` attiva una seconda chiamata con lo strumento `submit_review`.
  Ogni segnalazione marca il blocco «⚠ non verificato», le spiegazioni restano in `verification.json` e un errore
  del critico è solo un avviso. È spento per default.

## Registrazioni

- Il gruppo `najdorf` ha due esecuzioni in più (1200 e 2500 FIDE) per AC-12. In modalità «estensione» sono servite
  solo due ricerche nuove di Stockfish.
- I pacchetti congelati non cambiano, salvo il 2400: S11 ora è richiesta.
- Risposta di DeepSeek sul pacchetto 2400 registrata di nuovo: degradata, con 3 rimozioni (una nota con cifre e due
  paragrafi «engine» senza dati).

## Il critico con il modello di sviluppo

Prova reale sul fewshot 1900, un'analisi valida:
- con la prima stesura del prompt DeepSeek dava 10 segnalazioni: 4 si definivano «coerenti» nella spiegazione
  stessa e 2 erano sbagliate (un conteggio corretto e il segno di una valutazione, che è sempre dal punto di vista
  dell'utente);
- con due regole in più nel prompt del critico le segnalazioni sono scese a 5, di cui ancora 4 «coerenti».

Con DeepSeek il critico marcherebbe come non verificati soprattutto blocchi corretti. Per questo resta spento, e va
rivalutato quando si sceglierà il modello di produzione (D-67). La risposta reale è registrata
(`real_critic_najdorf_w_1900.json`) e un test la rigioca.

## Stato

**M4 chiusa.** AC-12 e AC-20 sono superati e tutte le funzioni di M4 ci sono, con test. Restano:
- il critico da valutare con il modello di produzione;
- i fewshot da validare (§8-bis.5), ora anche S11 a 2400;
- la calibrazione dei numeri, che è M5.

## Uso

```bash
.venv/bin/chessanalyst analyze --yes --color both --elo-white 1900 --elo-black 1600   # due prospettive, un file
.venv/bin/chessanalyst analyze --yes --elo 2200 --detail 5                            # S11, T avversario, linee più lunghe
.venv/bin/chessanalyst analyze --yes --elo 1500 --detail 1                            # solo le sezioni obbligatorie
.venv/bin/chessanalyst                                                                # flusso interattivo (Elo dai tag PGN)
```

Per attivare il critico: `llm: {critic: true}` in `config/local.yaml`. Scelte e default: `docs/OPEN_QUESTIONS.md`
(OQ-M4-1…7).
