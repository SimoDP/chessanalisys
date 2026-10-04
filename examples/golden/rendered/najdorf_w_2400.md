# Analisi della posizione: Sicilian Defense: Najdorf Variation

FEN: `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` · Tratto: il Bianco · Giochi con: il Bianco
Elo dichiarato 2400 FIDE → 2400 in scala Lichess usata da Maia-2 · Avversario: 2400 FIDE → 2400
Fascia ge2400 · Ancora 2400 · Profilo deep · Stockfish 16 · profondità radice 25

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore.
> Test di move order limitati al primo livello: l'analisi completa a questo livello arriva in una versione successiva.
> Maia-2 è poco affidabile a questo livello (vedi le sezioni sull'avversario).

## Sintesi

Posizione teorica, vantaggio minimo: da +0,39 a +0,21 tra le cinque mosse spiegate, patta al 95% secondo il motore. Il problema non è cercare vantaggio ma **scegliere la struttura e il move order** che portano alla posizione voluta, evitando i rifugi teorici del Nero. Con il Nero al tratto la valutazione sarebbe +0,01 (...e5): il vantaggio è sostanzialmente il tratto.

Fattori decisivi: la corsa g4 → g5 contro ...b5 → ...b4 con gli arrocchi opposti; la casa d5 dopo ...e5 (+0,30); la diagonale a7–g1 con la donna nera in b6; la stabilità di e4.

## Piani per struttura

- **Inglese (Be3 → f3 → Qd2 → O-O-O):** arrocco lungo, poi g4 → g5 → h4; il Nero risponde con ...b5 → ...b4 e con la rottura in d5 nei momenti giusti. È una corsa: un tempo decide. Il motore tiene i due ordini 6.f3 (+0,39) e 6.Be3 (+0,34) quasi alla pari; con 6.f3 il salto del cavallo in g4 non esiste.
- **Classica (Be2 → O-O → Be3 → a4):** arrocco corto; la spinta in a4 frena la spinta del pedone b, il salto in d5 forza lo scambio e cambia la struttura, come nella linea 6.Be2 e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 Nxd5 10.exd5 Bf5. Costo rispetto alla migliore: 0,14.
- **Con 6.h3:** g4 → g5 senza la spinta in f3, con il re bianco ancora flessibile. Contro ...e5 il cavallo va in e2 e il motore prepara il fianchetto (6.h3 e5 7.Nde2 h5 8.g3 Be7); contro ...e6 la spinta g4 vale +0,33.
- **Pedone e4:** nelle strutture con f3 è stabile; senza f3 resta esposto alla presa del cavallo f6 se il cavallo c3 è sovraccarico o cacciato dalla spinta in b4. 6.Bd3 (+0,27) lo protegge con l'alfiere e porta all'arrocco corto.
- **Diagonale a7–g1:** con l'alfiere in e3, il cavallo in d4 e il re in g1, la donna in b6 mette in difficoltà l'alfiere se il cavallo deve muoversi. †

## Cosa cerca il Nero

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

Le idee del Nero dipendono dal sistema. Contro 6.Be3 la migliore è ...Ng4 (+0,35), un tempo sull'alfiere; contro 6.f3 il Nero sceglie tra ...e5 (+0,30) e ...Nc6 (+0,34).

| Dopo… | Migliore del Nero | ...e5 | Costo |
| --- | --- | --- | --- |
| 6.f3 | ...e5 (+0,30) | +0,30 | 0,00 |
| 6.Be3 | ...Ng4 (+0,35) | +0,36 | 0,01 |
| 6.h3 | ...e5 (+0,22) | +0,22 | 0,00 |
| 6.Bd3 | ...Nbd7 (+0,26) | +0,29 | 0,03 |
| 6.Bg5 | ...e6 (+0,21) | +1,07 | 0,86 |

La mossa di contesto è ...e5: contro 6.f3, 6.Be3, 6.h3 e 6.Bd3 costa al massimo 0,03, contro 6.Bg5 perde 0,86 (+1,07 invece di +0,21): con l'alfiere in g5 la spinta inchioda il cavallo f6 sulla donna e cede la casa d5.

Le frequenze di Maia-2 indicano soltanto che contro 6.Be3 ...e5 resta la scelta più comune (69%), davanti a ...Ng4 (15%): bisogna essere pronti a entrambe.

Contro le strutture inglesi lo schema tipico del Nero è ...e5 → ...Be6 → ...Be7 → ...O-O, con il cavallo di donna in d7 e la spinta del pedone b appena il re bianco va sul lato di donna; contro la classica cerca la rottura in d5 o il cavallo in c5. †

## Mosse candidate e test di move order

| Mossa | Valutazione | Scelta a 2400* | Linea del motore | Nota |
| --- | --- | --- | --- | --- |
| **6.f3** ★ | +0,39 | 13% | 6...e5 7.Nb3 Be6 8.Be3 h5 9.Nd5 Bxd5 10.exd5 | Evita il salto in g4; dopo ...e5 segue Nb3 (+0,38) |
| 6.Be3 | +0,34 | 20% | 6...e5 7.Nb3 Be6 8.h3 Nbd7 9.g4 h6 10.Qd2 | Ammette ...Ng4 (+0,35) |
| 6.h3 | +0,32 | 3% | 6...e5 7.Nde2 h5 8.g3 Be7 9.Bg2 b5 10.Nd5 | Senza f3; contro ...e6 segue g4 (+0,33) |
| 6.Bd3 | +0,27 | 3% | 6...e5 7.Nde2 Be7 8.O-O O-O 9.Ng3 g6 10.Bc4 | Arrocco corto; il motore risponde ...Nbd7 (+0,26) |
| 6.Be2 | +0,25 | 10% | 6...e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 Nxd5 10.exd5 | — |
| 6.f4 | +0,25 | 1% | 6...e5 7.Nf3 Qc7 8.a4 Be7 9.Bd3 O-O 10.O-O | — |
| 6.g3 | +0,25 | 1% | 6...e5 7.Nb3 Be7 8.Bg5 Nbd7 9.a4 h6 10.Be3 | — |
| 6.a4 | +0,24 | 4% | 6...e5 7.Nf3 Be7 8.Bg5 Be6 9.Bxf6 Bxf6 10.Nd5 | — |
| 6.Qd3 | +0,21 | <1% | 6...e6 7.a4 Bd7 8.Be2 Nc6 9.Nxc6 Bxc6 10.O-O | — |
| 6.Bg5 | +0,21 | 32% | 6...e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 Qa3 10.f5 | Teoria del Pedone Avvelenato: 6.Bg5 e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 Qa3 10.f5 Nc6 |
| 6.Nb3 | +0,14 | <1% | 6...e6 7.a4 Nc6 8.Be2 d5 9.exd5 exd5 10.Bf3 | — |
| 6.Bc4 | +0,12 | 9% | 6...e6 7.Bb3 b5 8.Be3 Be7 9.a3 O-O 10.f3 | — |

* Probabilità di Maia-2 poco affidabili a questo livello.

| Dopo | Mosse (dalla migliore) | Nota |
| --- | --- | --- |
| 6.f3 | 6...e5 (+0,30), 6...Nc6 (+0,34), 6...e6 (+0,43) | — |
| 6.f3 e5 | 7.Nb3 (+0,38), 7.Nde2 (-0,10), 7.Nf5 (-1,28) | Solo Nb3 tiene: Nf5 perde 1,66 |
| 6.f3 Nc6 | 7.Be3 (+0,51), 7.Bg5 (+0,27), 7.Be2 (+0,24) | — |
| 6.f3 e6 | 7.g4 (+0,46), 7.Be3 (+0,42), 7.a3 (+0,34) | — |
| 6.Be3 | 6...Ng4 (+0,35), 6...e5 (+0,36), 6...e6 (+0,48) | Le prime due risposte sono pari (0,01) |
| 6.Be3 Ng4 | 7.Bc1 (+0,38), 7.Bg5 (+0,22), 7.Qe2 (0,00) | Qd2 (-0,05) regala il vantaggio: si ritira l'alfiere |
| 6.Be3 e5 | 7.Nb3 (+0,34), 7.Nf3 (+0,15), 7.Nde2 (+0,07) | — |
| 6.Be3 e6 | 7.Qd2 (+0,41), 7.f3 (+0,39), 7.Be2 (+0,39) | Contro questa struttura il vantaggio cresce (+0,41) |
| 6.h3 | 6...e5 (+0,22), 6...e6 (+0,27), 6...g6 (+0,40) | ...e5 è la risposta più precisa (+0,22) |
| 6.h3 e5 | 7.Nb3 (+0,25), 7.Nde2 (+0,20), 7.Nf3 (+0,14) | — |
| 6.h3 e6 | 7.g4 (+0,33), 7.Qf3 (+0,25), 7.a4 (+0,20) | — |
| 6.h3 g6 | 7.g4 (+0,41), 7.Be3 (+0,41), 7.g3 (+0,30) | — |

Tra la prima e la quinta mossa spiegata ci sono 0,18: la scelta è di sistema, non di valutazione. Il test critico è dopo 6.Be3 ...Ng4: Bc1 (+0,38) conserva il vantaggio, Bg5 (+0,22) è la ritirata più comune ma costa 0,16.

6.f3 è l'ordine che lascia meno scelte al Nero; 6.h3 (+0,32) e 6.Bd3 (+0,27) cambiano struttura senza perdere quasi nulla.

## Imprecisioni sottili

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

6.h3 è la mossa più difficile da trovare tra le prime: +0,32, a 0,07 dalla migliore, scelta solo dal 3%. Toglie al Nero il salto in g4 e lascia aperte entrambe le strutture.

Imprecisione tipica: dopo 6.f3 ...e6 la mossa naturale Be3 (93%) concede 0,04 rispetto a g4. È poco, ma nella corsa decide i tempi.

## Rapporto tecnico

- Versioni: Stockfish 16 · Maia-2 0.11.0 (modello rapid, cpu) · modello di linguaggio: nessuno (esempio di riferimento)
- Profilo deep · tempo dei motori 879,2 s · nodi analizzati 42 · profondità minima 18 e massima 26
- Nodi sotto la profondità minima: nessuno
- Elo dichiarato 2400 FIDE · Elo Maia-2 2400 · fascia ge2400 · ancora 2400 · confidenza di Maia-2 bassa
- Sezioni omesse: S02 (milestone), S05 (band_2400), S09 (milestone), S10 (band_2400), S11 (milestone), S12 (matrix), S13 (matrix) · assorbite: S04 in S03
- Fasi omesse: E3l2 (milestone), E3l3 (milestone) · nodi omessi: nessuno
- Contenuto teorico: 2 blocchi, 12% delle parole
- Controlli: V01 superato · V02 superato · V03 superato · V04 superato · V05 superato · V06 superato · V07 superato · V08 superato · V09 superato · V10 superato · V11 superato
- Retry: 0
- Rimossi in modalità degradata: nessuno
- Marcati come non verificati: nessuno
- Avvisi: nessuno
- Note del modello: nessuna
- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e asserzione non è controllata.

---

† contenuto teorico, non verificato dai motori
