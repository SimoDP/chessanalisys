# Rapporto della milestone M1c — Modello

Contenuto (§13): client del modello (OpenRouter predefinito, Anthropic in alternativa: D-64), prompt (Appendice E), schema dello strumento (Appendice F), legenda dei
token, vista ridotta del pacchetto, retry di verifica e di rete, `rerun`.

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-01 | Superato: esempio, `FakeEngine`, `FakeMaia`, `FakeLLM` con `good_najdorf_1900.json` → `analysis.md`, `pack.json`, `llm_raw.json`, `verification.json`, `run.log`, codice 0; il pacchetto coincide con quello congelato e la verifica non trova errori | `test_ac01_full_run.py` |
| AC-10 (risposta del modello reale) | **In attesa**: serve una risposta registrata con la chiave API (`pytest -m llm --record`); il test c'è ed è saltato finché la registrazione manca | `test_ac10_najdorf_sections.py` |
| AC-15 | Superato: `rerun` senza motori, `pack.json` invariato, file precedenti in `*.prev.*`, avviso se `config_hash` differisce | `test_ac15_rerun.py` |
| AC-16 (ciclo completo) | Superato: per ogni risposta difettosa retry con `tool_result` `is_error` e correzione; dopo i retry rimozione o marcatura registrata; V07(d) da solo al massimo un retry; nessuna risposta valida → codice 5 | `test_ac16_fault_injection.py` |
| AC-21 (modello) | **In attesa** come AC-10 | `test_ac21_opponent_to_move.py` |
| AC-35 | Superato: nessun nodo `citable: false`, nessuna tabella, al massimo 5 righe per nodo (PV di 6 semimosse, 5 mosse di Maia-2) | `test_ac35_llm_view.py` |

Altri test: system prompt identico all'Appendice E.1; schema generato equivalente all'Appendice F (accetta e
rifiuta le stesse risposte); struttura del messaggio utente (E.2) e del retry (E.3); scelta dell'esempio per
ancora e `_s07_alt.json` in modalità avversario; politica di rete (429/5xx/529 e connessione con attese e
`retry-after`, 400/401/403 senza tentativi, `temperature` rifiutata); riservatezza (nomi, tag e percorsi di un
PGN non arrivano al messaggio).

Suite: `pytest` → 473 test superati e 3 saltati (le risposte reali), senza motori né rete.

## Che cosa manca per chiudere M1c

AC-10 e AC-21 nella parte «modello» richiedono una chiamata vera: con `OPENROUTER_API_KEY` impostata (D-64),

```bash
.venv/bin/pytest -m llm --record      # registra real_najdorf_w_1500/1900 e real_najdorf_after_be3_w_1900
.venv/bin/pytest                      # i tre test non sono più saltati
```

## Uso

```bash
export OPENROUTER_API_KEY=...                              # mai scritta su disco né nei log
.venv/bin/chessanalyst analyze --yes --elo 1900
.venv/bin/chessanalyst rerun output/<cartella>             # rifà modello, verifica e render da pack.json
```

Senza chiave l'analisi dei motori viene comunque salvata (`pack.json`) e l'uscita è con codice 4 e
l'indicazione del comando `rerun`. Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M1c-1…8).
