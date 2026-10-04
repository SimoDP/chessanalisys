# Analisi della posizione: Sicilian Defense: Najdorf Variation

FEN: `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` · Tratto: il Bianco · Giochi con: il Bianco
Elo dichiarato 2400 FIDE → 2400 in scala Lichess usata da Maia-2 · Avversario: 2400 FIDE → 2400
Fascia ge2400 · Ancora 2400 · Profilo deep · Stockfish 19 · profondità radice 31

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore.
> Maia-2 è poco affidabile a questo livello (vedi le sezioni sull'avversario).

## Sintesi

Posizione teorica, vantaggio minimo: da +0,34 a +0,04 tra le cinque mosse spiegate, patta al 93% secondo il motore. Il problema non è cercare vantaggio ma **scegliere la struttura e il move order** che portano alla posizione voluta, evitando i rifugi teorici del Nero. Con il Nero al tratto la valutazione sarebbe -0,07 (...e6): il vantaggio è sostanzialmente il tratto.

Fattori decisivi: la corsa g4 → g5 contro ...b5 → ...b4 con gli arrocchi opposti; la casa d5 dopo ...e5 (+0,28); la diagonale a7–g1 con la donna nera in b6; la stabilità di e4.

## Fattori decisivi

| Categoria | T (tu)* | R | Nota |
| --- | --- | --- | --- |
| Attività dei pezzi | 100 | 26 | — |
| Struttura pedonale | 100 | 12 | — |
| Spazio e centro | 100 | 7 | — |
| Complessità pratica | 80 | 7 | — |
| Sicurezza del re | 98 | 1 | — |

* Punteggi poco affidabili: Maia-2 poco affidabile a questo livello o valutazioni instabili.

Fattori di lungo periodo: l'attività (26), con quattro pezzi neri ancora chiusi, e la struttura (12), che le linee di 6.f3 e 6.Be3 fissano al centro. Nessun fattore tattico; complessità pratica media (80).

## Piani per struttura

- **Inglese (Be3 → f3 → Qd2 → O-O-O):** arrocco lungo, poi g4 → g5 → h4; il Nero risponde con ...b5 → ...b4 e con la rottura in d5 nei momenti giusti. È una corsa: un tempo decide. Il motore tiene i due ordini 6.f3 (+0,34) e 6.Be3 (+0,32) quasi alla pari e le loro linee principali si incontrano dopo sette semimosse; con 6.f3 il salto del cavallo in g4 non esiste.
- **Alfiere in d3:** 6.Bd3 (+0,19) protegge e4 con l'alfiere e lascia aperta la scelta dell'arrocco; contro il fianchetto la linea del motore è 6.Bd3 g6 7.f3 e5 8.Nb3 Be6. Costo rispetto alla migliore: 0,15.
- **Donna in d3:** 6.Qd3 (+0,20) è la scelta meno teorica; dopo ...Nbd7 la posizione è 0,00 e il Nero prepara il fianchetto, come in 6.Qd3 Nbd7 7.Be2 g6 8.Bg5 Bg7.
- **Pedone e4:** nelle strutture con f3 è stabile; senza f3 resta esposto alla presa del cavallo f6 se il cavallo c3 è sovraccarico o cacciato dalla spinta in b4. †
- **Diagonale a7–g1:** con l'alfiere in e3, il cavallo in d4 e il re in g1, la donna in b6 mette in difficoltà l'alfiere se il cavallo deve muoversi. †

## Cosa cerca il Nero

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

Le idee del Nero dipendono dal sistema. Contro 6.Be3 la migliore è ...Ng4 (+0,28), un tempo sull'alfiere; contro 6.f3 il Nero sceglie tra ...e5 (+0,28) e ...Nc6 (+0,28).

| Dopo… | Migliore del Nero | ...g6 | Costo |
| --- | --- | --- | --- |
| 6.f3 | ...e5 (+0,28) | +0,61 | 0,33 |
| 6.Be3 | ...Ng4 (+0,28) | +0,68 | 0,40 |
| 6.Qd3 | ...Nbd7 (0,00) | +0,22 | 0,22 |
| 6.Bd3 | ...e5 (+0,15) | +0,15 | 0,00 |
| 6.Bg5 | ...e6 (+0,05) | +1,12 | 1,07 |
| 6.f3 e5 7.Nb3 | ...Be6 (+0,30) | +0,64 | 0,34 |
| 6.f3 Nc6 7.Be3 | ...e5 (+0,25) | +0,76 | 0,51 |
| 6.f3 e6 7.g4 | ...h6 (+0,29) | +1,46 | 1,17 |
| 6.Be3 Ng4 7.Bg5 | ...h6 (+0,31) | +1,18 | 0,87 |
| 6.Be3 Nc6 7.h3 | ...e5 (+0,40) | +0,54 | 0,14 |
| 6.Be3 e5 7.Nb3 | ...Be7 (+0,28) | +0,89 | 0,61 |
| 6.Qd3 Nbd7 7.Be2 | ...b5 (0,00) | +0,22 | 0,22 |
| 6.Qd3 e6 7.a4 | ...Nc6 (+0,14) | +0,62 | 0,48 |
| 6.Qd3 e5 7.Nf5 | ...g6 (+0,30) | +0,30 | 0,00 |

La mossa di contesto è il fianchetto ...g6: contro 6.Bd3 non costa nulla (0,00), contro 6.f3 e 6.Be3 costa 0,33 e 0,40, contro 6.Bg5 perde 1,07, e dopo 6.f3 ...e6 7.g4 perde 1,17: con il pedone già in g4 l'attacco arriva con un tempo di vantaggio.

Le frequenze di Maia-2 indicano soltanto che contro 6.Be3 ...e5 resta la scelta più comune (69%), davanti a ...Ng4 (15%): bisogna essere pronti a entrambe.

Contro le strutture inglesi lo schema tipico del Nero è ...e5 → ...Be6 → ...Be7 → ...O-O, con il cavallo di donna in d7 e la spinta del pedone b appena il re bianco va sul lato di donna. †

## Mosse candidate e test di move order

| Mossa | Valutazione | Scelta a 2400* | Linea del motore | Nota |
| --- | --- | --- | --- | --- |
| **6.f3** ★ | +0,34 | 13% | 6...e5 7.Nb3 Be6 8.Be3 Be7 9.Qd2 O-O 10.O-O-O | Evita il salto in g4; dopo ...e5 segue Nb3 (+0,30) |
| 6.Be3 | +0,32 | 20% | 6...e5 7.Nb3 Be6 8.Qd2 Be7 9.f3 Nbd7 10.g4 | Ammette ...Ng4 (+0,28) |
| 6.Qd3 | +0,20 | <1% | 6...Nbd7 7.Be2 g6 8.Bg5 Bg7 9.f4 h6 10.Bh4 | Fuori teoria; ...Nbd7 pareggia (0,00) |
| 6.Bd3 | +0,19 | 3% | 6...g6 7.f3 e5 8.Nb3 Be6 9.Be3 Be7 10.Qd2 | Contro il fianchetto non perde nulla (+0,15) |
| 6.g3 | +0,15 | 1% | 6...e5 7.Nb3 Be7 8.Bg2 a5 9.Nd2 Bg4 10.Bf3 | — |
| 6.Be2 | +0,15 | 10% | 6...e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 Nbd7 10.Qd3 | — |
| 6.h3 | +0,14 | 3% | 6...e5 7.Nde2 h5 8.g3 Be6 9.Bg2 b5 10.a4 | — |
| 6.a4 | +0,11 | 4% | 6...e5 7.Nf3 Be7 8.Bg5 Be6 9.Bxf6 Bxf6 10.Nd5 | — |
| 6.Bc4 | +0,09 | 9% | 6...e6 7.Bb3 b5 8.Be3 Be7 9.a3 O-O 10.f3 | — |
| 6.f4 | +0,04 | 1% | 6...e5 7.Nf3 Nbd7 8.a4 Be7 9.Bc4 Qa5 10.Qe2 | — |
| 6.Bg5 | +0,04 | 32% | 6...e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 Qa3 10.f5 | Teoria del Pedone Avvelenato: 6.Bg5 e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 Qa3 10.f5 Be7 |
| 6.Nb3 | +0,04 | <1% | 6...e6 7.Be2 Nc6 8.a4 Be7 9.Be3 b6 10.O-O | — |

* Probabilità di Maia-2 poco affidabili a questo livello.

| Dopo | Mosse (dalla migliore) | Nota |
| --- | --- | --- |
| 6.f3 | 6...e5 (+0,28), 6...Nc6 (+0,28), 6...e6 (+0,30) | — |
| 6.f3 e5 | 7.Nb3 (+0,30), 7.Nde2 (-0,19), 7.Nf5 (-1,08) | Solo Nb3 tiene: Nf5 perde 1,38 |
| 6.f3 e5 7.Nb3 | 7...Be6 (+0,30), 7...Be7 (+0,30), 7...h6 (+0,45) | — |
| 6.f3 e5 7.Nb3 Be6 | 8.Be3 (+0,30), 8.a3 (+0,06), 8.h4 (+0,02) | — |
| 6.f3 Nc6 | 7.Be3 (+0,26), 7.Be2 (+0,17), 7.h4 (+0,16) | — |
| 6.f3 Nc6 7.Be3 | 7...e5 (+0,25), 7...d5 (+0,53), 7...h5 (+0,53) | — |
| 6.f3 Nc6 7.Be3 e5 | 8.Nb3 (+0,32), 8.Nde2 (+0,16), 8.Nxc6 (+0,13) | — |
| 6.f3 e6 | 7.g4 (+0,35), 7.Be3 (+0,32), 7.a3 (+0,24) | — |
| 6.f3 e6 7.g4 | 7...h6 (+0,29), 7...b5 (+0,53), 7...Nfd7 (+0,54) | ...h6 è quasi obbligata: ...b5 costa 0,24 |
| 6.f3 e6 7.g4 h6 | 8.Be3 (+0,28), 8.Qe2 (+0,28), 8.h4 (+0,17) | — |
| 6.Be3 | 6...Ng4 (+0,28), 6...Nc6 (+0,30), 6...e5 (+0,31) | — |
| 6.Be3 Ng4 | 7.Bg5 (+0,31), 7.Bc1 (+0,31), 7.Qd3 (-0,10) | Le due ritirate si equivalgono (+0,31) |
| 6.Be3 Ng4 7.Bg5 | 7...h6 (+0,31), 7...Nc6 (+0,56), 7...Bd7 (+1,02) | — |
| 6.Be3 Ng4 7.Bg5 h6 | 8.Bh4 (+0,29), 8.Bc1 (+0,06), 8.Bd2 (-0,19) | Solo Bh4 tiene: Bc1 cede 0,23 |
| 6.Be3 Nc6 | 7.h3 (+0,34), 7.f4 (+0,33), 7.Nb3 (+0,31) | — |
| 6.Be3 Nc6 7.h3 | 7...e5 (+0,40), 7...Bd7 (+0,49), 7...g6 (+0,54) | — |
| 6.Be3 Nc6 7.h3 e5 | 8.Nb3 (+0,36), 8.Nxc6 (+0,31), 8.Nf3 (+0,14) | — |
| 6.Be3 e5 | 7.Nb3 (+0,13), 7.Nf3 (+0,05), 7.Nde2 (-0,11) | — |
| 6.Be3 e5 7.Nb3 | 7...Be7 (+0,28), 7...Be6 (+0,31), 7...Qc7 (+0,47) | — |
| 6.Be3 e5 7.Nb3 Be7 | 8.f3 (+0,24), 8.Be2 (+0,22), 8.Qd3 (+0,15) | — |
| 6.Qd3 | 6...Nbd7 (0,00), 6...e6 (+0,15), 6...g6 (+0,22), 6...e5 (+0,28) | — |
| 6.Qd3 Nbd7 | 7.Be2 (0,00), 7.a4 (-0,05), 7.f3 (-0,09) | — |
| 6.Qd3 Nbd7 7.Be2 | 7...b5 (0,00), 7...e6 (+0,13), 7...Nc5 (+0,22) | — |
| 6.Qd3 Nbd7 7.Be2 b5 | 8.Nd5 (+0,05), 8.O-O (0,00), 8.b4 (0,00) | — |
| 6.Qd3 e6 | 7.a4 (+0,15), 7.f4 (+0,03), 7.Bd2 (+0,02) | — |
| 6.Qd3 e6 7.a4 | 7...Nc6 (+0,14), 7...Nbd7 (+0,18), 7...Be7 (+0,20) | — |
| 6.Qd3 e6 7.a4 Nc6 | 8.Nxc6 (+0,08), 8.Be2 (-0,14), 8.Qe3 (-0,19) | — |
| 6.Qd3 g6 | 7.f3 (+0,22), 7.Be2 (+0,18), 7.Bg5 (+0,09) | — |
| 6.Qd3 g6 7.f3 | 7...b5 (+0,17), 7...Bg7 (+0,32), 7...Nbd7 (+0,33) | — |
| 6.Qd3 g6 7.f3 b5 | 8.Be3 (+0,11), 8.a4 (+0,10), 8.Be2 (+0,06) | — |
| 6.Qd3 e5 | 7.Nf5 (+0,29), 7.Nb3 (+0,12), 7.Nf3 (-0,15) | Nf5 (+0,29) è più forte della ritirata Nb3 |
| 6.Qd3 e5 7.Nf5 | 7...g6 (+0,30), 7...Bxf5 (+0,32), 7...h6 (+0,62) | — |
| 6.Qd3 e5 7.Nf5 g6 | 8.Ne3 (+0,29), 8.Nh6 (-0,03), 8.Ng3 (-0,20) | — |

Tra la prima e la quinta mossa spiegata ci sono 0,30: la scelta è di sistema, non di valutazione. Il test critico è dopo 6.Be3 ...Ng4: dopo Bg5 ...h6 solo Bh4 (+0,29) conserva il vantaggio.

6.f3 è l'ordine che lascia meno scelte al Nero; 6.Qd3 (+0,20) e 6.Bd3 (+0,19) cambiano struttura cedendo poco più di un decimo.

## Minacce invisibili al tuo livello

Nessuna linea supera la soglia di rischio, che a questo livello è la più bassa: con una mossa in più il Nero otterrebbe -0,07. Nell'albero dei test di move order non c'è una perdita decisiva nascosta.

## Rapporto tecnico

- Versioni: Stockfish 19 · Maia-2 0.11.0 (modello rapid, cpu) · modello di linguaggio: nessuno (esempio di riferimento)
- Profilo deep · tempo dei motori 1483,6 s · nodi analizzati 72 · profondità minima 18 e massima 31
- Nodi sotto la profondità minima: nessuno
- Elo dichiarato 2400 FIDE · Elo Maia-2 2400 · fascia ge2400 · ancora 2400 · confidenza di Maia-2 bassa
- Sezioni omesse: S05 (band_2400), S08 (no_classified_move), S10 (band_2400), S11 (milestone), S12 (matrix), S13 (matrix) · assorbite: S04 in S03
- Fasi omesse: nessuna · nodi omessi: nessuno
- Contenuto teorico: 3 blocchi, 16% delle parole
- Controlli: V01 superato · V02 superato · V03 superato · V04 superato · V05 superato · V06 superato · V07 superato · V08 superato · V09 superato · V10 superato · V11 superato
- Retry: 0
- Rimossi in modalità degradata: nessuno
- Marcati come non verificati: nessuno
- Avvisi: nessuno
- Note del modello: nessuna
- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e asserzione non è controllata.

---

† contenuto teorico, non verificato dai motori
