# Rapporto della milestone M1b — Verifica, render e golden

Contenuto (§13): risoluzione dei token, controlli V01–V11, modalità degradata, render Markdown (testata,
tabelle, frasi fisse, rapporto, formati), `golden --packs`, i tre fewshot con `_s07_alt.json` e `_terms.txt`,
`golden --render`, misura delle parole e aggiornamento dei valori di §0.5, `rendered` pronti per la
revisione umana. **Nessuna chiamata al modello** (arriva con M1c).

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-04 | Superato: tutti i token dei fewshot e della risposta valida si risolvono; resa di ogni tipo di token; V02 su ID inesistente, valore nullo, sintassi, nodo non citabile, `pv` troppo lunga, mossa senza valutazione, nodo senza Maia-2, `sc` (M3) | `test_ac04_tokens.py` |
| AC-05 | Superato: le 17 stringhe dell'Appendice G.4 | `test_ac05_v03.py` |
| AC-06 | Superato: sezioni del documento = SectionPlan per le tre ancore; omesse e assorbite nel rapporto con motivo; sezione mancante, extra e ordine sbagliato riparati in modalità degradata | `test_ac06_sections.py` |
| AC-07 | Superato: casi dell'Appendice G.5, segnalazione dello sforamento, i tre fewshot entro i budget | `test_ac07_words.py` |
| AC-08 | Superato: V05 sul token `pv` (`bad_long_line.json`) e sul blocco `line` | `test_ac08_max_plies.py` |
| AC-10 (1500, 1900) | Superato sui `rendered`: sezioni attese, titoli di `section_titles.yaml` nell'ordine di §8.1, S08 sempre presente a 1500, S04 assorbita a 1500, omissioni registrate | `test_ac10_najdorf_sections.py` |
| AC-16 (verifica) | Superato: ogni risposta dell'Appendice G.6 dà esattamente gli errori attesi; in modalità degradata ogni errore è rimosso, marcato o riportato nel rapporto e in `verification.json` | `test_ac16_fault_injection.py` |
| AC-18 (documento) | Superato: a 1900 e 2400 frase fissa all'inizio di S06 e S08, nota sotto T1, avviso in testata; V11 rileva la frase mancante | `test_ac18_maia_saturation.py` |
| AC-21 (documento) | Superato: titolo alternativo di S07, T1 alternativa, S03 e S08 omesse con `opponent_to_move`, fasi omesse nel rapporto | `test_ac21_opponent_to_move.py` |
| AC-23 | Superato: resa di `plan`; mossa illegale, scacco non finale, lato sotto scacco, oltre `plan_max_moves` → V04; `plan` in un paragrafo `engine` → V10 | `test_ac23_plan.py` |
| AC-27 | Superato: i tre fewshot e `_s07_alt.json` superano V01–V10; il render riproduce esattamente i `rendered` versionati | `test_ac27_golden.py` |
| AC-28 | Superato: esempi di §9-bis.7, confini delle bande (±14, ±15, ±49, ±50, ±99, ±100, ±199, ±200), matto, bande di Maia-2 | `test_ac28_formats.py` |

Suite: `pytest` → 400 test in circa 20 s, senza motori né rete. I criteri di M0 e M1a restano verdi.

## Golden

| File | Contenuto |
| --- | --- |
| `examples/golden/packs/najdorf_w_{1500,1900,2400}.pack.json` | Pacchetti congelati (profilo `deep`, E3 a ℓ1) |
| `examples/golden/packs/najdorf_after_be3_w_1900.pack.json` | Pacchetto della fixture AC-21, per `_s07_alt.json` |
| `examples/golden/fewshot/najdorf_w_*.json` | I tre fewshot (formato di §9-bis.6), scritti dai raw con i token del pacchetto |
| `examples/golden/fewshot/*.meta.yaml` | `validated: false`, sezioni da rivedere (`needs_review`) e differenze dal raw |
| `examples/golden/fewshot/_s07_alt.json`, `_terms.txt` | S07 in modalità avversario; termini per V09 |
| `examples/golden/rendered/najdorf_w_*.md` | Documenti generati da `golden --render` (non si modificano a mano) |

Differenze di contenuto rispetto ai raw, dovute ai dati dei pacchetti: la raccomandazione calcolata è 6.f3
(debole, nessuna mossa unica) a tutte le ancore, quindi a 1500 il piano semplice è quello con l'arrocco
lungo e 6.Be2 resta l'alternativa con arrocco corto; la mossa di contesto è `...e5` (non `...Nc6`), con un
costo di 0,86 contro 6.Bg5; le candidate spiegate sono 6.f3, 6.Be3, 6.h3, 6.Bd3, 6.Bg5 (a 1500: 6.f3, 6.Be3,
6.Bg5). S08 a 1900 e 2400 è scritta da zero (nel raw era un segnaposto). Il dettaglio è nei `meta.yaml`.

**Revisione umana (§8-bis.5).** I `rendered` vanno letti da giocatori di circa 1500, 1900 e 2400; dopo la
revisione si mette `validated: true` nel `meta.yaml`. Fino ad allora i documenti portano in testata
l'avviso `references_not_validated`.

## Misura delle parole (§0.5)

| Ancora | Parole del fewshot | `prose_words` | Decisione |
| --- | --- | --- | --- |
| 1500 | 506 | 650 | → 500, pesi dell'ancora aggiornati |
| 1900 | 1217 | 1400 | invariato (−13%) |
| 2400 | 609 | 800 | → 610 |

Dettagli e regola in `docs/golden_diff.md`; i tetti `theory_max_share` restano invariati (misure 0,50,
0,42, 0,13).

## Uso

```bash
.venv/bin/chessanalyst golden --render                     # verifica i fewshot e rigenera rendered/
.venv/bin/chessanalyst golden --packs --force              # rigenera i pacchetti con i motori veri
.venv/bin/chessanalyst golden --packs --force --recorded   # ... oppure dalle registrazioni (OQ-M1b-1)
.venv/bin/python -m tests.fault_fixtures                   # rigenera le risposte difettose (G.6)
```

`analyze` produce ancora solo `pack.json`: client Anthropic, prompt, retry e `rerun` sono M1c. Le scelte
prese dove la specifica lasciava margine sono in `docs/OPEN_QUESTIONS.md` (OQ-M1b-1…13).
