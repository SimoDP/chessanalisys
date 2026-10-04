---
id: "najdorf_w_1900"
anchor: "1900"
fen: "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
user_color: "w"
source: "Esempio di output ideale — Najdorf, Bianco, 1900.md"
status: "raw_v0"
validated: false
corrections:
  - "§6: ...Ng4 contro 6.Be3 è la risposta migliore per il motore (+0,33 contro +0,35 di ...e5), non la seconda (coerente con la tabella di ...Nc6 e con il raw 2400)"
  - "§6: il fianchetto ...g6 compare nelle linee del motore anche contro 6.Bc4 (tabella §7), non solo contro 6.Bd3"
  - "§5: «(o f3, f5, de2)» → «(o in f3 o e2; oppure avanza in f5)»: «de2» era un refuso e f5 non è una ritirata"
  - "§3: «Pressione su e6/f6, attacco in c4» → bersagli corretti dei due alfieri"
  - "§3: giudizio «per un 1900 la scelta più equilibrata è 6.Be3» marcato non vincolante (D-29)"
needs_review:
  - "S08: da scrivere con i dati di Maia-2"
  - "T3: 6.Be2 e5 7.Nb3 (+0,24, nodo dopo 7.Nb3) e il raw 2400 (+0,30, nodo dopo 7...Be7) sono nodi diversi: non è un errore (D-40)"
---

# Esempio di output ideale — Najdorf, mossa 6, Bianco, 1900 FIDE

`rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` *1.e4 c5 2.Nf3 d6 3.d4 cxd4 4.Nxd4 Nf6 5.Nc3 a6 — tocca al Bianco.*

> **Stato (raw v0, corretto in v0.9.1).** Dati di Stockfish **reali** (Stockfish 16, profondità ≈ 17-22), valori in pedoni dal punto di vista del Bianco. Campi `[MAIA]` = segnaposto. Radar illustrativo. Parti teoriche non validate. Questo file è materiale di partenza per il fewshot (documentazione §8-bis.4): **non** va usato come esempio nel prompt. I commenti `<!-- Sxx -->` indicano la sezione di destinazione (§8.2-ter).

## 1. Sintesi  <!-- S01 -->

Posizione teorica e molto equilibrata: il Bianco ha un vantaggio minimo (+0,2 / +0,4 pedoni a seconda della mossa), con circa il 92% di patta secondo il motore. Quasi tutte le mosse di sviluppo stanno nello stesso intervallo di 0,2 pedoni. **Non devi cercare "la mossa migliore": devi scegliere un sistema e giocarlo bene.**

Se toccasse al Nero, la valutazione sarebbe circa 0,0 (migliore: ...e5). Il tuo vantaggio è quindi quasi solo il tratto: non sprecare tempi.

## 2. Radar delle categorie (valori illustrativi)  <!-- S02 (da M3: escluso dal fewshot fino ad allora) -->

| Categoria | T (tu) | R | Nota |
| --- | --- | --- | --- |
| Iniziativa e tempo | 70 | 70 | Chi sviluppa meglio e chi si arrocca per primo decide |
| Attività dei pezzi | 78 | 60 | Gli alfieri e il cavallo in d4 sono i pezzi chiave |
| Minacce e dinamismo | 82 | 50 | Attenzione a ...Qb6 e ...Nxe4 |
| Struttura pedonale | 85 | 45 | e4 da proteggere; d6 nero potenziale bersaglio dopo ...e5 |
| Sicurezza del re | 88 | 25 | Nessuna minaccia immediata (analisi con Nero al tratto ≈ 0,0) |
| Spazio | 80 | 30 | Leggero vantaggio centrale, nulla di decisivo |

## 3. I tre sistemi che puoi scegliere  <!-- S03 -->

| Sistema | Prima mossa | SF | Arrocco | Idea | Per chi |
| --- | --- | --- | --- | --- | --- |
| **Attacco inglese** | 6.Be3 | +0,37 | **Lungo** | f3, Qd2, O-O-O, poi g4-g5 | Chi vuole attaccare con i pedoni; molta teoria |
| **Classico** | 6.Be2 | +0,22 | **Corto** | O-O, Be3, f4 o a4 | Chi vuole una posizione solida e piani posizionali |
| **Aggressivo-teorico** | 6.Bg5 / 6.Bc4 | +0,29 / +0,23 | Varia | Bg5: pressione sul cavallo f6; Bc4: alfiere puntato su f7 ed e6 | Chi conosce bene la teoria |

Alternative pratiche: 6.h3 (+0,35, idea g4-g5 senza Be3) e 6.g3 (+0,22, fianchetto). `[MAIA]` mossa naturale a 1900 vs. mossa migliore: da riempire.

<!-- Giudizio non vincolante (D-29): nel fewshot vale la raccomandazione calcolata (§4.3). -->
**Per un 1900 la scelta più equilibrata è 6.Be3**: ha la migliore valutazione del motore e piani molto concreti. Costa studio di teoria. In alternativa 6.Be2 è più semplice da gestire.

## 4. Dove ti arrocchi  <!-- S04 -->

- **Con Be2 → arrocco corto** (O-O). Re al sicuro, poi Be3, f4 o a4 e Rf1/Rd1.
- **Con Be3 + f3 + Qd2 → arrocco lungo** (O-O-O). Re a sinistra, poi g4-g5 e h4 contro il re nero. Il Nero di solito arrocca corto e contrattacca con ...b5-b4: è una corsa.
- **Attenzione alla diagonale a7–g1.** Con Be3 e Nd4 sulla diagonale e il re in g1, ...Qb6 attacca Nd4 e b2: se il cavallo si muove, Be3 deve essere difeso, altrimenti c'è anche lo scacco in diagonale. Per questo f3 + Be3 + arrocco corto richiede cautela.

## 5. Cosa vuole ogni pezzo  <!-- S05 -->

| Pezzo | Obiettivo tipico | Attenzione |
| --- | --- | --- |
| Pedone e4 | Va protetto (Nc3, f3, Bd3 o Qd3) | ...Nxe4 se Nc3 è sovraccarico o inchiodato |
| Cavallo d4 | Centro; dopo ...e5 si ritira in **b3** (o in f3 o e2; oppure avanza in f5) | Non lasciarlo bersaglio di ...Qb6 |
| Cavallo c3 | Difende e4, controlla d5; dopo ...e5 il sogno è **Nd5** | ...b5-b4 lo scaccia |
| Alfiere c1 | **e3** (flessibile) o **g5** (mette pressione su Nf6, linee teoriche affilate) | Non lasciarlo senza difesa sulla diagonale a7–g1 |
| Alfiere f1 | **e2** (solido), **d3** o **c4** (aggressivo, spesso dopo ...e6 si va in b3) | c4 invita ...b5 |
| Donna | **d2** (con O-O-O) o e2 (arrocco corto) | ...Qb6 con attacco su b2 e d4 |
| Torri | Arrocco corto: Rf1/Rd1. Arrocco lungo: **Rg1** per g4-g5 | Non lasciare la torre a1 senza piani |
| Re | Vedi §4 | Diagonale a7–g1, colonna c con O-O-O |
| Pedoni f/g/h | f3 (sostegno a e4), g4-g5 nell'Inglese | f3 indebolisce la diagonale a7–g1 |

## 6. Cosa cerca il Nero  <!-- S06 -->

- **...e5** (Najdorf classico): occupa il centro, ma lascia **d5 come buco** e d6 arretrato. Segue ...Be6, ...Be7, ...O-O, spesso ...b5.
- **...e6** (struttura Scheveningen): più elastica, prepara ...b5, ...Bb7, ...Be7, ...Qc7 e eventualmente ...d5.
- **...Ng4** contro 6.Be3: per il motore è la risposta migliore (+0,33), di poco davanti a ...e5 (+0,35); colpisce l'alfiere e fa perdere un tempo.
- **...b5-b4** nel lato di donna per cacciare Nc3 e togliere protezione a e4.
- **...Qb6** (specie dopo 6.Bg5 e6 7.f4): attacca Nd4 e b2.
- Il fianchetto ...g6 / ...Bg7 non è il piano principale nella Najdorf (è tipico del Dragon): nelle linee del motore compare solo in sistemi secondari: 6.Bd3 g6 e, più avanti nella variante, 6.Bc4 b5 7.Bd5 Nxd5 8.exd5 g6.

### Dove vanno i pezzi neri  <!-- S06 (la tabella di ...Nc6 è T3) -->

*Valori di Stockfish dal punto di vista del Bianco: più basso significa meglio per il Nero.*

| Pezzo nero | Dove va di solito | Dato del motore |
| --- | --- | --- |
| Alfiere c8 | **e6**: contrasta d5 e prepara ...Bxc4 o ...Bxb3. Con ...e6 invece va in b7 o d7 | Contro l'Inglese (6.Be3 e5 7.Nb3) ...Be6 è la migliore (+0,33) |
| Cavallo b8 | **d7** (sostiene ...b5 e ...Qc7) oppure **c6** (pressione sul centro) | Dipende dal sistema, vedi sotto |
| Alfiere f8 | **e7**, poi arrocco corto | Contro 6.Be2 e5 7.Nb3, ...Be7 è la migliore (+0,24) |
| Donna | **c7** (sostiene ...b5 e ...e5, controlla la colonna c) o **b6** |  |
| Re | Arrocco corto, di solito dopo ...Be7 |  |

**...Nc6 dipende dal sistema scelto dal Bianco:**

| Dopo… | Migliore del Nero | ...Nc6 | Costo di ...Nc6 |
| --- | --- | --- | --- |
| 6.Be3 (subito) | ...Ng4 (+0,33) | +0,41 | ≈ 0,1 |
| 6.Be3 e5 7.Nb3 | ...Be6 (+0,33) | +0,86 | **≈ 0,5: impreciso** |
| 6.Be2 e5 7.Nb3 | ...Be7 (+0,24) | +0,34 | ≈ 0,1 |
| 6.f4 e5 7.Nb3 | ...Nbd7 (+0,06) | +0,09 | ≈ 0 |

Per te come Bianco, questo significa: contro l'attacco inglese, se il Nero risponde con ...Nc6 dopo ...e5 e Nb3 ha già perso circa mezzo pedone di valutazione. Contro i sistemi più tranquilli (6.Be2, 6.f4), ...Nc6 è invece una risposta normale. `[MAIA]` quanto è frequente ...Nc6 contro ciascun sistema a 1900: da riempire.

## 7. Mosse candidate (Stockfish, +, tratto Bianco)  <!-- S07 (T1) -->

| Mossa | SF | Linea del motore | Idea |
| --- | --- | --- | --- |
| **6.Be3** | +0,37 | ...e5 7.Nb3 Be7 8.f3 Be6 9.Qd2 | Attacco inglese |
| 6.f3 | +0,37 | ...e5 7.Nb3 Be7 8.Be3 Be6 9.Qd2 | Stessa posizione per trasposizione |
| 6.h3 | +0,35 | ...e5 7.Nb3 Be7 8.g4 h6 9.Be3 | g4 senza f3 |
| 6.Bg5 | +0,29 | ...e6 | Linee teoriche affilate |
| 6.Nb3 | +0,25 | ...e6 7.g4 b5 8.g5 b4 9.Na4 | Attacco immediato |
| 6.Bd3 | +0,25 | ...g6 7.h3 Bg7 8.Be3 O-O 9.O-O | Linea secondaria |
| 6.Bc4 | +0,23 | ...b5 7.Bd5 Nxd5 8.exd5 g6 | Attacco in c4 |
| 6.a4 | +0,23 | ...e5 7.Nf3 Be7 8.Bg5 | Frena ...b5 |
| 6.g3 | +0,22 | ...e5 7.Nb3 Be7 8.Bg5 Be6 | Fianchetto |
| **6.Be2** | +0,22 | ...e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 | Sistema classico |
| 6.f4 | +0,20 | ...e5 7.Nb3 Nc6 8.f5 | Attacco con i pedoni |
| 6.Rg1 | +0,17 | ...e5 7.Nb3 Be6 8.g4 d5 | Spinta g4 immediata |

Il motore non vede un chiaro vincitore: la differenza tra la mossa migliore e l'ultima è circa 0,2 pedoni. A 1900 conta di più la **conoscenza dei piani** che la scelta fra queste mosse.

## 8. Trappole naturali e mosse difficili — `[MAIA]`  <!-- S08 -->

Qui Maia a 1900 indicherà quali mosse "sembrano" naturali ma peggiorano la posizione, e quali mosse forti sono difficili da trovare. Da riempire quando Maia sarà collegato.

## 9. Come ragionare in questa posizione  <!-- S10 -->

1. **Scegli il sistema** (Inglese o Classico) e quindi il lato dell'arrocco.
2. **Proteggi e4** prima di ogni mossa non forzata.
3. **Prima di muovere, controlla ...Qb6 e ...Nxe4**: sono le due tattiche che il Nero cerca più spesso.
4. Se il Nero gioca **...e5**, ritira il cavallo in b3 e punta a **d5**.
5. Non perdere tempi: il tuo vantaggio è il tratto.
