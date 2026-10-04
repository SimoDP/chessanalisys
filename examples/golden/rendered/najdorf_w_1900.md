# Analisi della posizione: Sicilian Defense: Najdorf Variation

FEN: `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` · Tratto: il Bianco · Giochi con: il Bianco
Elo dichiarato 1900 FIDE → 2025 in scala Lichess usata da Maia-2 · Avversario: 1900 FIDE → 2025
Fascia 1600_2000 · Ancora 1900 · Profilo deep · Stockfish 19 · profondità radice 31

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore.
> Maia-2 è poco affidabile a questo livello (vedi le sezioni sull'avversario).

## Sintesi

Posizione teorica e molto equilibrata: il motore dà al Bianco un vantaggio minimo, +0,34 con la mossa migliore, e circa il 93% di patta. Le cinque mosse spiegate stanno in un intervallo piccolo: tra 6.f3 (+0,34) e 6.Bg5 (+0,04) la differenza è appena 0,30.

**Non devi cercare la mossa migliore: devi scegliere un sistema e giocarlo bene.** Se toccasse al Nero, la valutazione sarebbe -0,07 (migliore ...e6): il tuo vantaggio è quasi solo il tratto, quindi non sprecare tempi. Nessuna delle candidate perde materiale: decide il piano che conosci meglio.

## Radar delle categorie

| Categoria | T (tu)* | R | Nota |
| --- | --- | --- | --- |
| Attività dei pezzi | 100 | 26 | Il Nero ha più pezzi ancora chiusi |
| Struttura pedonale | 100 | 12 | Cambia nelle linee di 6.f3 e 6.Be3 |
| Spazio e centro | 100 | 7 | — |
| Complessità pratica | 80 | 7 | Molte mosse giocabili, nessuna unica |
| Sicurezza del re | 98 | 1 | — |
| Minacce e dinamica | 100 | 1 | — |
| Iniziativa e tempi | 100 | 0 | — |
| Materiale | 100 | 0 | — |
| Transizioni e piani | 100 | 0 | — |

* Punteggi poco affidabili: Maia-2 poco affidabile a questo livello o valutazioni instabili.

Nessuna categoria preoccupa: la tranquillità più bassa è quella della complessità pratica (80), perché quasi ovunque ci sono più mosse giocabili. Pesa di più l'attività dei pezzi (26): il Nero ha quattro pezzi chiusi, tu solo le torri. Nessuna linea filtrata tocca il re.

## I sistemi che puoi scegliere

| Sistema | Prima mossa | Arrocco | Idea | Per chi |
| --- | --- | --- | --- | --- |
| **Attacco inglese** | 6.f3 (+0,34) o 6.Be3 (+0,32) | **Lungo** | Be3 → Qd2 → O-O-O, poi g4 → g5 | Chi vuole attaccare con i pedoni; molta teoria † |
| **Donna in d3** | 6.Qd3 (+0,20) | Varia | La donna difende e4 e lascia aperta la scelta del lato | Chi vuole uscire dalla teoria principale † |
| **Alfiere in d3** | 6.Bd3 (+0,19) | **Corto** | O-O → f4 con l'alfiere che protegge e4 | Chi vuole una posizione solida e piani posizionali † |
| **Aggressivo e teorico** | 6.Bg5 (+0,04) | Varia | Pressione sul cavallo f6, spesso con la spinta del pedone f | Chi conosce bene la teoria † |

Il motore preferisce di pochissimo 6.f3, la mossa consigliata, ma **non esiste una mossa unica migliore**: 6.f3 e 6.Be3 portano di solito alla stessa struttura e la differenza tra loro è 0,02. Le scelte più tranquille, 6.Qd3 e 6.Bd3, costano 0,14 e 0,15.

Come scegliere: se conosci la teoria dell'attacco inglese e ti piacciono le posizioni con arrocchi opposti, gioca 6.f3 o 6.Be3; se preferisci manovrare con il re al sicuro, 6.Bd3 costa poco; 6.Bg5 richiede una preparazione specifica e la lasci per quando l'avrai studiata.

## Dove ti arrocchi

- **Con l'alfiere in e2 si arrocca corto.** Il re è al sicuro; poi alfiere in e3, spinta del pedone f o del pedone a, torri al centro. †
- **Con alfiere in e3, pedone in f3 e donna in d2 si arrocca lungo.** Poi g4 → g5 → h4 contro il re nero. Il Nero di solito arrocca corto e contrattacca con ...b5 → ...b4: è una corsa. †
- **Attenzione alla diagonale a7–g1.** Con l'alfiere in e3, il cavallo in d4 e il re in g1, la donna nera in b6 attacca il cavallo e il pedone b2: se il cavallo si muove, l'alfiere va difeso. Per questo la spinta in f3 con l'arrocco corto richiede cautela. †

Oggi entrambi i re possono ancora arroccare da tutti e due i lati: la scelta del lato è libera e dipende solo dal sistema.

## Cosa vuole ogni pezzo

| Pezzo | Obiettivo tipico | Attenzione |
| --- | --- | --- |
| Pedone e4 | Va protetto: dal cavallo c3, con il pedone in f3, con l'alfiere o la donna in d3 | La presa in e4 del cavallo f6 se il cavallo c3 è sovraccarico o inchiodato † |
| Cavallo d4 | Centro; dopo ...e5 si ritira in **b3**: Nb3 vale +0,30 | Nf5 sembra attivo ma perde 1,38 † |
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
- Contro 6.Be3 la risposta migliore per il motore è ...Ng4 (+0,28), quasi alla pari con ...e5 (+0,31): il cavallo attacca l'alfiere e fa perdere un tempo.
- La spinta ...b5 → ...b4 sul lato di donna caccia il cavallo c3 e toglie protezione a e4. †
- Dopo 6.Bg5 la donna in b6 è un'idea concreta: nella linea del motore 6.Bg5 e6 7.f4 Qb6 8.Qd2 Qxb2 il Nero prende il pedone b2, il **Pedone Avvelenato**.
- Il fianchetto del re nero non è il piano principale della Najdorf: è tipico del **Dragon**, e qui è proprio la mossa che cambia valore da un sistema all'altro. †

| Pezzo nero | Dove va di solito |
| --- | --- |
| Alfiere c8 | **e6** contro d5; con la struttura Scheveningen in b7 o d7 † |
| Cavallo b8 | **d7** a sostegno della spinta del pedone b, oppure **c6** contro il centro † |
| Alfiere f8 | **e7**, poi arrocco corto † |
| Donna | **c7** sulla colonna c, oppure **b6** contro b2 e d4 † |

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

La tabella mostra quanto costa il fianchetto ...g6 contro ciascun sistema. Contro 6.Bd3 non costa nulla (0,00), contro 6.f3 e 6.Be3 costa già 0,33 e 0,40, e contro 6.Bg5 è un errore: ...g6 vale +1,12 invece di +0,05. Lo stesso vale dopo 6.f3 ...e6 7.g4, dove ...g6 perde 1,17. La stessa mossa è buona o cattiva a seconda del sistema: con l'alfiere in d3 il pedone e4 è già protetto e la diagonale lunga del Nero non trova bersagli.

Secondo Maia-2, contro 6.Bg5 sceglie ...e6 il 80% dei giocatori del tuo livello, mentre ...g6 raccoglie appena 1%: l'errore esiste, ma a questo livello si commette di rado.

## Mosse candidate

| Mossa | Valutazione | Scelta a 1900* | Linea del motore | Idea |
| --- | --- | --- | --- | --- |
| **6.f3** ★ | +0,34 | 13% | 6...e5 7.Nb3 Be6 8.Be3 Be7 9.Qd2 | Attacco inglese che evita il salto del cavallo in g4; contro ...e5 segue Nb3 (+0,30) |
| 6.Be3 | +0,32 | 20% | 6...e5 7.Nb3 Be6 8.Qd2 Be7 9.f3 | Attacco inglese diretto; deve fare i conti con ...Ng4 (+0,28) |
| 6.Qd3 | +0,20 | <1% | 6...Nbd7 7.Be2 g6 8.Bg5 Bg7 9.f4 | La donna difende e4; il motore risponde ...Nbd7 e la posizione si pareggia (0,00) |
| 6.Bd3 | +0,19 | 3% | 6...g6 7.f3 e5 8.Nb3 Be6 9.Be3 | Sviluppo tranquillo e arrocco corto; contro ...e5 la valutazione resta +0,15 |
| 6.g3 | +0,15 | 1% | 6...e5 7.Nb3 Be7 8.Bg2 a5 9.Nd2 | — |
| 6.Be2 | +0,15 | 10% | 6...e5 7.Nb3 Be7 8.Be3 Be6 9.Nd5 | — |
| 6.h3 | +0,14 | 3% | 6...e5 7.Nde2 h5 8.g3 Be6 9.Bg2 | — |
| 6.a4 | +0,11 | 4% | 6...e5 7.Nf3 Be7 8.Bg5 Be6 9.Bxf6 | — |
| 6.Bc4 | +0,09 | 9% | 6...e6 7.Bb3 b5 8.Be3 Be7 9.a3 | — |
| 6.f4 | +0,04 | 1% | 6...e5 7.Nf3 Nbd7 8.a4 Be7 9.Bc4 | — |
| 6.Bg5 | +0,04 | 32% | 6...e6 7.f4 Qb6 8.Qd2 Qxb2 9.Rb1 | La più giocata a questo livello (32%); il Nero risponde ...e6 |
| 6.Nb3 | +0,04 | <1% | 6...e6 7.Be2 Nc6 8.a4 Be7 9.Be3 | — |

* Probabilità di Maia-2 poco affidabili a questo livello.

Il motore non vede un vincitore chiaro: tra la prima e l'ultima mossa spiegata ci sono 0,30 pedoni. La linea principale dopo 6.f3 è 6.f3 e5 7.Nb3 Be6 8.Be3 Be7 9.Qd2 O-O; con 6.Be3 si arriva alla stessa posizione cambiando l'ordine delle mosse (6.Be3 e5 7.Nb3 Be6 8.Qd2 Be7 9.f3).

A questo livello conta di più la **conoscenza dei piani** che la scelta tra queste mosse: 6.Be3 e 6.f3 sono intercambiabili, 6.Qd3 e 6.Bd3 sono alternative valide (+0,20 e +0,19).

Le altre mosse della tabella restano tutte entro 0,30 dalla migliore: nessuna è un errore, ma nessuna ha un piano più chiaro dei sistemi spiegati sopra.

## Trappole naturali e mosse difficili

A questo livello Maia-2, il modello del comportamento umano, distingue poco tra i giocatori più forti: le probabilità indicate sono poco affidabili e le indicazioni si basano soprattutto sul motore.

**6.Bg5 è un'alternativa pratica**: la sceglie il 32% dei giocatori del tuo livello e costa 0,30 rispetto alla migliore, ma lungo la sua linea non ci sono mosse obbligate da trovare.

Dopo 6.f3 ...e5 la ritirata del cavallo va scelta bene: Nb3 tiene il vantaggio, Nde2 costa già 0,49 e la mossa d'attacco Nf5, che sembra la più attiva, perde 1,38.

Dopo 6.Be3 ...Ng4 la ritirata naturale è Bg5, scelta dal 53% dei giocatori: qui l'istinto è giusto, perché vale quanto Bc1 (+0,31), mentre Qd2 perde 0,46.

## Minacce invisibili al tuo livello

Nessuna linea del motore entra nel referto a questo livello: in tutto l'albero analizzato non c'è una minaccia, né per te né per il Nero, il cui rischio pratico superi la soglia del tuo Elo, e nessuna perdita decisiva è nascosta. Se passassi la mossa, il Nero otterrebbe soltanto -0,07 con ...e6: non ha colpi pronti.

Anche la candidata più lontana dal motore, 6.Bg5, cede appena 0,30, e nessuna linea forzata la trasforma in uno svantaggio serio. I pericoli di questa posizione sono di piano, non tattici: li trovi nelle sezioni sui sistemi e sulle idee del Nero.

## Come ragionare

1. **Scegli il sistema** (attacco inglese o alfiere in d3) e quindi il lato dell'arrocco. †
2. **Proteggi e4** prima di ogni mossa non forzata. †
3. **Prima di muovere, controlla la donna nera in b6 e la presa in e4**: sono le due tattiche che il Nero cerca più spesso. †
4. Se il Nero gioca ...e5, ritira il cavallo in b3 (+0,30) e punta alla casa d5.
5. Se il cavallo nero salta in g4, non rispondere d'istinto: confronta le ritirate dell'alfiere prima di muovere. †
6. Non perdere tempi: con il Nero al tratto la posizione sarebbe -0,07, il tuo vantaggio è il tratto.

## Rapporto tecnico

- Versioni: Stockfish 19 · Maia-2 0.11.0 (modello rapid, cpu) · modello di linguaggio: nessuno (esempio di riferimento)
- Profilo deep · tempo dei motori 1429,3 s · nodi analizzati 62 · profondità minima 18 e massima 31
- Nodi sotto la profondità minima: nessuno
- Elo dichiarato 1900 FIDE · Elo Maia-2 2025 · fascia 1600_2000 · ancora 1900 · confidenza di Maia-2 bassa
- Sezioni omesse: S11 (elo<2000), S12 (matrix), S13 (matrix) · assorbite: nessuna
- Fasi omesse: nessuna · nodi omessi: nessuno
- Contenuto teorico: 56 blocchi, 37% delle parole
- Controlli: V01 superato · V02 superato · V03 superato · V04 superato · V05 superato · V06 superato · V07 superato · V08 superato · V09 superato · V10 superato · V11 superato
- Retry: 0
- Rimossi in modalità degradata: nessuno
- Marcati come non verificati: nessuno
- Avvisi: nessuno
- Note del modello: nessuna
- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e asserzione non è controllata.

---

† contenuto teorico, non verificato dai motori
