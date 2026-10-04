# Analisi della posizione: Sicilian Defense: Najdorf Variation

FEN: `rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6` · Tratto: il Bianco · Giochi con: il Bianco
Elo dichiarato 1500 FIDE → 1700 in scala Lichess usata da Maia-2 · Avversario: 1500 FIDE → 1700
Fascia 1200_1600 · Ancora 1500 · Profilo deep · Stockfish 19 · profondità radice 31

> Convenzione: le valutazioni sono in pedoni dal tuo punto di vista (positivo = meglio per te).
> Gli esempi di riferimento per questo livello non sono ancora stati validati da un giocatore.

## In una frase

La posizione è equilibrata: vince chi sviluppa meglio e non regala materiale. Il motore dà al Bianco un vantaggio minimo (+0,34), quindi **stai bene: devi solo giocare in modo ordinato**. Se toccasse al Nero la valutazione sarebbe pari (-0,07): il tuo piccolo vantaggio è il tratto.

## Radar semplificato

| Categoria | T (tu) | R | Nota |
| --- | --- | --- | --- |
| Attività dei pezzi | 100 | 30 | — |
| Struttura pedonale | 100 | 13 | — |
| Spazio e centro | 100 | 11 | — |
| Complessità pratica | 77 | 8 | — |
| Sicurezza del re | 98 | 1 | — |

Nessuna categoria è da attenzione. Conta di più sviluppare i pezzi (rilevanza 30): il Nero ne ha ancora quattro chiusi. Più delicata è la scelta tra tante mosse giocabili (77).

## Le tre cose da fare adesso

1. **Sviluppa i pezzi**: prima gli alfieri, poi la donna se serve. †
2. **Arrocca presto**: il lato dipende dal sistema che scegli, come vedi sotto. †
3. **Tieni protetto il pedone e4.** †

**La mossa consigliata: 6.f3.** Il motore la valuta +0,34, ma non c'è una mossa unica migliore: anche 6.Be3 (+0,32) va benissimo e porta allo stesso piano. Con questi due sistemi il re di solito va **a sinistra, con l'arrocco lungo**.

**Piano semplice:** f3 → Be3 → Qd2 → O-O-O, poi spingi i pedoni del lato di re contro l'arrocco nero. †

Se preferisci arroccare **corto** e avere una posizione più tranquilla, 6.Be2 costa solo 0,19: poi Be2 → Be3 → O-O.

6.Bg5 è la mossa che si gioca più spesso al tuo livello (29%), ma porta a linee molto teoriche: tienila per più avanti.

## Cosa vuole ogni pezzo

- **Cavallo d4:** sta bene al centro. Se il Nero gioca ...e5 il cavallo è attaccato: **ritiralo in b3** (Nb3), non lasciarlo catturare. †
- **Cavallo c3:** protegge e4 e controlla d5. Dopo la spinta del Nero in e5, la casa **d5** diventa un punto debole: è il tuo obiettivo. †
- **Alfiere c1:** va in e3, dietro al cavallo d4. †
- **Alfiere f1:** va in e2 se arrocchi corto; con l'arrocco lungo può aspettare. †
- **Re:** arrocca appena possibile, dal lato del tuo sistema. †

Oggi i tuoi due alfieri sono ancora a casa: sviluppali prima di tutto il resto.

## Cosa fa il Nero

- Gioca ...e5 per prendersi il centro: è la risposta più frequente (53% contro 6.f3).
- Oppure ...e6, più elastico. †
- Spesso spinge ...b5 sul lato di donna per attaccare il cavallo c3. †
- Contro 6.Be3 può saltare con il cavallo: ...Ng4 attacca l'alfiere (+0,28).

Quasi sempre il Nero arrocca corto: se tu arrocchi lungo, la partita diventa una corsa tra gli attacchi di pedoni sui due lati. †

## Mosse candidate

| Mossa | Valutazione | Scelta a 1500 | Per chi |
| --- | --- | --- | --- |
| **6.f3** ★ | +0,34 | 8% | Consigliata: piano semplice e chiaro, anche se a questo livello è poco giocata (8%) |
| 6.Be3 | +0,32 | 17% | Stesso piano; la sceglie il 17% dei giocatori del tuo livello |
| 6.Qd3 | +0,20 | <1% | — |
| 6.Bd3 | +0,19 | 9% | — |
| 6.Bg5 | +0,04 | 29% | La più giocata (29%), ma molto teorica: meglio più avanti |

Le mosse del motore sono vicinissime: tra 6.f3 e 6.Bg5 si perdono solo 0,30. Scegli quella di cui capisci il piano.

## Attenzione a questi errori tipici

- Dopo ...e5, **non lasciare il cavallo d4** dove il pedone può catturarlo. †
- La ritirata giusta è in b3: Nf5 sembra attivo ma perde 1,38.
- Non lasciare **e4 senza protezione**: il cavallo nero in f6 può catturarlo. †
- Non mandare la donna a mangiare pedoni lontani: è il modo più comune di perdere tempo e pezzi. †
- Non lanciare attacchi di pedoni **prima di aver sviluppato i pezzi**. †
- 6.Bg5 è la mossa più giocata al tuo livello (29%): costa 0,30 rispetto alla migliore, ma è un'**alternativa pratica**, senza mosse difficili da trovare. Se la giochi, studia la risposta ...e6.

## Minacce invisibili al tuo livello

Nessuna minaccia nascosta: nessuna linea del motore è pericolosa al tuo livello. Anche con una mossa in più il Nero otterrebbe solo -0,07: puoi pensare con calma al tuo piano.

## Prima di ogni mossa, controlla

1. Cosa minaccia l'avversario con la sua ultima mossa? †
2. Tutti i miei pezzi sono protetti? †
3. Posso sviluppare un pezzo o arroccare? †
4. C'è una cattura o uno scacco che mi conviene? †
5. Il pedone e4 è ancora protetto? †

## Rapporto tecnico

- Versioni: Stockfish 19 · Maia-2 0.11.0 (modello rapid, cpu) · modello di linguaggio: nessuno (esempio di riferimento)
- Profilo deep · tempo dei motori 1096,1 s · nodi analizzati 41 · profondità minima 18 e massima 31
- Nodi sotto la profondità minima: nessuno
- Elo dichiarato 1500 FIDE · Elo Maia-2 1700 · fascia 1200_1600 · ancora 1500 · confidenza di Maia-2 normale
- Sezioni omesse: S11 (elo<2000), S12 (matrix), S13 (matrix) · assorbite: S04 in S03
- Fasi omesse: nessuna · nodi omessi: nessuno
- Contenuto teorico: 21 blocchi, 43% delle parole
- Controlli: V01 superato · V02 superato · V03 superato · V04 superato · V05 superato · V06 superato · V07 superato · V08 superato · V09 superato · V10 superato · V11 superato
- Retry: 0
- Rimossi in modalità degradata: nessuno
- Marcati come non verificati: nessuno
- Avvisi: nessuno
- Note del modello: nessuna
- Le asserzioni tipizzate sono verificate contro il pacchetto; la corrispondenza tra frase e asserzione non è controllata.

---

† contenuto teorico, non verificato dai motori
