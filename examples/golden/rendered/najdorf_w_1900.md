# Analisi della posizione: Sicilian Defense: Najdorf Variation

FEN: `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` · Tratto: il Bianco · Giochi con: il Bianco
Elo dichiarato 1900 FIDE → 2025 in scala Lichess usata da Maia-2 · Avversario: 1900 FIDE → 2025
Fascia 1600_2000 · Ancora 1900 · Profilo deep · Stockfish 16 · profondità radice 25

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore.
> Maia-2 è poco affidabile a questo livello (vedi le sezioni sull'avversario).

## Sintesi

Posizione teorica e molto equilibrata: il motore dà al Bianco un vantaggio minimo, +0,39 con la mossa migliore, e circa il 95% di patta. Le cinque mosse spiegate stanno tutte in un intervallo piccolissimo: tra 6.f3 (+0,39) e 6.Bg5 (+0,21) la differenza è appena 0,18.

**Non devi cercare la mossa migliore: devi scegliere un sistema e giocarlo bene.** Se toccasse al Nero, la valutazione sarebbe +0,01 (migliore ...e5): il tuo vantaggio è quasi solo il tratto, quindi non sprecare tempi. Nessuna delle candidate perde materiale: decide il piano che conosci meglio.

## I sistemi che puoi scegliere

| Sistema | Prima mossa | Arrocco | Idea | Per chi |
| --- | --- | --- | --- | --- |
| **Attacco inglese** | 6.Be3 (+0,34) o 6.f3 (+0,39) | **Lungo** | Be3 → Qd2 → O-O-O, poi g4 → g5 | Chi vuole attaccare con i pedoni; molta teoria † |
| **Classico** | 6.Be2 (+0,25) o 6.Bd3 (+0,27) | **Corto** | Be2 → Be3 → O-O → f4 oppure la spinta del pedone a | Chi vuole una posizione solida e piani posizionali † |
| **Spinta di pedone** | 6.h3 (+0,32) | Varia | g4 → g5 senza la spinta in f3 | Chi conosce già l'attacco inglese † |
| **Aggressivo e teorico** | 6.Bg5 (+0,21) | Varia | Pressione sul cavallo f6, spesso con la spinta del pedone f | Chi conosce bene la teoria † |

Il motore preferisce di pochissimo 6.f3, la mossa consigliata, ma **non esiste una mossa unica migliore**: 6.f3 e 6.Be3 portano di solito alla stessa struttura e la differenza tra loro è 0,05. Se vuoi una posizione più tranquilla, 6.Be2 costa solo 0,14.

Come scegliere: se conosci la teoria dell'attacco inglese e ti piacciono le posizioni con arrocchi opposti, gioca 6.f3 o 6.Be3; se preferisci manovrare con il re al sicuro, il sistema classico costa pochissimo; 6.Bg5 richiede una preparazione specifica e la lasci per quando l'avrai studiata.

## Dove ti arrocchi

- **Con l'alfiere in e2 si arrocca corto.** Il re è al sicuro; poi alfiere in e3, spinta del pedone f o del pedone a, torri al centro. †
- **Con alfiere in e3, pedone in f3 e donna in d2 si arrocca lungo.** Poi g4 → g5 → h4 contro il re nero. Il Nero di solito arrocca corto e contrattacca con ...b5 → ...b4: è una corsa. †
- **Attenzione alla diagonale a7–g1.** Con l'alfiere in e3, il cavallo in d4 e il re in g1, la donna nera in b6 attacca il cavallo e il pedone b2: se il cavallo si muove, l'alfiere va difeso. Per questo la spinta in f3 con l'arrocco corto richiede cautela. †

Oggi entrambi i re possono ancora arroccare da tutti e due i lati: la scelta del lato è libera e dipende solo dal sistema.

## Cosa vuole ogni pezzo

| Pezzo | Obiettivo tipico | Attenzione |
| --- | --- | --- |
| Pedone e4 | Va protetto: dal cavallo c3, con il pedone in f3, con l'alfiere o la donna in d3 | La presa in e4 del cavallo f6 se il cavallo c3 è sovraccarico o inchiodato † |
| Cavallo d4 | Centro; dopo ...e5 si ritira in **b3**: Nb3 vale +0,38 | Nf5 sembra attivo ma perde 1,66 † |
| Cavallo c3 | Difende e4 e controlla d5; dopo la spinta del Nero in e5 il sogno è il salto in **d5** | La spinta ...b5 → ...b4 lo scaccia † |
| Alfiere c1 | **e3** (flessibile) o **g5** (pressione sul cavallo f6, linee affilate) | Non lasciarlo senza difesa sulla diagonale a7–g1 † |
| Alfiere f1 | **e2** (solido), **d3** o **c4** (aggressivo) | In c4 invita la spinta del pedone b † |
| Donna | **d2** con l'arrocco lungo, **e2** con l'arrocco corto | La donna nera in b6 attacca b2 e il cavallo d4 † |
| Torri | Arrocco corto: in f1 e d1. Arrocco lungo: torre in **g1** per sostenere la spinta del pedone g | Non lasciare la torre a1 senza un piano † |
| Pedoni f, g e h | Pedone in f3 a sostegno di e4; g4 → g5 nell'attacco inglese | La spinta in f3 indebolisce la diagonale a7–g1 † |

Oggi i tuoi due alfieri sono ancora a casa, come tre pezzi minori neri, e la colonna d è aperta davanti al tuo re: sviluppo e arrocco vengono prima di tutto.

## Cosa cerca il Nero

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

- ...e5 è la risposta più naturale contro quasi tutti i sistemi (contro 6.f3 Maia-2 la dà al 74%): occupa il centro, ma lascia **d5 come buco** e il pedone d6 arretrato.
- ...e6 porta alla struttura **Scheveningen**: più elastica, prepara ...b5 → ...Bb7 → ...Be7 → ...Qc7 e talvolta la spinta in d5. †
- Contro 6.Be3 la risposta migliore per il motore è ...Ng4 (+0,35), alla pari con ...e5 (+0,36): il cavallo attacca l'alfiere e fa perdere un tempo.
- La spinta ...b5 → ...b4 sul lato di donna caccia il cavallo c3 e toglie protezione a e4. †
- Dopo 6.Bg5 la donna in b6 è un'idea concreta: nella linea del motore 6.Bg5 e6 7.f4 Qb6 8.Qd2 Qxb2 il Nero prende il pedone b2, il **Pedone Avvelenato**.
- Il fianchetto del re nero non è il piano principale della Najdorf: è tipico del **Dragon**. †

| Pezzo nero | Dove va di solito |
| --- | --- |
| Alfiere c8 | **e6** contro d5; con la struttura Scheveningen in b7 o d7 † |
| Cavallo b8 | **d7** a sostegno della spinta del pedone b, oppure **c6** contro il centro † |
| Alfiere f8 | **e7**, poi arrocco corto † |
| Donna | **c7** sulla colonna c, oppure **b6** contro b2 e d4 † |

| Dopo… | Migliore del Nero | ...e5 | Costo |
| --- | --- | --- | --- |
| 6.f3 | ...e5 (+0,30) | +0,30 | 0,00 |
| 6.Be3 | ...Ng4 (+0,35) | +0,36 | 0,01 |
| 6.h3 | ...e5 (+0,22) | +0,22 | 0,00 |
| 6.Bd3 | ...Nbd7 (+0,26) | +0,29 | 0,03 |
| 6.Bg5 | ...e6 (+0,21) | +1,07 | 0,86 |

La tabella mostra quanto costa ...e5 contro ciascun sistema. Contro 6.f3, 6.Be3, 6.h3 e 6.Bd3 è una risposta normale (al massimo 0,03), mentre contro 6.Bg5 è un errore: ...e5 vale +1,07 invece di +0,21, cioè perde 0,86. La stessa mossa è buona o cattiva a seconda del sistema: contro l'alfiere in g5 il Nero deve rispondere ...e6.

Secondo Maia-2, contro 6.Bg5 sceglie ...e5 il 10% dei giocatori del tuo livello, mentre la risposta corretta raccoglie 80%.

## Mosse candidate

| Mossa | Valutazione | Scelta a 1900* | Linea del motore | Idea |
| --- | --- | --- | --- | --- |
| **6.f3** ★ | +0,39 | 13% | 6...e5 7.Nb3 Be6 8.Be3 h5 9.Nd5 | Attacco inglese che evita il salto del cavallo in g4; contro ...e5 segue Nb3 (+0,38) |
| 6.Be3 | +0,34 | 20% | 6...e5 7.Nb3 Be6 8.h3 Nbd7 9.g4 | Attacco inglese diretto; deve fare i conti con ...Ng4 (+0,35) |
| 6.h3 | +0,32 | 3% | 6...e5 7.Nde2 h5 8.g3 Be7 9.Bg2 | Prepara la spinta del pedone g senza f3; dopo ...e6 segue g4 (+0,33) |
| 6.Bd3 | +0,27 | 3% | 6...e5 7.Nde2 Be7 8.O-O O-O 9.Ng3 | Sviluppo tranquillo e arrocco corto; contro ...e5 il cavallo va in e2 (+0,29) |
| 6.Be2 | +0,25 | 10% | 6...e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 | — |
| 6.f4 | +0,25 | 1% | 6...e5 7.Nf3 Qc7 8.a4 Be7 9.Bd3 | — |
| 6.g3 | +0,25 | 1% | 6...e5 7.Nb3 Be7 8.Bg5 Nbd7 9.a4 | — |
| 6.a4 | +0,24 | 4% | 6...e5 7.Nf3 Be7 8.Bg5 Be6 9.Bxf6 | — |
| 6.Qd3 | +0,21 | <1% | 6...e6 7.a4 Bd7 8.Be2 Nc6 9.Nxc6 | — |
| 6.Bg5 | +0,21 | 32% | 6...e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 | La più giocata a questo livello (32%); il Nero risponde ...e6 |
| 6.Nb3 | +0,14 | <1% | 6...e6 7.a4 Nc6 8.Be2 d5 9.exd5 | — |
| 6.Bc4 | +0,12 | 9% | 6...e6 7.Bb3 b5 8.Be3 Be7 9.a3 | — |

* Probabilità di Maia-2 poco affidabili a questo livello.

Il motore non vede un vincitore chiaro: tra la prima e l'ultima mossa spiegata ci sono 0,18 pedoni. La linea principale dopo 6.f3 è 6.f3 e5 7.Nb3 Be6 8.Be3 h5 9.Nd5 Bxd5: il Bianco ottiene la casa d5 in cambio dell'alfiere nero.

A questo livello conta di più la **conoscenza dei piani** che la scelta tra queste mosse: 6.Be3 e 6.f3 sono intercambiabili, 6.h3 e 6.Bd3 sono alternative valide (+0,32 e +0,27).

Le altre mosse della tabella restano tutte entro 0,27 dalla migliore: nessuna è un errore, ma nessuna ha un piano più chiaro dei sistemi spiegati sopra.

## Trappole naturali e mosse difficili

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

**6.h3 è una mossa difficile**: il motore la mette tra le prime tre (+0,32, solo 0,07 dalla migliore), ma a questo livello la sceglie appena il 3% dei giocatori.

Dopo 6.f3 ...e5 la ritirata del cavallo va scelta bene: Nb3 tiene il vantaggio, Nde2 costa già 0,48 e la mossa d'attacco Nf5, che sembra la più attiva, perde 1,66.

Dopo 6.Be3 ...Ng4 la ritirata naturale è Bg5, scelta dal 53%, ma il motore preferisce Bc1 (+0,38); Qd2 perde 0,43.

## Come ragionare

1. **Scegli il sistema** (attacco inglese o classico) e quindi il lato dell'arrocco. †
2. **Proteggi e4** prima di ogni mossa non forzata. †
3. **Prima di muovere, controlla la donna nera in b6 e la presa in e4**: sono le due tattiche che il Nero cerca più spesso. †
4. Se il Nero gioca ...e5, ritira il cavallo in b3 (+0,38) e punta alla casa d5.
5. Se il cavallo nero salta in g4, non rispondere d'istinto: confronta le ritirate dell'alfiere prima di muovere. †
6. Non perdere tempi: con il Nero al tratto la posizione sarebbe +0,01, il tuo vantaggio è il tratto.

## Rapporto tecnico

- Versioni: Stockfish 16 · Maia-2 0.11.0 (modello rapid, cpu) · modello di linguaggio: nessuno (esempio di riferimento)
- Profilo deep · tempo dei motori 851,8 s · nodi analizzati 32 · profondità minima 18 e massima 26
- Nodi sotto la profondità minima: nessuno
- Elo dichiarato 1900 FIDE · Elo Maia-2 2025 · fascia 1600_2000 · ancora 1900 · confidenza di Maia-2 bassa
- Sezioni omesse: S02 (milestone), S09 (milestone), S11 (elo<2000), S12 (matrix), S13 (matrix) · assorbite: nessuna
- Fasi omesse: E3l2 (milestone), E3l3 (milestone) · nodi omessi: nessuno
- Contenuto teorico: 56 blocchi, 42% delle parole
- Controlli: V01 superato · V02 superato · V03 superato · V04 superato · V05 superato · V06 superato · V07 superato · V08 superato · V09 superato · V10 superato · V11 superato
- Retry: 0
- Rimossi in modalità degradata: nessuno
- Marcati come non verificati: nessuno
- Avvisi: nessuno
- Note del modello: nessuna
- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e asserzione non è controllata.

---

† contenuto teorico, non verificato dai motori
