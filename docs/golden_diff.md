# Golden: confronto tra i raw e la nuova esecuzione (M0)

Generato da `chessanalyst golden --data` il 2026-10-04T02:01:56+00:00 (app 0.1.0, profilo `deep`, fattore di tempo 1.0).
Motore: Stockfish 16. Valori in pedoni dal punto di vista del Bianco (= utente nei raw).
Soglia di segnalazione: scostamento > 0,25 pedoni (⚠).

## AC-09

Esito: **superato** (le prime 3 candidate dei raw devono differire ≤ 0,25 e restare tra le prime 6).

| Mossa | Raw | Nuovo | Differenza | Rango nuovo | Esito |
| --- | --- | --- | --- | --- | --- |
| 6.Be3 | +0,37 | +0,32 | -0,05 | 3 | OK |
| 6.f3 | +0,37 | +0,38 | +0,01 | 1 | OK |
| 6.h3 | +0,35 | +0,32 | -0,03 | 2 | OK |

## Nodi analizzati

| Nodo | Fase | Profondità | MultiPV | Tempo (s) | Instabile | Migliore |
| --- | --- | --- | --- | --- | --- | --- |
| radice | E0 | 29 | 16 | 270 | no | f3 +0,38 |
| mossa nulla (tratto al Nero) | E1 | 26 | 8 | 72 | no | e5 0,00 |
| 6.Be3 | E2 | 24 | 8 | 59 | no | e5 +0,34 |
| 6.Be2 | E2 | 25 | 8 | 59 | no | e5 +0,20 |
| 6.Bg5 | E2 | 24 | 8 | 59 | no | e6 +0,23 |
| 6.f4 | E2 | 24 | 8 | 59 | no | e5 +0,06 |
| 6.Be3 Ng4 | E3 | 24 | 8 | 23 | no | Bg5 +0,30 |
| 6.Be3 e5 7.Nb3 | E3 | 22 | 8 | 23 | no | Be6 +0,30 |
| 6.Be3 e5 7.Nb3 Be6 | E3 | 24 | 8 | 23 | no | Qd2 +0,31 |
| 6.Be3 e6 | E3 | 22 | 8 | 23 | no | a3 +0,48 |
| 6.Bg5 e6 7.f4 | E3 | 22 | 8 | 23 | no | Qb6 +0,22 |
| 6.Be2 e5 7.Nb3 | E3 | 23 | 8 | 23 | no | Be6 +0,25 |
| 6.Be2 e5 7.Nb3 Be7 | E3 | 24 | 8 | 23 | no | O-O +0,26 |
| 6.f4 e5 7.Nb3 | E3 | 22 | 8 | 23 | no | Nc6 +0,02 |

WDL alla radice (riga 1): [46, 953, 1] per mille; patta 95% (raw: circa 92%).

## Valori numerici dei raw

| Nodo | Mossa | Raw | Nuovo | Differenza | Fonte del nuovo valore | Raw citati | Nota |
| --- | --- | --- | --- | --- | --- | --- | --- |
| radice | Be3 | +0,37 | +0,32 | -0,05 | MultiPV 3 | 1500, 1900, 2400 |  |
| radice | f3 | +0,37 | +0,38 | +0,01 | MultiPV 1 | 1900 |  |
| radice | h3 | +0,35 | +0,32 | -0,03 | MultiPV 2 | 1900 |  |
| radice | Bg5 | +0,29 | +0,21 | -0,08 | MultiPV 6 | 1500, 1900 |  |
| radice | Nb3 | +0,25 | +0,14 | -0,11 | MultiPV 8 | 1900 |  |
| radice | Bd3 | +0,25 | +0,26 | +0,01 | MultiPV 5 | 1900 |  |
| radice | Bc4 | +0,23 | +0,07 | -0,16 | MultiPV 12 | 1500, 1900 |  |
| radice | a4 | +0,23 | +0,18 | -0,05 | MultiPV 7 | 1900 |  |
| radice | g3 | +0,22 | +0,10 | -0,12 | MultiPV 11 | 1900 |  |
| radice | Be2 | +0,22 | +0,26 | +0,04 | MultiPV 4 | 1500, 1900 |  |
| radice | f4 | +0,20 | +0,04 | -0,16 | MultiPV 13 | 1900 |  |
| radice | Rg1 | +0,17 | 0,00 | -0,17 | MultiPV 16 | 1900, 2400 |  |
| mossa nulla (tratto al Nero) | e5 | 0,00 | 0,00 | 0,00 | MultiPV 1 | 1900, 2400 | valore approssimato nel raw (≈ 0,0) |
| 6.Be3 | Ng4 | +0,33 | +0,39 | +0,06 | MultiPV 2 | 1900, 2400 |  |
| 6.Be3 | e5 | +0,35 | +0,34 | -0,01 | MultiPV 1 | 1900, 2400 |  |
| 6.Be3 | Nc6 | +0,41 | +0,39 | -0,02 | MultiPV 3 | 1900, 2400 |  |
| 6.Be3 | e6 | +0,50 | +0,47 | -0,03 | MultiPV 4 | 2400 |  |
| 6.Be3 Ng4 | Bg5 | +0,38 | +0,30 | -0,08 | MultiPV 1 | 2400 |  |
| 6.Be3 Ng4 | Bc1 | +0,36 | +0,28 | -0,08 | MultiPV 2 | 2400 |  |
| 6.Be3 Ng4 | Qd2 | 0,00 | -0,15 | -0,15 | MultiPV 4 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 Ng4 | Qe2 | 0,00 | -0,03 | -0,03 | MultiPV 3 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 Ng4 | Qf3 | 0,00 | -0,16 | -0,16 | MultiPV 6 | 2400 | ≈ 0,00 nel raw |
| 6.Be3 e5 7.Nb3 | Be6 | +0,33 | +0,30 | -0,03 | MultiPV 1 | 1900 |  |
| 6.Be3 e5 7.Nb3 | Nc6 | +0,86 | +0,83 | -0,03 | MultiPV 8 | 1900, 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | h3 | +0,34 | +0,31 | -0,03 | MultiPV 2 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Qd2 | +0,32 | +0,31 | -0,01 | MultiPV 1 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | f3 | +0,28 | +0,28 | 0,00 | MultiPV 3 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Be2 | +0,24 | +0,24 | 0,00 | MultiPV 4 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | Qd3 | +0,22 | +0,24 | +0,02 | MultiPV 5 | 2400 |  |
| 6.Be3 e5 7.Nb3 Be6 | a3 | +0,09 | +0,13 | +0,04 | MultiPV 6 | 2400 |  |
| 6.Be3 e6 | a3 | +0,49 | +0,48 | -0,01 | MultiPV 1 | 2400 |  |
| 6.Be3 e6 | Be2 | +0,43 | +0,36 | -0,07 | MultiPV 3 | 2400 |  |
| 6.Be3 e6 | f3 | +0,43 | +0,42 | -0,01 | MultiPV 2 | 2400 |  |
| 6.Be3 e6 | Qd2 | +0,42 | +0,33 | -0,09 | MultiPV 5 | 2400 |  |
| 6.Be3 e6 | g4 | +0,40 | 0,00 | -0,40 ⚠ | ricerca ristretta (E2c) | 2400 |  |
| 6.Be3 e6 | Qf3 | +0,30 | +0,35 | +0,05 | MultiPV 4 | 2400 |  |
| 6.Bg5 e6 7.f4 | Qb6 | +0,13 | +0,22 | +0,09 | MultiPV 1 | 2400 |  |
| 6.Bg5 e6 7.f4 | h6 | +0,20 | +0,48 | +0,28 ⚠ | MultiPV 4 | 2400 |  |
| 6.Bg5 e6 7.f4 | Nbd7 | +0,38 | +0,24 | -0,14 | MultiPV 2 | 2400 |  |
| 6.Bg5 e6 7.f4 | Be7 | +0,38 | +0,45 | +0,07 | MultiPV 3 | 2400 |  |
| 6.Bg5 e6 7.f4 | b5 | +0,52 | +0,49 | -0,03 | MultiPV 5 | 2400 |  |
| 6.Be2 e5 7.Nb3 | Be7 | +0,24 | +0,26 | +0,02 | MultiPV 2 | 1900 |  |
| 6.Be2 e5 7.Nb3 | Nc6 | +0,34 | +0,42 | +0,08 | MultiPV 4 | 1900, 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | (nodo) | +0,30 | +0,26 | -0,04 | riga 1 | 2400 | valutazione del nodo (D-40) |
| 6.Be2 e5 7.Nb3 Be7 | Be3 | +0,30 | +0,23 | -0,07 | MultiPV 2 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | O-O | +0,30 | +0,26 | -0,04 | MultiPV 1 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | Bf3 | +0,25 | +0,21 | -0,04 | MultiPV 4 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | Qd3 | +0,24 | +0,22 | -0,02 | MultiPV 3 | 2400 |  |
| 6.Be2 e5 7.Nb3 Be7 | h3 | +0,12 | +0,03 | -0,09 | ricerca ristretta (E2c) | 2400 |  |
| 6.f4 e5 7.Nb3 | Nbd7 | +0,06 | +0,22 | +0,16 | MultiPV 4 | 1900, 2400 |  |
| 6.f4 e5 7.Nb3 | Nc6 | +0,09 | +0,02 | -0,07 | MultiPV 1 | 1900, 2400 |  |

Valori oltre la soglia: **2** su 51.

## Mossa migliore per nodo

| Nodo | Migliore nei raw | Migliore ora | Coincide |
| --- | --- | --- | --- |
| radice | Be3 / f3 | f3 | sì |
| mossa nulla (tratto al Nero) | e5 | e5 | sì |
| 6.Be3 | Ng4 | e5 | no |
| 6.Be3 Ng4 | Bg5 | Bg5 | sì |
| 6.Be3 e5 7.Nb3 | Be6 | Be6 | sì |
| 6.Be3 e5 7.Nb3 Be6 | h3 | Qd2 | no |
| 6.Be3 e6 | a3 | a3 | sì |
| 6.Bg5 e6 7.f4 | Qb6 | Qb6 | sì |
| 6.Be2 e5 7.Nb3 | Be7 | Be6 | no |
| 6.Be2 e5 7.Nb3 Be7 | Be3 / O-O | O-O | sì |
| 6.f4 e5 7.Nb3 | Nbd7 | Nc6 | no |

## Maia-2

**Non eseguito**: Pesi di Maia-2 (rapid) assenti in /home/user/chessanalisys/data/maia2_models: esegui `python scripts/setup_engines.py`. `fixtures/golden_maia.json` non è stato prodotto; va rigenerato con `chessanalyst golden --data` su una macchina con i pesi di Maia-2.

## Parole di prosa dei raw (prima stima, §9-bis.8)

Escluse tabelle numeriche, righe `[MAIA]`, titoli, commenti e nota di stato; le tabelle di solo testo contano cella per cella. Budget = `prose_words` della fascia dell'Elo dell'ancora (dettaglio 4).

| Raw | Sezioni (parole) | Totale | `prose_words` della fascia |
| --- | --- | --- | --- |
| najdorf_w_1500 | S01 33, S03 77, S05 61, S06 24, S08 52, S10 35, S02 37 | 319 | 650 (1200_1600) |
| najdorf_w_1900 | S01 80, S03 33, S04 98, S05 163, S06 152, S07 36, S08 27, S10 65 | 654 | 1400 (1600_2000) |
| najdorf_w_2400 | S01 81, S07 38, S03 109 | 228 | 800 (ge2400) |
