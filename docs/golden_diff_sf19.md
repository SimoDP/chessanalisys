# Golden: confronto tra i raw e Stockfish 19 (D-66)

Stessa procedura di `docs/golden_diff.md` (M0, Stockfish 16), ripetuta dopo il passaggio a Stockfish 19.
I dati sono in `fixtures/golden_nodes_sf19.json` e `fixtures/golden_maia_sf19.json`; `fixtures/golden_nodes.json`
resta il dato di M0 (Stockfish 16), che riproduce i raw ed è usato da AC-32.

Generato da `chessanalyst golden --data` il 2026-10-04T18:11:28+00:00 (app 0.1.0, profilo `deep`, fattore di tempo 1.0).
Motore: Stockfish 19. Valori in pedoni dal punto di vista del Bianco (= utente nei raw).
Soglia di segnalazione: scostamento > 0,25 pedoni (⚠).

## AC-09

Esito: **superato** (le prime 3 candidate dei raw devono differire ≤ 0,25 e restare tra le prime 6).

| Mossa | Raw | Nuovo | Differenza | Rango nuovo | Esito |
| --- | --- | --- | --- | --- | --- |
| 6.Be3 | +0,37 | +0,19 | -0,18 | 3 | OK |
| 6.f3 | +0,37 | +0,19 | -0,18 | 2 | OK |
| 6.h3 | +0,35 | +0,22 | -0,13 | 1 | OK |

## Nodi analizzati

| Nodo | Fase | Profondità | MultiPV | Tempo (s) | Instabile | Migliore |
| --- | --- | --- | --- | --- | --- | --- |
| radice | E0 | 31 | 16 | 270 | no | h3 +0,22 |
| mossa nulla (tratto al Nero) | E1 | 28 | 8 | 72 | no | e5 0,00 |
| 6.Be3 | E2 | 26 | 8 | 59 | no | Ng4 +0,31 |
| 6.Be2 | E2 | 26 | 8 | 59 | no | e5 +0,11 |
| 6.Bg5 | E2 | 24 | 8 | 59 | no | e6 +0,05 |
| 6.f4 | E2 | 26 | 8 | 59 | no | e5 +0,04 |
| 6.Be3 Ng4 | E3 | 24 | 8 | 23 | no | Bg5 +0,37 |
| 6.Be3 e5 7.Nb3 | E3 | 22 | 8 | 23 | no | Be6 +0,24 |
| 6.Be3 e5 7.Nb3 Be6 | E3 | 24 | 8 | 23 | no | f3 +0,24 |
| 6.Be3 e6 | E3 | 22 | 8 | 23 | no | Qe2 +0,32 |
| 6.Bg5 e6 7.f4 | E3 | 22 | 8 | 23 | no | Qb6 +0,09 |
| 6.Be2 e5 7.Nb3 | E3 | 22 | 8 | 23 | no | Be6 +0,13 |
| 6.Be2 e5 7.Nb3 Be7 | E3 | 24 | 8 | 23 | no | h4 +0,16 |
| 6.f4 e5 7.Nb3 | E3 | 24 | 8 | 23 | no | Nc6 0,00 |

WDL alla radice (riga 1): [39, 954, 7] per mille; patta 95% (raw: circa 92%).

## Valori numerici dei raw

| Nodo | Mossa | Raw | Nuovo | Differenza | Fonte del nuovo valore | Raw citati | Nota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radice | Be3 | +0,37 | +0,19 | -0,18 | MultiPV 3 | 1500, 1900, 2400 |  |
| radice | f3 | +0,37 | +0,19 | -0,18 | MultiPV 2 | 1900 |  |
| radice | h3 | +0,35 | +0,22 | -0,13 | MultiPV 1 | 1900 |  |
| radice | Bg5 | +0,29 | +0,10 | -0,19 | MultiPV 7 | 1500, 1900 |  |
| radice | Nb3 | +0,25 | +0,03 | -0,22 | MultiPV 14 | 1900 |  |
| radice | Bd3 | +0,25 | +0,18 | -0,07 | MultiPV 4 | 1900 |  |
| radice | Bc4 | +0,23 | +0,05 | -0,18 | MultiPV 11 | 1500, 1900 |  |
| radice | a4 | +0,23 | +0,07 | -0,16 | MultiPV 9 | 1900 |  |
| radice | g3 | +0,22 | +0,11 | -0,11 | MultiPV 6 | 1900 |  |
| radice | Be2 | +0,22 | +0,16 | -0,06 | MultiPV 5 | 1500, 1900 |  |
| radice | f4 | +0,20 | +0,07 | -0,13 | MultiPV 10 | 1900 |  |
| radice | Rg1 | +0,17 | +0,09 | -0,08 | MultiPV 8 | 1900, 2400 |  |
| mossa nulla (tratto al Nero) | e5 | 0,00 | 0,00 | 0,00 | MultiPV 1 | 1900, 2400 | valore approssimato nel raw (≈ 0,0) |
| 6.Be3 | Ng4 | +0,33 | +0,31 | -0,02 | MultiPV 1 | 1900, 2400 |  |
| 6.Be3 | e5 | +0,35 | +0,31 | -0,04 | MultiPV 2 | 1900, 2400 |  |
| 6.Be3 | Nc6 | +0,41 | +0,48 | +0,07 | MultiPV 5 | 1900, 2400 |  |
| 6.Be3 | e6 | +0,50 | +0,33 | -0,17 | MultiPV 3 | 2400 |  |
| 6.Be3 Ng4 | Bg5 | +0,38 | +0,37 | -0,01 | MultiPV 1 | 2400 |  |
| 6.Be3 Ng4 | Bc1 | +0,36 | +0,27 | -0,09 | MultiPV 2 | 2400 |  |
| 6.Be3 Ng4 | Qd2 | 0,00 | -0,12 | -0,12 | MultiPV 5 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 Ng4 | Qe2 | 0,00 | -0,14 | -0,14 | MultiPV 7 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 Ng4 | Qf3 | 0,00 | -0,10 | -0,10 | MultiPV 3 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 e5 7.Nb3 | Be6 | +0,33 | +0,24 | -0,09 | MultiPV 1 | 1900 |  |
| 6.Be3 e5 7.Nb3 | Nc6 | +0,86 | +0,75 | -0,11 | MultiPV 8 | 1900, 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | h3 | +0,34 | +0,24 | -0,10 | MultiPV 3 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Qd2 | +0,32 | +0,24 | -0,08 | MultiPV 2 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | f3 | +0,28 | +0,24 | -0,04 | MultiPV 1 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Be2 | +0,24 | +0,12 | -0,12 | MultiPV 4 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Qd3 | +0,22 | +0,12 | -0,10 | MultiPV 5 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | a3 | +0,09 | +0,04 | -0,05 | ricerca ristretta (E2c) | 2400 |  |
| 6.Be3 e6 | a3 | +0,49 | +0,31 | -0,18 | MultiPV 2 | 2400 |  |
| 6.Be3 e6 | Be2 | +0,43 | +0,31 | -0,12 | MultiPV 3 | 2400 |  |
| 6.Be3 e6 | f3 | +0,43 | +0,28 | -0,15 | MultiPV 5 | 2400 |  |
| 6.Be3 e6 | Qd2 | +0,42 | +0,29 | -0,13 | MultiPV 4 | 2400 |  |
| 6.Be3 e6 | g4 | +0,40 | +0,22 | -0,18 | MultiPV 6 | 2400 |  |
| 6.Be3 e6 | Qf3 | +0,30 | +0,20 | -0,10 | ricerca ristretta (E2c) | 2400 |  |
| 6.Bg5 e6 7.f4 | Qb6 | +0,13 | +0,09 | -0,04 | MultiPV 1 | 2400 |  |
| 6.Bg5 e6 7.f4 | h6 | +0,20 | +0,31 | +0,11 | MultiPV 3 | 2400 |  |
| 6.Bg5 e6 7.f4 | Nbd7 | +0,38 | +0,31 | -0,07 | MultiPV 2 | 2400 |  |
| 6.Bg5 e6 7.f4 | Be7 | +0,38 | +0,38 | 0,00 | MultiPV 4 | 2400 |  |
| 6.Bg5 e6 7.f4 | b5 | +0,52 | +0,73 | +0,21 | MultiPV 7 | 2400 |  |
| 6.Be2 e5 7.Nb3 | Be7 | +0,24 | +0,13 | -0,11 | MultiPV 2 | 1900 |  |
| 6.Be2 e5 7.Nb3 | Nc6 | +0,34 | +0,27 | -0,07 | MultiPV 3 | 1900, 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | (nodo) | +0,30 | +0,16 | -0,14 | riga 1 | 2400 | valutazione del nodo (D-40) |
| 6.Be2 e5 7.Nb3 Be7 | Be3 | +0,30 | +0,12 | -0,18 | MultiPV 4 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | O-O | +0,30 | +0,13 | -0,17 | MultiPV 2 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | Bf3 | +0,25 | +0,13 | -0,12 | MultiPV 3 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | Qd3 | +0,24 | +0,06 | -0,18 | MultiPV 6 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | h3 | +0,12 | 0,00 | -0,12 | ricerca ristretta (E2c) | 2400 |  |
| 6.f4 e5 7.Nb3 | Nbd7 | +0,06 | +0,13 | +0,07 | MultiPV 2 | 1900, 2400 |  |
| 6.f4 e5 7.Nb3 | Nc6 | +0,09 | 0,00 | -0,09 | MultiPV 1 | 1900, 2400 |  |

Valori oltre la soglia: **0** su 51.

## Mossa migliore per nodo

| Nodo | Migliore nei raw | Migliore ora | Coincide |
| --- | --- | --- | --- |
| radice | Be3 / f3 | h3 | no |
| mossa nulla (tratto al Nero) | e5 | e5 | sì |
| 6.Be3 | Ng4 | Ng4 | sì |
| 6.Be3 Ng4 | Bg5 | Bg5 | sì |
| 6.Be3 e5 7.Nb3 | Be6 | Be6 | sì |
| 6.Be3 e5 7.Nb3 Be6 | h3 | f3 | no |
| 6.Be3 e6 | a3 | Qe2 | no |
| 6.Bg5 e6 7.f4 | Qb6 | Qb6 | sì |
| 6.Be2 e5 7.Nb3 | Be7 | Be6 | no |
| 6.Be2 e5 7.Nb3 Be7 | Be3 / O-O | h4 | no |
| 6.f4 e5 7.Nb3 | Nbd7 | Nc6 | no |

## Maia-2

maia2 0.11.0, modello rapid, dispositivo cpu.

| Ancora | Elo Maia | Fascia | Satura | Prime 3 alla radice | Risultato atteso (radice) |
| --- | --- | --- | --- | --- | --- |
| 1500 | 1700 | 7 | no | Bg5 29%, Be3 17%, Bc4 15% | 0.52 |
| 1900 | 2025 | 10 | sì | Bg5 32%, Be3 20%, f3 13% | 0.50 |
| 2400 | 2400 | 10 | sì | Bg5 32%, Be3 20%, f3 13% | 0.50 |

## Parole di prosa dei raw (prima stima, §9-bis.8)

Escluse tabelle numeriche, righe `[MAIA]`, titoli, commenti e nota di stato; le tabelle di solo testo contano cella per cella. Budget = `prose_words` della fascia dell'Elo dell'ancora (dettaglio 4).

| Raw | Sezioni (parole) | Totale | `prose_words` della fascia |
| --- | --- | --- | --- |
| najdorf_w_1500 | S01 33, S03 77, S05 61, S06 24, S08 52, S10 35, S02 37 | 319 | 500 (1200_1600) |
| najdorf_w_1900 | S01 80, S03 33, S04 98, S05 163, S06 152, S07 36, S08 27, S10 65 | 654 | 1400 (1600_2000) |
| najdorf_w_2400 | S01 81, S07 38, S03 109 | 228 | 610 (ge2400) |

<!-- keep: M1b -->
## Misura delle parole dei fewshot (M1b, §8-bis.4 punto 6, §0.5)

Conteggio di §9-bis.8 su tutte le parole scritte nei fewshot (paragrafi, voci, celle di testo, intestazioni
di `text_table`). Regola applicata: si aggiorna `prose_words` della fascia dell'ancora se il totale si
discosta di oltre il 15%; si aggiornano i pesi di un'ancora se la quota di almeno una sezione si discosta di
oltre il 15% dalla quota configurata (pesi rinormalizzati sulle sezioni presenti).

| Fewshot | Parole per sezione | Totale | `prose_words` prima | Scarto | Decisione |
| --- | --- | --- | --- | --- | --- |
| najdorf_w_1500 | S01 46, S03 124, S05 94, S06 65, S07 56, S08 84, S10 37 | 506 | 650 (1200_1600) | −22% | `prose_words` 650 → 500; pesi 1500 aggiornati (S10 pesava 0,13 delle sezioni presenti, misura 0,07) |
| najdorf_w_1900 | S01 91, S03 177, S04 136, S05 222, S06 258, S07 155, S08 80, S10 98 | 1217 | 1400 (1600_2000) | −13% | nessuna modifica (quote entro il 15%; la più lontana è S06, −14%) |
| najdorf_w_2400 | S01 90, S03 190, S06 143, S07 130, S08 56 | 609 | 800 (ge2400) | −24% | `prose_words` 800 → 610; pesi invariati (quote entro il 15%) |

Pesi dell'ancora 1500 (`config/section_budget.yaml`): S01 0,08 → 0,09; S03 0,25 → 0,23; S05 0,15 → 0,18;
S06 0,10 → 0,12; S07 0,10; S08 0,14 → 0,16; S10 0,12 → 0,07 (S02, S09, S12, S13 invariati: non misurabili in M1).
Le fasce non coperte da un'ancora (`lt1200`, `2000_2400`) restano alle ipotesi iniziali.

Quota `theory` misurata: 1500 0,50 (tetto 0,70), 1900 0,42 (tetto 0,50), 2400 0,13 (tetto 0,35). I tetti
restano invariati: sono limiti superiori, e la misura serve a evitare che V08 blocchi gli esempi (§14),
cosa che non accade.

Dopo le modifiche i pacchetti golden sono stati rigenerati (`golden --packs --recorded --force`): cambiano
solo `word_budget`, `config_hash` e `created_utc` (`prose_words` e i pesi non intervengono nell'esplorazione, che rigioca le stesse registrazioni). `_s07_alt.json` misura 194
parole contro un budget di 230 (S07 nella modalità avversario, ancora 1900).
