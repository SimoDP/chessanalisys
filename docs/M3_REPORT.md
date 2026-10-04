# Rapporto della milestone M3 — Category Scoring Engine

Contenuto (§13):
- §5-bis completo;
- feature «M3»;
- radar S02;
- S09;
- confidenza.

Criteri di uscita: ogni `T`/`R` tracciabile a feature o linee, test unitari delle formule. Prima di M3 sono stati
chiusi due punti rimasti aperti dopo M2:
- **Stockfish 19 e tablebase installati** in questo container (`doctor` tutto OK);
- **AC-09 ripetuto con Stockfish 19** (`docs/golden_diff_sf19.md`): superato, con scarti tra −0,13 e −0,18 sulle
  prime 3 dei raw e nessun valore oltre 0,25. Il test controlla sia Stockfish 16 (M0) sia Stockfish 19.

## Criteri di uscita

| Criterio | Esito | Test |
| --- | --- | --- |
| Ogni T/R tracciabile | Superato sui 7 pacchetti congelati. T_stat si ricalcola dalle feature tracciate, T_dyn dalle linee tracciate, T da combinazione e override, R dai suoi termini. Le linee del referto rispettano il filtro, T4 segue R e `must_cover` di S09 coincide con le linee invisibili | `tests/acceptance/test_m3_traceability.py` |
| Test unitari delle formule | Coperti: `side_value`, probabilità del percorso, `P_att` (solo mosse da trovare), rischio, filtro per θ con le eccezioni matto/decisiva, ID `L<n>`, T_stat (anche relativa), bande di advice, combinazione T, override solo sulla categoria principale, R, confidenza, foglia dopo quiescenza | `tests/test_scoring.py` |
| Feature «M3» | Tutte le chiavi di §5.1 marcate M3, una posizione per definizione | `tests/test_features_m3.py` |
| Verifica dei nuovi token | `sc`, `L<n>` in `pv`/`ev`/`loss` e nei blocchi `line`, `category_advice`, vista ridotta | `tests/test_verify_m3.py` |

**Suite:** `pytest` → 583 superati, nessun fallito, 2 avvisi `ChecklistQualityWarning`.

## Che cosa c'è

- **Feature M3** (`features/`):
  - zona del re (attaccanti, difensori);
  - mobilità per pezzo, pezzi inattivi, alfiere su diagonale aperta;
  - infilata, inforchetta (non catturabile con SEE ≥ 0), pezzo sovraccarico;
  - mosse forzanti nella PV migliore;
  - attacco di minoranza, vantaggio di spazio, controllo di colonna, catene di pedoni.

  Le soglie sono in `thresholds.yaml: features`.
- **Linee e filtro** (`scoring/filter.py`, OQ-M3-1):
  - minacce della mossa nulla e confutazioni delle mosse che portano ai nodi E2, E3 e R;
  - `P_att` dalle probabilità di Maia-2 della prima mossa e delle mosse forzanti dell'attaccante;
  - `1 − P_dif` = probabilità che il difensore non eviti la linea;
  - rischio in pedoni e filtro per `θ(fascia)`. Matti e perdite decisive entrano sempre, «invisibili» se `P_att`
    < 0,10.
- **Categorie** (`scoring/categories.py`, OQ-M3-2…4):
  - tag dal confronto tra inizio e foglia, dopo quiescenza;
  - T statica dai punti delle feature, T dinamica `100·exp(−Σrisk/k)`, combinazione con `w`;
  - override a 29 sulla categoria principale;
  - R con preoccupazione, |balance|, vicinanza pesata col rischio e quota della decisione (PV delle candidate);
  - complessità pratica da entropia e mosse uniche;
  - confidenza.
- **Pacchetto:** `categories`, `filtered_lines`, tabella T4 (`scoring/radar.py`), S02 e S09 nel SectionPlan (c9,
  `must_cover` = linee invisibili).
- **Testo:**
  - token `{{sc:CAT.T}}`/`{{sc:CAT.R}}`;
  - linee `L<n>` in `pv`, `ev`, `loss` e nel blocco `line`;
  - asserzione `category_advice`;
  - nel prompt, l'Appendice E.1 parola per parola più sette modifiche elencate (OQ-M3-6).
- **Costanti:** tutte in `thresholds.yaml: scoring`, ipotesi iniziali da calibrare in M5 (§0.5).

## Che cosa dicono i radar

| Pacchetto | Righe principali di T4 (T tu · R) | Linee | S09 |
| --- | --- | --- | --- |
| Najdorf 1500/1900/2400 | Attività 100 · 26–30, Struttura 100 · 12–13, Complessità pratica 77–80 · 7–8 | nessuna | obbligatoria, «nessuna minaccia nascosta» |
| Najdorf dopo `6.Be3` | Attività 100 · 30, Spazio 100 · 13 | nessuna | idem |
| Fried Liver 1500 | **Minacce e dinamica 29 (critico) · 63**, Re 78 · 46, Attività 85 · 44, Materiale 100 · 44 | 5 (`...Qxg5` dopo una mossa che non para, confutazioni di `...Qh4` e `...Qf6`) | L1, L2 (decisive ma invisibili a 1500) |
| Finale di torri 1900 | Attività 100 · 25, Complessità pratica 61 · 15 | nessuna | omessa (c9) |
| Lucena 1900 | — (colonna 4: S02 e S09 omesse) | nessuna | omessa |

Nella Najdorf il radar è tranquillo, come la posizione. Nella Fried Liver mette in cima il cavallo in presa in g5
(`...Qxg5`), e DeepSeek lo scrive.

## Fewshot e pacchetti

- I pacchetti congelati sono rigenerati dalle registrazioni. Le ricerche di Stockfish non cambiano, così come
  nodi, candidate e ID.
- Le risposte di Maia-2 lungo le linee sono state aggiunte senza Stockfish (`CHESSANALYST_RECORD_MAIA_ONLY`,
  OQ-M3-8): sedici in tutto.
- I tre fewshot hanno S02 e S09 scritte sui dati del pacchetto; `needs_review` le elenca e `rendered` è
  rigenerato.
- `prose_words` è aggiornato in modo che le altre sezioni tengano il loro budget (OQ-M3-7).
- Le risposte difettose di G.6 sono rigenerate dal fewshot 1900.

## Il modello di sviluppo (DeepSeek, D-67)

Risposte registrate di nuovo con `pytest -m llm --record` (prompt M3): sette pacchetti, tre risposte ciascuno.

| Pacchetto | Errori per tentativo | Esito |
| --- | --- | --- |
| Najdorf 1500 | 4, 5, 1 | degradata, 0 rimozioni |
| Najdorf 1900 | 9, 8, 8 | degradata, 2 rimozioni |
| Najdorf 2400 | 1, 20, 3 | degradata, 1 rimozione |
| Najdorf dopo `6.Be3` | 29, 9, 9 | degradata, 3 rimozioni |
| Fried Liver 1500 | 1, 24, 21 | degradata, 4 rimozioni |
| Finale di torri 1900 | 32, 10, 3 | degradata, 2 rimozioni |
| Lucena 1900 | 40, 12, 8 | degradata, 4 rimozioni |

Errori legati a M3:
- **S02 troppo lunga (V07 d):** DeepSeek riempie la nota di ogni riga di T4 e supera il budget di S02 (30 parole a
  1500, 70 a 1900, 40 a 2400). È il solo errore frequente su S02 e S09;
- **giudizi corretti:** le asserzioni `category_advice` e i token `sc`/`L<n>` sono quasi sempre giusti. Ci sono un
  solo V06 (banda di `ev:N2` in S09) e un solo V10 in S02;
- **note:** la regola 12 ora chiede di segnalare in `notes` i punteggi incoerenti (§5-bis.5). DeepSeek commenta
  i punteggi con le cifre («T=29, R=63») e nelle note i V03 aumentano (OQ-M1c-10: le note con cifre vengono
  rimosse).
- **primo tentativo:** nella prima registrazione della Fried Liver tutti e tre i tentativi mancavano del campo
  `notes` (V01) e il ciclo è finito senza risposta. Nella seconda registrazione è andata come in tabella. Il
  modello di sviluppo non è affidabile su questo: il ciclo lo segnala con il codice di uscita previsto.

Checklist: la Fried Liver ora cita anche l'errore tipico `d3`. Mancano ancora «costruire il ponte» (Lucena) e lo
scambio delle torri (finale di torri). Restano misure di qualità (decisione dell'utente in M2).

Prompt, esempi e budget **non** sono stati cambiati dopo aver letto le risposte. Due interventi possibili, da
decidere:
- alzare il peso di S02 in `section_budget.yaml`, oppure scrivere nel prompt che la Nota di T4 è facoltativa;
- dire nel prompt che le note vanno scritte in lettere.

## Stato

**M3 chiusa.** I criteri di uscita sono superati e la suite è verde. Restano:
- le costanti di §5-bis, ipotesi iniziali da calibrare in M5;
- i fewshot da validare (§8-bis.5), ora con S02 e S09;
- la lunghezza di S02 nelle risposte di DeepSeek, da decidere.

## Uso

```bash
.venv/bin/chessanalyst analyze --input pgn --file partita.pgn --yes     # radar in S02, minacce invisibili in S09
CHESSANALYST_RECORD_MAIA_ONLY=1 .venv/bin/pytest -m engines --record    # solo le risposte di Maia-2 mancanti
.venv/bin/chessanalyst golden --packs --force --recorded                # pacchetti congelati
.venv/bin/pytest -m llm --record                                         # risposte del modello reale
```

Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M3-1…8).
