# Chess Position Analyst — regole per Claude Code
- Fonte di verità: docs/Chess_Position_Analyst_Documentazione_tecnica_v0_9_1.md. La v0.9.1 è CONGELATA:
  il registro decisioni (§0.3, D-01…D-63) prevale e non si riapre; tra due decisioni vale l'ID più alto.
- Decisioni dell'utente successive al congelamento: docs/DECISIONI_POST_CONGELAMENTO.md (D-64…); prevalgono
  sui punti della v0.9.1 che modificano (D-64 fornitore OpenRouter/Anthropic, D-65 costanti, D-66 Stockfish).
- Le Appendici D–G sono normative: i file di config/ partono esattamente da quei contenuti.
- Lavora per milestone nell'ordine M0, M1a, M1b, M1c, M2… (§13). Non implementare funzioni di milestone
  successive. Opzioni non ancora disponibili: rifiuto esplicito, codice di uscita 2 (D-30).
- Non inventare versioni/API: verifica Stockfish, python-chess, Maia-2, Anthropic, OpenRouter dalle fonti ufficiali.
  Maia-2 si importa solo in engines/maia2.py; Stockfish solo in engines/stockfish.py.
- Nessuna costante numerica nel codice: tutto in config/*.yaml (§0.5 dice chi può cambiare che cosa).
- Il LLM non scrive mai numeri o mosse in chiaro: token di §9-bis. Tabelle, titoli, testata, frasi fisse
  e rapporto li scrive il render.
- Testi per l'utente in italiano; codice, commenti, chiavi in inglese; multipiattaforma (pathlib, niente
  shell); nomi di file solo ASCII (D-34).
- Test senza motori né rete (fixture registrate, Appendice G). Ogni bug di verifica diventa un test di
  fault injection. Un file di test per ogni criterio AC in tests/acceptance/.
- Se una premessa del documento è falsa e non è tra i parametri di §0.5: FERMATI, scrivi problema, prova
  e proposta in docs/OPEN_QUESTIONS.md e chiedi all'utente.
- Dubbi minori: default di §15.2, annotati in docs/OPEN_QUESTIONS.md.
- Mai salvare o stampare la chiave API; mai inviare PGN, nomi o percorsi all'API.
