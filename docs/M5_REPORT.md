# Rapporto della milestone M5 — Calibrazione dei numeri

Contenuto (§13):
- 50–100 posizioni annotate;
- calibrazione di `k_c`, `w_c`, `θ`, `A`, `B`, `L_max` su partite del database aperto Lichess (D-21);
- regressione del prompt.

Criteri di uscita: relazione di calibrazione, soglie aggiornate.

## Che cosa è stato fatto

1. **Campione** (`chessanalyst calibrate --sample`, OQ-M5-2):
   - 100 posizioni da partite rapid valutate di agosto 2026, 20 per fascia del giocatore al tratto, lette in
     streaming dal file mensile;
   - senza nomi: solo ID pubblico, Elo e mosse;
   - file: `fixtures/calibration/positions.jsonl`.
2. **Annotazione** (`chessanalyst calibrate --annotate`, OQ-M5-1), automatica con Stockfish 19 e Maia-2:
   - pipeline completa dell'app (profilo `fast`);
   - tutte le linee di §5-bis prima del filtro θ, con i tag;
   - la mossa giocata e le due successive del giocatore, con il loro costo e, per gli errori (≥ 1 pedone), le
     categorie della confutazione;
   - file: `fixtures/calibration/annotations.jsonl`. Circa 75 s per posizione.
3. **Fit** (`chessanalyst calibrate --fit`, OQ-M5-3): ricerca a griglia senza motori sulle annotazioni, controllo
   incrociato su due metà, regole di adozione scritte prima di guardare i risultati. File:
   `docs/CALIBRATION_REPORT.md` e `fixtures/calibration/fit.json`.
4. **Regressione del prompt** (`chessanalyst regression`, OQ-M5-4): il modello sui sette pacchetti congelati, tre
   giri ciascuno, confronto con il riepilogo precedente. File: `docs/regression/`.

## Risultati

**Campione.** Gli errori calano con l'Elo: posizioni con almeno un errore del giocatore 9, 12, 10, 9 e 5 su 20, dalla
fascia più bassa alla più alta. Il costo medio della mossa giocata va da 151 cp sotto 1200 a 20 cp tra 2000 e 2400.

**Tranquillità T.** Prima della calibrazione T prevedeva gli errori poco meglio del caso (AUC media 0,58).
- Il primo passo (θ, k, w insieme) non passa il controllo incrociato: θ cambia direzione tra le due metà.
- Il secondo passo (θ fisso) passa in entrambe le metà.
- **Adottati**: k_c × 0,15 e w_c + 0,15 per le otto categorie con linee. AUC sulle metà non usate per il fit: da
  0,58 a 0,61.
- Tasso di errore per banda di T con i valori nuovi: 35% sotto 30, 37% tra 30 e 60, 19% tra 60 e 85, 14% da 85.
  «Una T alta non precede errori frequenti», come chiede §5-bis.4.

In pratica il rischio delle linee era pesato troppo poco rispetto alle feature statiche. Sulla Fried Liver la
sicurezza del re è ora «critica» (T 18) e le minacce T 14. Sulla Najdorf, posizione tranquilla, nulla cambia.

**Invariati, con motivo:**
- **θ:** instabile tra le due metà del campione.
- **A e L_max:** nessuna fascia migliora di 10 punti la quota di posizioni in cui la mossa giocata è tra le candidate
  spiegate. Le coperture sono 55%, 70%, 90%, 85% e 90% dalla fascia più bassa.
- **B:** nelle partite non c'è una verità per il peso della complessità nella raccomandazione.

**Regressione del prompt** (DeepSeek, D-67, 3 giri × 7 pacchetti, prima e dopo la calibrazione,
`docs/regression/20261004T232459.md`):

|  | Prima | Dopo |
| --- | --- | --- |
| Risposte complete | 10 su 21 | 6 su 21 |
| Rimozioni in media | 2,4 | 2,2 |

Le differenze sono quelle tipiche del modello di sviluppo e compaiono in entrambe le serie: JSON non valido al
primo tentativo (V01), sezioni fuori budget (V07 d), giri senza risposta valida. Con tre giri per pacchetto,
10 contro 6 non è una differenza significativa. Il primo riferimento a un solo giro aveva mostrato lo stesso
pacchetto passare da completo a 23 rimozioni. Per questo la regressione ora ripete ogni pacchetto.

Dopo l'adozione:
- i pacchetti congelati sono stati rigenerati;
- i fewshot passano ancora la verifica senza modifiche;
- `rendered` e risposte difettose di G.6 sono rigenerati;
- le risposte di DeepSeek usate dai test sono registrate di nuovo.

**Suite:** `pytest` → 624 superati, nessun fallito, 2 avvisi `ChecklistQualityWarning` (come in M3–M4).

## Limiti

- **Campione.** Cento posizioni e un mese di partite: abbastanza per una direzione, non per valori fini. L'ottimo
  dei dati è sul bordo della griglia (k ancora più piccolo, w ancora più grande); si è scelto il punto robusto
  interno.
- **Annotazione.** È automatica: misura gli errori secondo Stockfish, non l'utilità percepita da un giocatore. Le
  metriche umane di §12.2 restano alla validazione degli esempi.
- **Profilo.** Le posizioni sono analizzate col profilo `fast`: con `deep` le linee sarebbero di più e il fit
  potrebbe spostarsi.
- **Valori da rivedere.** Le costanti statiche (`scoring.static`), le soglie dei tag e i pesi di R restano ipotesi
  di M3. Il fit tocca solo θ, k e w come chiede §0.5.

## Stato

**M5 chiusa**: c'è la relazione di calibrazione e le soglie sono aggiornate (k_c, w_c), con la procedura
ripetibile:

```bash
.venv/bin/pip install -e ".[calibration]"
.venv/bin/chessanalyst calibrate --sample      # posizioni dal database aperto di Lichess
.venv/bin/chessanalyst calibrate --annotate    # motori veri, circa due ore per cento posizioni
.venv/bin/chessanalyst calibrate --fit         # griglia, controllo incrociato, relazione
.venv/bin/chessanalyst regression              # modello sui pacchetti congelati, confronto con il giro precedente
```

Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M5-1…4).
