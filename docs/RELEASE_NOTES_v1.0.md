# Chess Position Analyst 1.0 — note di rilascio

Prima versione completa del piano di §13: milestone M0–M6.

## Che cosa fa

Data una posizione (esempio, FEN o PGN, con scelta della partita e della mossa) e il tuo Elo, produce un'analisi
in italiano calibrata sul tuo livello:
- **Motori.** Stockfish 19 cerca le mosse e le linee; Maia-2 stima che cosa giocano davvero i giocatori del tuo
  livello e di quello dell'avversario.
- **Testo.** Un modello di linguaggio scrive il testo solo con riferimenti ai dati: ogni mossa, valutazione e
  probabilità la scrive il programma. Ogni frase è verificata (V01–V11); quello che non passa si corregge o si marca.
- **Contenuto.** Sezioni scelte per il livello: sintesi, radar delle categorie, candidate, piani, minacce invisibili
  al tuo livello, finali, note da maestro…

## Come si usa

```bash
chessanalyst ui                      # nel browser: posizione, impostazioni, conferma con la scacchiera, analisi
chessanalyst                         # lo stesso nel terminale
chessanalyst analyze --yes --elo 1900 --budget fast
chessanalyst export output/<cartella> --format pgn   # oppure html, md
chessanalyst rerun output/<cartella> # rifà solo testo e verifica dal pacchetto salvato
chessanalyst doctor                  # controlla motori, pesi, chiave API
```

Ogni analisi è una cartella con `analysis.md`, `analysis.html` (mosse e varianti cliccabili sulla scacchiera,
anche senza rete) e i dati per rifarla (`pack.json`, risposte e controlli del modello, `run.log`).

## Novità di M6

- **Interfaccia nel browser.** `chessanalyst ui`, solo su questo computer (127.0.0.1).
- **Pagina dell'analisi.** Ogni mossa, variante e posizione del testo è cliccabile; le frecce scorrono le varianti.
- **Esportazione.** HTML, Markdown e PGN; nel PGN le candidate e le linee del motore sono varianti con la
  valutazione.
- **Costi.** Nel rapporto di ogni analisi ci sono chiamate, token e costo del modello; due punti di cache nel primo
  messaggio per i modelli Anthropic.

## Requisiti

- **Software.** Python 3.11 o 3.12, Stockfish 19, pesi di Maia-2 0.11.0, tablebase Syzygy fino a 5 pezzi, indice
  delle aperture: `scripts/setup_engines.py` li scarica.
- **Chiave del modello.** OpenRouter (`OPENROUTER_API_KEY`) o Anthropic (`ANTHROPIC_API_KEY`). La chiave non si
  salva mai su disco; al modello non vanno mai PGN, nomi o percorsi.

## Limiti noti e decisioni aperte

- **Modello di produzione.** Da scegliere (D-67). Lo sviluppo usa `deepseek/deepseek-v4.1-flash`: economico, ma
  con più retry e più parti marcate rispetto a un modello più forte. Il critico (`llm.critic`) resta spento perché
  con questo modello dà falsi positivi.
- **Esempi di riferimento.** I fewshot attendono la validazione umana (§8-bis.5).
- **Calibrazione.** Fatta su 100 posizioni e un mese di partite rapid, con annotazione automatica. Le costanti
  statiche e i pesi di R restano ipotesi (`docs/CALIBRATION_REPORT.md`). Resta da rifinire l'analisi per le diverse
  fasce di Elo.
- **Scala chess.com.** Rifiutata finché la tabella di conversione è vuota.

Dettagli: `docs/M6_REPORT.md`, `docs/OPEN_QUESTIONS.md` (OQ-M6-1…6), `docs/DECISIONI_POST_CONGELAMENTO.md`.
