# Rapporto della milestone M6 — UI e v1.0

Contenuto (§13): UI con scacchiera, varianti cliccabili, esportazione; ottimizzazione dei costi.
Criterio di uscita: rilascio v1.0.

## Che cosa è stato fatto

1. **Pagina `analysis.html`** (OQ-M6-3). Si scrive accanto ad `analysis.md` in ogni analisi, `rerun` ed
   *entrambi*:
   - **Testo.** È quello del documento Markdown.
   - **Collegamenti.** Ogni mossa, linea e valutazione di nodo porta alla posizione corrispondente.
   - **Scacchiera.** Disegnata dal FEN con l'ultima mossa evidenziata; frecce (anche da tastiera) per scorrere la
     variante; si può girare.
   - **Funzionamento.** Nessuna risorsa esterna: si apre anche senza rete.
   - **`render.json`.** Conserva output finale e informazioni del render, per ricostruire pagina ed esportazioni.
2. **Esportazione** (`chessanalyst export <cartella> --format html|md|pgn`, OQ-M6-4). Nel PGN:
   - le candidate sono varianti, la migliore è la linea principale;
   - le linee filtrate di §5-bis sono innestate nella posizione da cui partono;
   - le valutazioni sono dal punto di vista dell'utente;
   - non ci sono nomi.
3. **Interfaccia nel browser** (`chessanalyst ui`, OQ-M6-1, OQ-M6-2). Scelta dell'utente: pagina web locale.
   - **Flusso.** È quello interattivo: posizione, impostazioni, conferma con la scacchiera, Elo dai tag con la scala,
     avanzamento, elenco delle analisi con pagina e download.
   - **Server.** Solo libreria standard, solo su 127.0.0.1, con controllo di Host e Origin, token della pagina e file
     serviti per nome.
4. **Costi** (OQ-M6-5):
   - chiamate, token in ingresso e in cache, token in uscita e costo nel rapporto di ogni analisi, in
     `verification.json` e nella regressione (con il costo medio per analisi);
   - due punti di cache nel primo messaggio per i modelli Anthropic;
   - prezzi per modello configurabili (`llm.prices`) per i fornitori che non danno il costo.
5. **Versione 1.0.0** (OQ-M6-6): README, note di rilascio (`docs/RELEASE_NOTES_v1.0.md`), tag `v1.0.0`.

## Misure

**Costo del modello** (DeepSeek, D-67), dalla regressione del prompt: 7 pacchetti congelati × 3 giri, 20 analisi con
risposta valida su 21 (`docs/regression/20261005T073135.md`).

| Misura per analisi | Media | Min | Max |
| --- | --- | --- | --- |
| Costo | 0,0144 $ | 0,0060 $ | 0,0343 $ |
| Chiamate (1 + retry) | 2,85 | | |
| Token in ingresso | 119 mila (102 mila in cache) | | |
| Token in uscita | 10 mila | | |

- **Totale.** I 21 giri sono costati 0,29 $.
- **Prova dall'interfaccia.** Un'analisi della posizione d'esempio con i motori veri (profilo `fast`) è costata
  0,032 $: 3 chiamate, cache vuota alla prima richiesta.
- **Che cosa pesa.** I token in uscita e i retry: ogni retry rimanda la conversazione e riscrive l'intera analisi.
  La cache del fornitore copre già gran parte dell'ingresso. Con un modello Anthropic il costo per token è più alto,
  ma meno retry dovrebbero compensare in parte. Va misurato con `chessanalyst regression` quando si sceglie il
  modello di produzione.
- **Qualità.** Le risposte complete sono 4 su 21; nella regressione di M5 erano 6 su 21. È nella variabilità già
  vista con il modello di sviluppo: JSON non valido al primo tentativo, valori fuori banda (V10) rimossi in modalità
  degradata. M6 non tocca prompt né verifica.

**Suite:** `pytest` → 641 superati, nessun fallito, 2 avvisi `ChecklistQualityWarning` (come in M3–M5). Nuovi test:
- `tests/test_render_html.py`: testo uguale al Markdown, collegamenti, varianti in ordine, pagina offline;
- `tests/test_export.py`;
- `tests/test_ui_server.py`: protezioni, anteprima, analisi completa con motori sintetici, *entrambi*, un'analisi
  alla volta.

È stata provata anche un'analisi reale dall'interfaccia, in Chromium.

## Limiti

- **Collegamenti.** La pagina collega le mosse che il programma scrive. Le case citate nel testo libero non sono
  collegamenti.
- **Minacce nel PGN.** Le linee di minaccia non sono nel PGN: partono da una mossa nulla.
- **Interfaccia.** Non ferma un'analisi in corso: per interromperla si chiude il server, il pacchetto già scritto
  resta e si rifà con `rerun`.
- **Decisioni aperte** (note di rilascio):
  - il modello di produzione (D-67);
  - la validazione umana dei fewshot;
  - la rifinitura per le diverse fasce di Elo.

## Stato

**M6 chiusa, v1.0 rilasciata.**

```bash
.venv/bin/chessanalyst ui
.venv/bin/chessanalyst export output/<cartella> --format pgn
```
