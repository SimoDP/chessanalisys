---
id: "najdorf_w_1500"
anchor: "1500"
fen: "rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6"
user_color: "w"
source: "Esempi di output ideale — Najdorf, Bianco: 1500 e 2400.md (Parte A)"
status: "raw_v0"
validated: false
corrections:
  - "Nessuna correzione di contenuto: aggiunti intestazione, marcatori di sezione e note di conversione"
needs_review:
  - "S03: lato di arrocco per sistema (S04 assorbita, assente nel raw)"
  - "S03: raccomandazione da allineare a quella calcolata (D-29)"
  - "S08: con dati di Maia-2 aggiungere le trappole naturali reali a 1500"
---

# Esempio di output ideale — Najdorf, mossa 6, Bianco, 1500 FIDE

`rnbqkb1r/1p2pppp/p2p1n2/8/3NP3/2N5/PPP2PPP/R1BQKB1R w KQkq - 0 6`

> **Stato (raw v0, corretto in v0.9.1).** Dati di Stockfish **reali** (Stockfish 16, profondità ≈ 17-22), valori in pedoni dal punto di vista del Bianco. Campi `[MAIA]` = segnaposto. Radar illustrativo. Parti teoriche non validate. Questo file è materiale di partenza per il fewshot (documentazione §8-bis.4): **non** va usato come esempio nel prompt. I commenti `<!-- Sxx -->` indicano la sezione di destinazione (§8.2-ter).


## In una frase  <!-- S01 -->

La posizione è equilibrata: vince chi sviluppa meglio e non regala materiale. Il motore dà un vantaggio minimo al Bianco (+0,2 / +0,4), quindi **stai bene: devi solo giocare in modo ordinato**.

## Le tre cose da fare adesso  <!-- S03 -->

1. **Sviluppa i pezzi** (alfieri, poi la donna se serve).
2. **Arrocca presto** (corto, a destra).
3. **Tieni protetto il pedone e4**.

<!-- S04 assorbita (§8.2-bis): nel fewshot il blocco principi nomina il lato di arrocco di ogni sistema (corto con Be2, lungo con Be3 + f3 + Qd2). needs_review -->

<!-- Non vincolante (D-29): se la raccomandazione calcolata è 6.Be3, nel fewshot questo blocco e «Arrocca presto (corto)» vanno riscritti per il sistema con arrocco lungo. -->
## La mossa consigliata: 6.Be2  <!-- S03 (blocco raccomandazione: nel fewshot = raccomandazione calcolata, §4.3) -->

È solida: sviluppa l'alfiere, prepara l'arrocco e non ti espone a trappole. Il motore la valuta +0,22, a soli 0,15 dalla migliore. Un'alternativa più ambiziosa è **6.Be3** (+0,37), ma porta spesso ad arrocco lungo e a molta teoria.

**Piano semplice:** Be2 → Be3 → O-O → poi f4 oppure a4.

## Cosa vuole ogni pezzo  <!-- S05 -->

- **Cavallo d4:** sta bene al centro. Se il Nero gioca ...e5 il cavallo è attaccato: **ritiralo in b3**, non lasciarlo catturare.
- **Cavallo c3:** protegge e4 e controlla d5. Dopo ...e5, la casa **d5** è un punto debole del Nero: il tuo obiettivo.
- **Alfiere c1:** va in e3, dietro al cavallo d4.
- **Alfiere f1:** va in e2.
- **Re:** arrocca corto appena possibile.

## Cosa fa il Nero  <!-- S06 -->

- Gioca **...e5** per prendersi il centro (poi cerca ...Be7, ...O-O).
- Oppure **...e6**, più elastico.
- Spesso spinge **...b5** sul lato di donna per attaccare.

## Attenzione a questi errori tipici  <!-- S08 (sempre presente all'ancora 1500, theory ammessa) -->

- Dopo ...e5, **non lasciare il cavallo d4** dove può essere catturato dal pedone.
- Non lasciare **e4 senza protezione**: il cavallo nero può catturarlo con ...Nxe4.
- Non mandare la donna a mangiare pedoni lontani: è il modo più comune di perdere tempo e pezzi.
- Non lanciare attacchi di pedoni **prima di aver arroccato**.

## Prima di ogni mossa, controlla  <!-- S10 -->

1. Cosa minaccia l'avversario con la sua ultima mossa?
2. Tutti i miei pezzi sono protetti?
3. Posso sviluppare un pezzo o arroccare?
4. C'è una cattura o uno scacco che mi conviene?

## Radar semplificato (illustrativo)  <!-- S02 (da M3: escluso dal fewshot fino ad allora) -->

| Categoria | T (tu) | R |
| --- | --- | --- |
| Sviluppo e tempo | 70 | 75 |
| Sicurezza del re | 88 | 40 |
| Materiale | 100 | 10 |

*A questo livello mostriamo solo le categorie che contano e nascondiamo quelle in cui non c'è nulla da fare.*

## Mosse candidate (versione semplice)  <!-- S07 (T1, colonne dell'ancora 1500) -->

| Mossa | Motore | Per chi |
| --- | --- | --- |
| **6.Be2** | +0,22 | Consigliata: solida e semplice |
| 6.Be3 | +0,37 | Più ambiziosa, richiede più teoria |
| 6.Bg5 / 6.Bc4 | +0,29 / +0,23 | Buone ma molto teoriche: meglio più avanti |

`[MAIA]` mosse che a 1500 si giocano per istinto e perdono: da riempire.
