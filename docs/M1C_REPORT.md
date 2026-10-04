# Rapporto della milestone M1c — Modello

Contenuto (§13): client del modello (OpenRouter predefinito, Anthropic in alternativa: D-64), prompt (Appendice E), schema dello strumento (Appendice F), legenda dei
token, vista ridotta del pacchetto, retry di verifica e di rete, `rerun`.

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-01 | Superato: esempio, `FakeEngine`, `FakeMaia`, `FakeLLM` con `good_najdorf_1900.json` → `analysis.md`, `pack.json`, `llm_raw.json`, `verification.json`, `run.log`, codice 0; il pacchetto coincide con quello congelato e la verifica non trova errori | `test_ac01_full_run.py` |
| AC-10 (risposta del modello reale) | Superato con le risposte registrate di DeepSeek (1500 e 1900): vedi «Registrazione del modello reale» | `test_ac10_najdorf_sections.py` |
| AC-15 | Superato: `rerun` senza motori, `pack.json` invariato, file precedenti in `*.prev.*`, avviso se `config_hash` differisce | `test_ac15_rerun.py` |
| AC-16 (ciclo completo) | Superato: per ogni risposta difettosa retry con `tool_result` `is_error` e correzione; dopo i retry rimozione o marcatura registrata; V07(d) da solo al massimo un retry; nessuna risposta valida → codice 5 | `test_ac16_fault_injection.py` |
| AC-21 (modello) | **Fallito**: la risposta finale di DeepSeek ha un token nelle `notes`, il render si ferma su V11 (OQ-M1c-10) | `test_ac21_opponent_to_move.py` |
| AC-35 | Superato: nessun nodo `citable: false`, nessuna tabella, al massimo 5 righe per nodo (PV di 6 semimosse, 5 mosse di Maia-2) | `test_ac35_llm_view.py` |

Altri test: system prompt identico all'Appendice E.1; schema generato equivalente all'Appendice F (accetta e
rifiuta le stesse risposte); struttura del messaggio utente (E.2) e del retry (E.3); scelta dell'esempio per
ancora e `_s07_alt.json` in modalità avversario; politica di rete (429/5xx/529 e connessione con attese e
`retry-after`, 400/401/403 senza tentativi, `temperature` rifiutata); riservatezza (nomi, tag e percorsi di un
PGN non arrivano al messaggio).

Suite: `pytest` → 474 test superati e 3 saltati (le risposte reali), senza motori né rete (verificato il
4 ottobre 2026 con l'indice delle aperture costruito da `scripts/setup_engines.py --skip stockfish maia syzygy`;
senza l'indice AC-01 fallisce sul titolo dell'apertura).

## Che cosa manca per chiudere M1c

AC-10 e AC-21 nella parte «modello» richiedono una chiamata vera: con `OPENROUTER_API_KEY` impostata (D-64),

```bash
.venv/bin/pytest -m llm --record      # registra real_najdorf_w_1500/1900 e real_najdorf_after_be3_w_1900
.venv/bin/pytest                      # i tre test non sono più saltati
```

### Tentativo di registrazione del 4 ottobre 2026

Non riuscito, M1c **resta aperta**. Nell'ambiente cloud `OPENROUTER_API_KEY` non è impostata e il proxy
non autentica le richieste a `openrouter.ai` (ogni chiamata, anche a `/api/v1/chat/completions` con un
messaggio di prova, risponde `401 No cookie auth credentials found`). Il test di registrazione quindi si
salta e nessuna risposta di DeepSeek è stata ancora vista né verificata. Prompt ed esempi non sono stati
toccati. Per chiudere basta ripetere i due comandi qui sopra in una sessione in cui la chiave è disponibile
(variabile d'ambiente dell'ambiente cloud oppure in locale).

### Secondo tentativo, 4 ottobre 2026

Non riuscito, M1c **resta aperta**. Questa volta `OPENROUTER_API_KEY` è impostata nell'ambiente, ma
OpenRouter rifiuta ogni richiesta con `401 No cookie auth credentials found` (lo stesso errore che dà senza
chiave): `pytest -m llm --record` → 3 test falliti con `ModelError: Chiave API non valida o non autorizzata`,
nessuna risposta registrata. Il client gestisce correttamente il caso (401 non ritentato, messaggio in
italiano, chiave mai scritta nei log). Il modello quindi non ha ancora risposto e non ci sono errori di
verifica di DeepSeek da esaminare; prompt ed esempi non sono stati toccati. La suite senza rete resta a
474 superati e 3 saltati. Per chiudere serve una chiave OpenRouter valida (impostata come variabile
d'ambiente dell'ambiente cloud, oppure in locale) e i due comandi qui sopra.

### Registrazione del modello reale, 4 ottobre 2026 (terzo tentativo)

La variabile `OPENROUTER_API_KEY` adesso arriva a OpenRouter e la registrazione funziona. I primi due
tentativi erano falliti con un 401: il proxy dell'ambiente cloud sostituiva la chiave con una credenziale vuota.
Modello `deepseek/deepseek-v4.1-flash`, tre risposte (due retry) per ogni pacchetto:

| Pacchetto | Tentativo 1 | Tentativo 2 | Tentativo 3 | Esito |
| --- | --- | --- | --- | --- |
| `najdorf_w_1500` | V01: manca un campo obbligatorio | V04 piano `f3,…@N3` (f3 già giocato in N3), V07(d) | nessun errore | documento completo |
| `najdorf_w_1900` | V04 su due piani (mossa già giocata nel nodo), V07(d) | V04 piano `Be3,…@N4` | V04 piano `O-O-O@N4` (donna ancora in d1) | degradata: rimosso S03 · blocco 1 |
| `najdorf_after_be3_w_1900` (AC-21) | V02 nodi inesistenti N8 e N11, V04 mosse già giocate nei nodi N3–N5, V06 banda di N2, V07(d), V09 «Scheveningen» | solo V07(d) | solo V07(d) (S06 troppo corta) | **interrotta**: token nelle `notes` → V11 |

Errori ricorrenti del modello:
- Confonde il nodo da cui parte una mossa con il nodo che si ottiene dopo averla giocata (V04).
- Copia ID dei nodi che il pacchetto non ha (V02).
- Scrive testi più corti del budget (V07(d)).

I retry li correggono quasi sempre. Il caso di AC-21 invece rivela un buco della verifica: V01–V10 non
controllano le `notes`, e un token scritto lì blocca il render (OQ-M1c-10, serve una decisione dell'utente).
Prompt ed esempi non sono stati toccati.

Suite: `pytest` → 476 superati, 1 fallito (AC-21 «modello»). M1c **resta aperta** finché OQ-M1c-10 non è
decisa e corretta.

## Uso

```bash
export OPENROUTER_API_KEY=...                              # mai scritta su disco né nei log
.venv/bin/chessanalyst analyze --yes --elo 1900
.venv/bin/chessanalyst rerun output/<cartella>             # rifà modello, verifica e render da pack.json
```

Senza chiave l'analisi dei motori viene comunque salvata (`pack.json`) e l'uscita è con codice 4 e
l'indicazione del comando `rerun`. Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M1c-1…8).
