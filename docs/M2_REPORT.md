# Rapporto della milestone M2 — Completezza delle posizioni

Contenuto (§13):
- E3 ai livelli ℓ2–ℓ3;
- Syzygy, dentro Stockfish e con sonda diretta;
- aperture per sequenza;
- matrice completa, con S12 e S13;
- pacchetti e fewshot 1900/2400 completati;
- 2 fixture non-Najdorf con checklist.

Con D-66 si passa a Stockfish 19 e si rifanno registrazioni, pacchetti e fewshot.

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-10 (2400) | Superato sul `rendered` e sulla risposta registrata del modello reale. Sezioni S01, S03 (con S04 assorbita), S06, S07 (T1 + T2); S05 e S10 omesse (`band_2400`), S08 omessa per c8 (`no_classified_move`) | `test_ac10_najdorf_sections.py` |
| AC-13 | Superato: nelle risposte registrate su Fried Liver, finale di torri e Lucena nessun termine di `_terms.txt` | `test_ac13_contamination.py` |
| AC-17 | Superato su Lucena (5 pezzi). Il pacchetto ha `tablebase: {wdl: 2, dtz: 15, result_text_key: win}`, colonna 4, S12 con `must_cover: [N1]`. S12 riporta l'esito esatto a parole («vittoria teorica per te»); nel documento non c'è alcuna valutazione in pedoni né conteggio di matti (OQ-M2-4) | `test_ac17_tablebase_endgame.py` |
| AC-32 (registrato) | Superato sui nodi del raw 1900 in `fixtures/golden_nodes.json` (un nodo di E2 e tre di ℓ2): `...Nc6`, spread 53; soglia rispettata; stesso esito con le regole di D-68 | `test_ac32_context_move.py` |

I criteri delle milestone precedenti restano verdi, compresi AC-01 (esecuzione completa identica al pacchetto
congelato), AC-14 (profilo più leggero dalla cache di `deep`), AC-16 (con il nuovo caso
`bad_tool_arguments.json`) e AC-21.

**Suite:** `pytest` → 527 superati, 3 falliti. I falliti sono i controlli di contenuto delle checklist sulle
risposte di DeepSeek (vedi sotto). `pytest -m engines` → 4 superati, 1 saltato (la registrazione, che parte solo
con `--record`).

## Che cosa è cambiato

- **Stockfish 19** (D-66, OQ-M2-1). Da questa versione i binari sono universali: i nomi dei file sono stati
  verificati sulla pagina ufficiale. Pin `Stockfish 19`, `reference_time_s` 6,0 s (era 7,9 con Stockfish 16).
  `golden_nodes.json` resta il dato di M0 (Stockfish 16), perché riproduce i raw.
- **E3 ℓ2–ℓ3** (D-28). Con `milestone_max_e3_level: 3`, il profilo `standard` arriva a ℓ2 e `deep` a ℓ3. T2 ha le
  righe di ℓ2 e ℓ3 dopo quella di ℓ1 dello stesso ramo: 33 righe a 2400. T3 considera anche i nodi di ℓ2, con una
  seconda passata di E2c (OQ-M2-2). L'avviso `move_order_limited` vale solo finché la milestone limita i livelli.
- **Mossa di contesto (D-68, decisa dall'utente).** Con i nodi di ℓ2 l'algoritmo congelato sceglieva mosse che
  nessuno gioca, o mosse il cui spread nasce da un solo errore tattico (OQ-M2-8). Ora valgono due regole:
  - le candidate devono avere `p_opp` medio ≥ 3%;
  - una riga con costo ≥ 150 cp non conta.

  Sulla Najdorf la mossa di contesto diventa il fianchetto `...g6`: non costa nulla contro `6.Bd3`, costa 0,33 e
  0,40 contro `6.f3` e `6.Be3`, e oltre un pedone contro `6.Bg5` e dopo `6.f3 e6 7.g4`.
- **Syzygy** (D-62). `SyzygyPath` a Stockfish e sonda diretta (`engines/syzygy.py`). `profile.tablebase` porta
  la colonna 4. Con la tablebase l'esito esatto prevale ed è espresso a parole nei token e nelle tabelle;
  `pct:root.*` dà V02 (OQ-M2-4).
- **Aperture per sequenza** (OQ-M2-3). `data/openings_sequences.json` e ricerca della riga più lunga che è prefisso
  della partita. La Fried Liver da PGN è riconosciuta come «Italian Game: Two Knights Defense, Knight Attack,
  Normal Variation» (`matched_by: sequence`). `doctor` controlla le sequenze.
- **Matrice completa** (§8.2, §8.3). Colonne 2–4, S12 e S13. S05 in colonna 2 dipende da c5, con le
  `focus_squares` dei pezzi coinvolti (OQ-M2-5); l'avviso `profile_unsupported` non c'è più.
- **Verifica.** Argomenti dello strumento non in JSON valido → V01 e retry (OQ-M2-9). Era un bug trovato su
  una risposta reale di DeepSeek ed è diventato un test di fault injection.
- **Determinismo.**
  - La normalizzazione della policy di Maia-2 somma in ordine fisso: la somma dipendeva dal seme di hash di
    Python.
  - La soglia della policy salvata si applica al valore a quattro decimali.

  Tre rigenerazioni dei pacchetti danno file identici.

## Registrazioni e pacchetti

`pytest -m engines --record` (profilo `deep`, tempo pieno) produce `fixtures/recorded/{engine,maia,syzygy}`:

| Gruppo | Esecuzioni | Ricerche |
| --- | --- | --- |
| `najdorf` | 1500, 1900, 2400 (`deep`) + 1900 (`standard`, per AC-14) | 80 |
| `najdorf_after_be3` | 1900 | 5 |
| `fried_liver` (PGN) | 1500 | 30 |
| `rook_endgame` | 1900 | 56 |
| `lucena` | 1900 | 52 |

Il metodo di registrazione è cambiato rispetto a M1a (OQ-M2-7):
- orologio fermo per la sola scadenza globale;
- tutte le ricerche salvate, non solo quelle della cache;
- `FakeEngine` sceglie la migliore che soddisfa la richiesta;
- nel gruppo con più esecuzioni ogni ricerca aspetta la profondità minima, fino alla scadenza del profilo.

Con il metodo di M1a i replay chiedevano nodi mai registrati: servivano tre tentativi di registrazione per
accorgersene. Il comando `CHESSANALYST_RECORD_GROUPS=... CHESSANALYST_RECORD_EXTEND=1` estende un gruppo senza
rifarlo.

Pacchetti congelati (`golden --packs --force --recorded`):

| Pacchetto | Colonna | Candidate spiegate | Raccomandata | Sezioni |
| --- | --- | --- | --- | --- |
| `najdorf_w_1500` | 1 | 6.f3, 6.Be3, 6.Bg5 | 6.f3 (debole) | S01 S03 S05 S06 S07 S08 S10 |
| `najdorf_w_1900` | 1 | 6.f3, 6.Be3, 6.Qd3, 6.Bd3, 6.Bg5 | 6.f3 (debole) | S01 S03 S04 S05 S06 S07 S08 S10 |
| `najdorf_w_2400` | 1 | come 1900 | 6.f3 (debole) | S01 S03 S06 S07 |
| `fried_liver_w_1500` | 2 | 6.d4, 6.Nxf7 | 6.d4 | S01 S03 S05 S06 S07 S08 S10 S13 |
| `rook_endgame_w_1900` | 3 | 1.Rd7, 1.Rd6, 1.Rb1, 1.Rd4, 1.Rd8 (tutte 0,00) | 1.Rd7 (debole) | S01 S06 S07 S08 S10 S12 |
| `lucena_w_1900` | 4 | 1.Rc8+, 1.Rd1+, 1.Rh1, 1.Rc7, 1.Rb1 (tutte vinte) | 1.Rc8+ | S01 S06 S07 S10 S12 |

Lucena ha 31 nodi sotto la profondità minima, segnalati in testata e nel rapporto: con le tablebase alla radice
Stockfish 19 rallenta molto (OQ-M2-7).

## Fewshot

I tre fewshot sono riscritti sui nuovi pacchetti (§8-bis.4 M2); `_s07_alt.json` è riallineato. Tutti superano
V01–V10 e `golden --render` riproduce i `rendered` (AC-27). Che cosa è cambiato è nei `meta.yaml`:
- a 1900 i sistemi sono riscritti (donna in d3, alfiere in d3) e T3 è commentata su `...g6`;
- a 2400 T2 è completa (ℓ1–ℓ3, con note sulle righe critiche, per esempio dopo `6.Be3 Ng4 7.Bg5 h6` regge solo
  `8.Bh4`) e S08 è omessa per c8;
- a 1500 `6.Bg5` è l'alternativa pratica.

I fewshot restano `validated: false` (§8-bis.5).

## Il modello di sviluppo (DeepSeek, D-67)

Risposte registrate con `pytest -m llm --record`: sette pacchetti, tre risposte ciascuno.

| Pacchetto | Errori per tentativo | Esito |
| --- | --- | --- |
| Najdorf 1500 | 1, 2, 0 | completo |
| Najdorf 1900 | 1, 7, 6 | degradata, 1 rimozione |
| Najdorf 2400 | 7, 1, 2 | degradata, 2 rimozioni |
| Najdorf dopo `6.Be3` (AC-21) | 21, 5, 2 | degradata, 1 rimozione |
| Fried Liver 1500 | 11, 5, 5 | degradata, 2 rimozioni |
| Finale di torri 1900 | 26, 14, 13 | degradata, 5 rimozioni |
| Lucena 1900 | 1, 20, 6 | degradata, 2 rimozioni |

Sulle posizioni senza un esempio dello stesso tipo DeepSeek sbaglia di più. L'errore più frequente resta quello
già visto in M1c: cita la mossa nel nodo che si ottiene dopo averla giocata.

**Checklist.** Le tre checklist sono state scritte dai dati del motore prima di leggere le risposte, e nessuna è
soddisfatta per intero:
- Fried Liver: manca l'errore tipico `d3`;
- finale di torri: mancano «torre passiva» e lo scambio delle torri in un finale di pedoni perso;
- Lucena: manca «costruire il ponte».

Sezioni e mosse richieste ci sono sempre. Sono limiti di contenuto del modello di sviluppo, non del programma:
prompt, esempi e checklist non sono stati modificati in attesa della decisione dell'utente.

## Stato

Tutti i criteri di uscita di M2 (AC-10 a 2400, AC-13, AC-17, AC-32 registrato) sono superati. Restano aperti i
controlli di contenuto delle checklist sulle risposte di DeepSeek, che richiedono una decisione dell'utente.

## Uso

```bash
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --budget deep --yes    # apertura per sequenza
.venv/bin/chessanalyst analyze --input fen --text "1K1k4/1P6/8/8/8/8/r7/2R5 w - - 0 1" --yes   # tablebase
.venv/bin/pytest -m engines --record                       # tutte le registrazioni (circa un'ora e mezza)
CHESSANALYST_RECORD_GROUPS=najdorf CHESSANALYST_RECORD_EXTEND=1 .venv/bin/pytest -m engines --record
.venv/bin/chessanalyst golden --packs --force --recorded   # pacchetti congelati dalle registrazioni
```

Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M2-1…9); decisione D-68 in
`docs/DECISIONI_POST_CONGELAMENTO.md`.
