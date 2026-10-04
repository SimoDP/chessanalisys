# Rapporto della milestone M1c — Modello

Contenuto (§13): client del modello (OpenRouter predefinito, Anthropic in alternativa: D-64), prompt (Appendice E), schema dello strumento (Appendice F), legenda dei
token, vista ridotta del pacchetto, retry di verifica e di rete, `rerun`.

## Criteri di accettazione

| AC | Esito | Test |
| --- | --- | --- |
| AC-01 | Superato: esempio, `FakeEngine`, `FakeMaia`, `FakeLLM` con `good_najdorf_1900.json` → `analysis.md`, `pack.json`, `llm_raw.json`, `verification.json`, `run.log`, codice 0; il pacchetto coincide con quello congelato e la verifica non trova errori | `test_ac01_full_run.py` |
| AC-10 (risposta del modello reale) | Superato con le risposte registrate di DeepSeek (1500 e 1900): vedi «Registrazione del modello reale» | `test_ac10_najdorf_sections.py` |
| AC-15 | Superato: `rerun` senza motori, `pack.json` invariato, file precedenti in `*.prev.*`, avviso se `config_hash` differisce | `test_ac15_rerun.py` |
| AC-16 (ciclo completo) | Superato (con `bad_notes_token.json`, OQ-M1c-10): per ogni risposta difettosa retry con `tool_result` `is_error` e correzione; dopo i retry rimozione o marcatura registrata; V07(d) da solo al massimo un retry; nessuna risposta valida → codice 5 | `test_ac16_fault_injection.py` |
| AC-21 (modello) | Superato con la risposta registrata di DeepSeek (dopo la correzione di OQ-M1c-10) | `test_ac21_opponent_to_move.py` |
| AC-35 | Superato: nessun nodo `citable: false`, nessuna tabella, al massimo 5 righe per nodo (PV di 6 semimosse, 5 mosse di Maia-2) | `test_ac35_llm_view.py` |

Altri test: system prompt identico all'Appendice E.1; schema generato equivalente all'Appendice F (accetta e
rifiuta le stesse risposte); struttura del messaggio utente (E.2) e del retry (E.3); scelta dell'esempio per
ancora e `_s07_alt.json` in modalità avversario; politica di rete (429/5xx/529 e connessione con attese e
`retry-after`, 400/401/403 senza tentativi, `temperature` rifiutata); riservatezza (nomi, tag e percorsi di un
PGN non arrivano al messaggio).

Suite: `pytest` → **482 test superati, nessuno saltato**, senza motori né rete. Verificato il 4 ottobre 2026
dopo la registrazione definitiva, con l'indice delle aperture costruito da
`scripts/setup_engines.py --skip stockfish maia syzygy`; senza l'indice AC-01 fallisce sul titolo dell'apertura.

**Stato: M1c chiusa** il 4 ottobre 2026.

## Registrazione delle risposte reali (storia)

AC-10 e AC-21 nella parte «modello» richiedono una chiamata vera: con `OPENROUTER_API_KEY` impostata (D-64),

```bash
.venv/bin/pytest -m llm --record      # registra real_najdorf_w_1500/1900 e real_najdorf_after_be3_w_1900
.venv/bin/pytest                      # i tre test non sono più saltati
```

### Tentativo di registrazione del 4 ottobre 2026

Non riuscito, M1c restava aperta. Nell'ambiente cloud `OPENROUTER_API_KEY` non è impostata e il proxy
non autentica le richieste a `openrouter.ai` (ogni chiamata, anche a `/api/v1/chat/completions` con un
messaggio di prova, risponde `401 No cookie auth credentials found`). Il test di registrazione quindi si
salta e nessuna risposta di DeepSeek è stata ancora vista né verificata. Prompt ed esempi non sono stati
toccati. Per chiudere basta ripetere i due comandi qui sopra in una sessione in cui la chiave è disponibile
(variabile d'ambiente dell'ambiente cloud oppure in locale).

### Secondo tentativo, 4 ottobre 2026

Non riuscito, M1c restava aperta. Questa volta `OPENROUTER_API_KEY` è impostata nell'ambiente, ma
OpenRouter rifiuta ogni richiesta con `401 No cookie auth credentials found` (lo stesso errore che dà senza
chiave): `pytest -m llm --record` → 3 test falliti con `ModelError: Chiave API non valida o non autorizzata`,
nessuna risposta registrata. Il client gestisce correttamente il caso (401 non ritentato, messaggio in
italiano, chiave mai scritta nei log). Il modello quindi non ha ancora risposto e non ci sono errori di
verifica di DeepSeek da esaminare; prompt ed esempi non sono stati toccati. La suite senza rete resta a
474 superati e 3 saltati. Per chiudere serve una chiave OpenRouter valida (impostata come variabile
d'ambiente dell'ambiente cloud, oppure in locale) e i due comandi qui sopra.

### Registrazione del modello reale, 4 ottobre 2026

Al terzo tentativo `OPENROUTER_API_KEY` arriva finalmente a OpenRouter. I primi due erano falliti con un 401: il
proxy dell'ambiente cloud sostituiva la chiave con una credenziale vuota.

**Prima registrazione.** AC-10 è passato. AC-21 invece si è fermato: nell'ultima risposta DeepSeek aveva scritto
`{{pct:root.draw}}` nelle `notes`, che nessun controllo guardava, e V11 ha interrotto il render. Con l'approvazione
dell'utente V03 vale ora anche per le note (OQ-M1c-10). Una nota sbagliata provoca un retry e, se l'errore resta,
la nota viene rimossa e la rimozione compare nel rapporto. Prompt ed esempi sono invariati.

**Registrazione definitiva** (dopo la correzione), modello `deepseek/deepseek-v4.1-flash`:

| Pacchetto | Tentativo 1 | Tentativo 2 | Tentativo 3 | Esito |
| --- | --- | --- | --- | --- |
| `najdorf_w_1500` | V07(d) (S06 lunga) | nessun errore | — | completo, 1 retry |
| `najdorf_w_1900` | V01: manca un campo obbligatorio | V03 nelle note, V04 su due piani, V07(d) | V03 nelle note (cifre) | degradata: rimosse le note 2 e 3, testo intatto |
| `najdorf_after_be3_w_1900` (AC-21) | V02 (N8), V03 nelle note, V04, V06, V07(a)(d), V09 «Scheveningen», «Dragon» | solo V07(d) | nessun errore | completo, 2 retry |

Qualità di DeepSeek (D-67), sulle tre analisi:
- **Retry:** 5, in media 1,7 per analisi. Un'analisi su tre finisce in modalità degradata, e solo per le note.
- **Errori più frequenti:**
  - confonde il nodo di partenza di una mossa con quello che si ottiene dopo averla giocata (V04);
  - usa ID di nodi che il pacchetto non ha (V02);
  - scrive cifre e ID nelle note (V03);
  - scrive testi fuori budget (V07(d));
  - nomina aperture dell'esempio (V09).
- I retry li correggono quasi sempre. Il testo per l'utente non ha mai avuto rimozioni.

## Uso

```bash
export OPENROUTER_API_KEY=...                              # mai scritta su disco né nei log
.venv/bin/chessanalyst analyze --yes --elo 1900
.venv/bin/chessanalyst rerun output/<cartella>             # rifà modello, verifica e render da pack.json
```

Senza chiave l'analisi dei motori viene comunque salvata (`pack.json`) e l'uscita è con codice 4 e
l'indicazione del comando `rerun`. Scelte e default: `docs/OPEN_QUESTIONS.md` (OQ-M1c-1…10).
