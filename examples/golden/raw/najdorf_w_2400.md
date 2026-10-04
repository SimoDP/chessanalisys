---
id: "najdorf_w_2400"
anchor: "2400"
fen: "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
user_color: "w"
source: "Esempi di output ideale — Najdorf, Bianco: 1500 e 2400.md (Parte B)"
status: "raw_v0"
validated: false
corrections:
  - "Pedone Avvelenato: «pareggio quasi totale» sostituito da «posizioni molto vicine alla parità (+0,13)», coerente con il valore del motore"
needs_review:
  - "S07: manca T1 (tabella delle candidate): il fewshot la aggiunge"
  - "S03: «Bf3 evita ...Nd7-c5 con tempo» non verificato"
  - "S03: «...Nc4» da precisare"
  - "T2: le righe ℓ2-ℓ3 (6.Be3 e5 7.Nb3 Be6, 6.Bg5 e6 7.f4, 6.Be2 e5 7.Nb3 Be7) arrivano in M2"
---

# Esempio di output ideale — Najdorf, mossa 6, Bianco, 2400 FIDE

`rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6`

> **Stato (raw v0, corretto in v0.9.1).** Dati di Stockfish **reali** (Stockfish 16, profondità ≈ 17-22), valori in pedoni dal punto di vista del Bianco. Campi `[MAIA]` = segnaposto. Radar illustrativo. Parti teoriche non validate. Questo file è materiale di partenza per il fewshot (documentazione §8-bis.4): **non** va usato come esempio nel prompt. I commenti `<!-- Sxx -->` indicano la sezione di destinazione (§8.2-ter).


## Sintesi  <!-- S01 -->

Posizione teorica, vantaggio minimo: +0,17 / +0,37 a seconda della mossa, patta ≈ 92% al motore. Il problema non è cercare vantaggio ma **scegliere la struttura e il move order** per ottenere la posizione desiderata evitando i rifugi teorici del Nero. Se il Nero avesse la mossa: ≈ 0,00 (...e5). Il vantaggio è sostanzialmente il tratto.

Fattori decisivi: corsa g4-g5 contro ...b5-b4 nelle strutture con arrocco lungo; casa d5 dopo ...e5; diagonale a7–g1 con ...Qb6; stabilità di e4.

## Test critici di move order (Stockfish)  <!-- S07 (T2) -->

| Dopo | Risposte del Nero (miglior → peggior) | Note |
| --- | --- | --- |
| 6.Be3 | ...Ng4 (+0,33), ...e5 (+0,35), ...Nc6 (+0,41), ...e6 (+0,50) | Tutte le prime tre sono pari per il motore |
| 6.Be3 Ng4 | Bianco: **7.Bg5** (+0,38) h6 8.Bh4 g5 9.Bg3 Bg7 10.h3; **7.Bc1** (+0,36) Nf6 8.Be3; 7.Qd2/Qe2/Qf3 ≈ 0,00 | 7.Qd2 Nxe3 8.Qxe3 g6 pareggia: evitarla |
| 6.Be3 e5 7.Nb3 Be6 | Bianco: 8.h3 (+0,34), 8.Qd2 (+0,32), **8.f3** (+0,28), 8.Be2 (+0,24), 8.Qd3 (+0,22), 8.a3 (+0,09) | La differenza tra h3, Qd2 e f3 è ≤ 0,06: scelta di sistema, non di valutazione |
| 6.Be3 e6 | Bianco: 7.a3 (+0,49), 7.Be2/f3 (+0,43), 7.Qd2 (+0,42), 7.g4 (+0,40), 7.Qf3 (+0,30) | Contro ...e6 il vantaggio è un po' maggiore; Qf3 è meno forte |
| 6.Bg5 e6 7.f4 | Nero: **...Qb6** (+0,13), ...h6 (+0,20), ...Nbd7/...Be7 (+0,38), ...b5 (+0,52) | Il Pedone Avvelenato (8.Qd2 Qxb2 9.Rb1 Qa3 10.f5 Be7) porta a posizioni molto vicine alla parità (+0,13): per evitarlo servono alternative al 7.f4 da analizzare |
| 6.Be2 e5 7.Nb3 Be7 | Bianco: 8.Be3 / 8.O-O (+0,30), 8.Bf3 (+0,25), 8.Qd3 (+0,24), 8.h3 (+0,12) | Linea: 8.Be3 Be6 9.O-O O-O 10.Bf3 Nbd7 11.a4 |

<!-- S06: questo paragrafo e la tabella di ...Nc6 diventano T3 + testo in S06 -->
**...Nc6 del Nero** costa circa 0,5 dopo 6.Be3 e5 7.Nb3 (+0,86 contro +0,33): è impreciso in quella struttura. Contro 6.Be2 e 6.f4 è invece una risposta normale (≈ 0,1 e ≈ 0).

## Piani per struttura  <!-- S03 (S04 assorbita) -->

- **Inglese (Be3, f3, Qd2, O-O-O):** arrocco lungo, poi g4-g5 e h4; il Nero risponde con ...b5-b4 e ...Nc4 o ...d5 nei momenti giusti. <!-- needs_review: ...Nc4 presuppone ...Nbd7-b6 (o ...Nc6-a5); precisare o togliere --> È una corsa: un tempo decide.
- **Classica (Be2/Bf3, O-O, Be3, a4):** a4 frena ...b5; **Nd5** forza lo scambio e cambia la struttura (linea del motore: 9.Nd5 Nxd5 10.exd5 Bf5 11.O-O). Bf3 evita ...Nd7-c5 con tempo. <!-- needs_review: affermazione teorica non verificata -->
- **Pedone e4:** in f3-strutture è stabile; senza f3 resta soggetto a ...Nxe4 se Nc3 è sovraccarico o attaccato (...b5-b4).
- **Diagonale a7–g1:** con Be3, Nd4 e re in g1, ...Qb6 mette in difficoltà Be3 se Nd4 deve muoversi.

## Fattori pratici (Maia a 2400)  <!-- S06 (la frase di confidenza la inserisce il render, D-46) -->

Sopra \~2000 Maia ha meno dati: usare soprattutto Stockfish e indicare l'incertezza. `[MAIA]` probabilità che il Nero scelga ...Ng4, ...e5, ...e6 contro 6.Be3: da riempire.
