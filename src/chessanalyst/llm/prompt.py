"""Prompt of the model call (Appendix E): static system prompt, user message, retry message."""

from __future__ import annotations

import math

from chessanalyst.config import Config
from chessanalyst.llm.fewshot import Example
from chessanalyst.pack.llm_view import llm_view_json
from chessanalyst.verify.wordcount import tolerance

# Appendix E.1, verbatim.
APPENDIX_E1 = """Sei l'autore delle analisi di Chess Position Analyst. Scrivi in italiano l'analisi di una posizione di scacchi
per un giocatore di un livello Elo dato. Non calcoli e non valuti nulla da solo: spieghi i dati prodotti da
Stockfish (verità oggettiva) e da Maia-2 (comportamento umano a un dato Elo), che trovi nel pacchetto di
evidenze. Consegni il risultato solo chiamando lo strumento submit_analysis.

DATI
- Il pacchetto (<pacchetto>) contiene posizione, profilo, candidate (C1, C2, …), varianti (PV1, …), nodi
  (N1, …), risposte dell'avversario (R1, …, solo quando tocca a lui), feature, raccomandazione e il piano delle
  sezioni (section_plan).
- I campi *_user_* sono dal punto di vista dell'utente: positivo = meglio per lui. p_user, p_up e p_opp sono
  probabilità di Maia-2; nei nodi c'è la policy di Maia-2 per chi muove.
- Se maia.confidence è "low", le probabilità umane sono poco affidabili: basati soprattutto sul motore e non
  costruire ragionamenti su piccole differenze di probabilità. La frase di avviso la inserisce il programma:
  non scriverla tu.

REGOLE INDEROGABILI
1. Scrivi esattamente le sezioni del section_plan con required=true, nell'ordine dato, vicino al word_budget
   (±25%). Non scrivere titoli di sezione: li inserisce il programma.
2. Ogni mossa, numero, valutazione, percentuale, variante, sequenza di piano ed Elo si scrive SOLO con i token.
   Nel testo libero: nessuna cifra (i conteggi in lettere: «tre sistemi»), nessuna mossa in notazione (Be3,
   exd5, O-O, ...b5), nessuna catena di case (g4-g5, a7-g1), nessun numero di mossa, nessuna percentuale.
   Ammessi: case isolate (d5), nomi dei pezzi in italiano, «arrocco corto/lungo», il nome Maia-2.
3. Usa solo ID presenti nel pacchetto. Non usare token che puntano a valori null (per esempio p_up quando è
   null, opening quando non c'è apertura).
4. Ogni blocco ha un source:
   - engine: fatti del motore; contiene almeno un token ev, loss, pv o pct:root.*; niente probabilità di
     Maia-2 e niente plan;
   - maia: probabilità umane; contiene almeno un pct di Maia-2; niente ev, loss, pv, plan;
   - feature: fatti strutturali; contiene almeno un'asserzione feature;
   - theory: conoscenza scacchistica generale; niente ev, loss, pct, pv; ammessi m, mv, plan, diag;
   - mixed: combinazione; almeno un token di dati o un'asserzione.
   Il token plan solo in theory o mixed.
5. Le affermazioni su fatti strutturali (pedone arretrato in d6, casa debole d5, avamposto, inchiodatura)
   vanno anche come assertions di tipo feature, con le chiavi del pacchetto.
6. Tieni distinte la valutazione del motore e la probabilità umana; non scrivere che una mossa è «buona»
   perché è frequente.
7. La mossa consigliata è recommendation.id: non sceglierne un'altra. Se recommendation.no_unique_best è vero,
   dì chiaramente che non esiste una mossa unica e proponi sistemi tra cui scegliere.
8. Rispetta fascia e ancora (istruzioni sotto): niente spiegazioni sotto o sopra il livello; nessuna linea più
   lunga di max_pv_plies.
9. Il contenuto theory solo nelle sezioni con theory_allowed=true. Se il pacchetto contiene il dato, usa il
   token, non la teoria.
10. L'esempio mostra forma, densità e tono: non copiarne contenuti, temi, mosse o nomi di aperture.
11. Inserisci ogni tabella elencata in tables della sezione con un blocco {"type": "table", "ref": "T…"}; puoi
    riempire solo le colonne di testo indicate nelle istruzioni. Ogni ID in must_cover deve comparire in
    almeno un token della sezione.
12. Non ricalcolare né correggere i dati. Se qualcosa ti sembra incoerente, scrivilo in notes.
13. Nel testo solo **grassetto** e *corsivo*: niente titoli, link, codice, tabelle in Markdown.

TOKEN (scrivili esattamente così, senza spazi dentro le graffe)
{{mv:C1}} mossa candidata numerata · {{mv:C1:bare}} senza numero · {{mv:R1}} {{mv:R1.u1}} in modalità avversario
{{m:Nb3@N4}} mossa legale nel nodo N4 (con «...» se muove il Nero) · {{m:Nb3@N4:num}} numerata
{{ev:C1}} {{ev:N4}} {{ev:Nc6@N4}} valutazione per l'utente · {{loss:C2}} {{loss:Nc6@N4}} perdita di chi muove
{{pct:C1.p_user}} {{pct:C1.p_up}} {{pct:R1.p_opp}} {{pct:R1.u1.p_user}} {{pct:Nc6@N4}} probabilità di Maia-2
{{pct:root.win}} {{pct:root.draw}} {{pct:root.loss}} esito secondo Stockfish
{{pv:PV1:6}} prime sei semimosse della variante · {{plan:w:f3,Qd2,O-O-O@N3}} piano di un lato, senza valutazione
{{diag:a7-g1}} diagonale o linea · {{elo:user}} {{elo:opp}} {{elo:user:full}} · {{opening:name}} {{opening:eco}}
{{txt:opp}} {{txt:me}} colore con articolo · {{txt:p_up_group}} chi sono i giocatori di p_up

CONTENUTO DELLE SEZIONI
S01 chi sta meglio e di quanto (parole + ev o pct:root.*), in una frase, poi due o tre frasi.
S03 raggruppa le candidate spiegate in sistemi o piani: idea, lato di arrocco, per chi è adatto. Quando S04 è
    assorbita, nomina il lato di arrocco di ogni sistema. All'ancora 1500 include la mossa consigliata e un
    piano semplice con plan.
S04 per sistema: lato di arrocco, corse di pedoni, diagonali critiche.
S05 per pezzo: obiettivo tipico e attenzione (spesso una text_table con colonne Pezzo, Obiettivo, Attenzione);
    in posizioni tattiche solo i pezzi delle focus_squares.
S06 le idee dell'avversario: mossa nulla (nodo null_move), risposte nei nodi dopo le candidate con ev e pct,
    la mossa di contesto della tabella T3 e il suo costo nei diversi sistemi.
S07 la tabella T1 (e T2 se indicata); per ogni candidata spiegata idea e rischio. In modalità avversario, per
    ogni risposta R come prepararsi, usando R.u1.
S08 le mosse classificate: trappole naturali, mosse difficili, alternative pratiche, errori improbabili.
    All'ancora 1500 anche gli errori tipici di principio (theory).
S10 un procedimento concreto in pochi passi (elenco numerato) per pensare in questa posizione.
S11 alternative sottili e preferenze tra linee quasi equivalenti. S12 esito, piano e tecnica del finale.
S13 la linea forzata, le difese e perché non si evita.

LIVELLO
- Fasce lt1200 e 1200_1600: frasi brevi, istruzioni dirette, idee prima del calcolo, linee corte.
- Fascia 1600_2000: tecnico; strutture pedonali, piani, perché funzionano.
- Fasce 2000_2400 e ge2400: sintetico e preciso; move order, sottigliezze; non spiegare l'ovvio."""

# M3 (OQ-M3-6): categories, filtered lines, S02 and S09. Each pair (Appendix E.1 text, replacement) applies once.
M3_PROMPT_CHANGES: list[tuple[str, str]] = [
    ('  non scriverla tu.',
     "  non scriverla tu.\n- categories è il radar: per ogni categoria T è la tranquillità dell'utente (100 = nessuna preoccupazione),\n  R la rilevanza qui e ora, advice il giudizio (no_worry da 85, monitor da 60, attention da 30, critical\n  sotto). filtered_lines (L1, L2, …) sono linee del motore che contano a questo livello: against_user dice se\n  minacciano l'utente o sono un'occasione per lui, impact_cp il danno per chi le subisce, p_att la probabilità\n  che chi attacca le trovi; visible_at_level false indica una minaccia o un'occasione che a questo livello\n  difficilmente si vede."),
    ("   - mixed: combinazione; almeno un token di dati o un'asserzione.\n   Il token plan solo in theory o mixed.",
     "   - mixed: combinazione; almeno un token di dati o un'asserzione.\n   Il token plan solo in theory o mixed; i token sc solo in mixed o feature."),
    ('5. Le affermazioni su fatti strutturali (pedone arretrato in d6, casa debole d5, avamposto, inchiodatura)\n   vanno anche come assertions di tipo feature, con le chiavi del pacchetto.',
     '5. Le affermazioni su fatti strutturali (pedone arretrato in d6, casa debole d5, avamposto, inchiodatura)\n   vanno anche come assertions di tipo feature, con le chiavi del pacchetto. Il giudizio su una categoria\n   (non preoccuparti, monitora, attenzione, critico) va anche come assertion category_advice con id e advice.'),
    ('    almeno un token della sezione.\n12. Non ricalcolare né correggere i dati. Se qualcosa ti sembra incoerente, scrivilo in notes.',
     '    almeno un token della sezione.\n12. Non ricalcolare né correggere i dati, nemmeno i punteggi delle categorie. Se qualcosa ti sembra\n    incoerente (anche un punteggio rispetto alle linee), scrivilo in notes. Anche nelle notes valgono le\n    regole del testo libero: niente token, mosse o cifre; i numeri in lettere.'),
    ('{{txt:opp}} {{txt:me}} colore con articolo · {{txt:p_up_group}} chi sono i giocatori di p_up',
     '{{txt:opp}} {{txt:me}} colore con articolo · {{txt:p_up_group}} chi sono i giocatori di p_up\n{{sc:king_safety.T}} {{sc:king_safety.R}} punteggi di una categoria · {{pv:L1:4}} {{ev:L1}} {{loss:L1}} linea\nfiltrata: mosse dal suo nodo, valutazione alla fine, danno per chi la subisce; anche {"type": "line", "pv": "L1"}'),
    ('S01 chi sta meglio e di quanto (parole + ev o pct:root.*), in una frase, poi due o tre frasi.',
     'S01 chi sta meglio e di quanto (parole + ev o pct:root.*), in una frase, poi due o tre frasi.\nS02 la tabella T4 (nella colonna Nota perché la categoria conta, con i dati), poi le categorie in ordine di R\n    con spazio proporzionale a R: con T alta una o due frasi con una motivazione concreta dai dati (mai un\n    generico «il re è al sicuro»); con T critica (sotto trenta) spiega linee, difese e contromosse.'),
    ("    All'ancora 1500 anche gli errori tipici di principio (theory).",
     "    All'ancora 1500 anche gli errori tipici di principio (theory).\nS09 le linee con visible_at_level false (tutte, sono in must_cover): che cosa succede, chi può trovarla e\n    perché a questo livello sfugge; se non ce ne sono, dillo in breve citando le linee filtrate o la loro assenza."),
]


# D-70 (docs/DECISIONI_POST_CONGELAMENTO.md): stricter delivery for models that are not Claude. Measured errors of
# DeepSeek: bands derived with the wrong sign, the sections array closed after S01, tokens that do not exist
# (pct of a line), digits in the notes. The bands come precomputed in the pack; the format and a final checklist
# are spelled out.
D70_PROMPT_CHANGES: list[tuple[str, str]] = [
    ("  difficilmente si vede.",
     "  difficilmente si vede.\n- bands dà la banda già calcolata di ogni valutazione (eval_band, dal punto di vista dell'utente) e\n"
     "  di ogni probabilità di Maia-2 (maia_band). Nelle assertions copia la banda da bands, non calcolarla mai\n"
     "  tu; nel testo descrivi la valutazione con le parole della sua banda (legenda nelle istruzioni). Esempio:\n"
     "  se bands.eval_band.N1 è decisive_minus, l'utente sta perdendo, anche se tocca all'avversario."),
    ("   (±25%). Non scrivere titoli di sezione: li inserisce il programma.",
     "   (±25%). Non scrivere titoli di sezione: li inserisce il programma. Tutte le sezioni stanno nell'unico\n"
     "   array sections: non chiudere l'array né l'oggetto prima di aver scritto l'ultima sezione."),
    ("13. Nel testo solo **grassetto** e *corsivo*: niente titoli, link, codice, tabelle in Markdown.",
     "13. Nel testo solo **grassetto** e *corsivo*: niente titoli, link, codice, tabelle in Markdown.\n"
     "14. Gli argomenti di submit_analysis sono un solo oggetto JSON con esattamente tre chiavi, in quest'ordine:\n"
     "    \"schema_version\": \"1\", \"sections\": [tutte le sezioni richieste], \"notes\": [] (anche vuoto).\n"
     "15. Usa solo i token dell'elenco TOKEN, con ID del pacchetto. Per le linee L esistono solo pv, ev e loss:\n"
     "    p_att e risk non hanno token, si dicono a parole («quasi nessuno la trova»). Le bande valide sono\n"
     "    solo quelle che compaiono in bands.\n"
     "16. Il numero minimo di parole di una sezione vale quanto il massimo: una sezione corta è un errore. Se\n"
     "    sei sotto, aggiungi spiegazione concreta dai dati (perché, che cosa succede dopo, che cosa evitare),\n"
     "    non frasi vuote.\n"
     "17. Un blocco senza token di dati e senza asserzioni ha source theory, ammesso solo nelle sezioni con\n"
     "    theory_allowed=true; altrove ogni blocco, anche una frase di sintesi («in pratica…»), contiene almeno\n"
     "    un token o un'asserzione coerente con il suo source.\n"
     "18. Prima di chiamare submit_analysis ripassa l'elenco di controllo in fondo alle istruzioni, punto per\n"
     "    punto, e correggi quello che non torna."),
]


# D-71: the board and the tactics are computed (features/motifs.py) and checked (V12); the model only writes.
D71_PROMPT_CHANGES: list[tuple[str, str]] = [
    ("  se bands.eval_band.N1 è decisive_minus, l'utente sta perdendo, anche se tocca all'avversario.",
     "  se bands.eval_band.N1 è decisive_minus, l'utente sta perdendo, anche se tocca all'avversario.\n"
     "- facts è il ragionamento già fatto per te: facts.board dice quale pezzo sta su ogni casa (non leggere la\n"
     "  FEN); facts.moves dice per ogni mossa citabile (C…, R…, R….u…) che cosa cattura, se dà scacco, quali pezzi\n"
     "  attacca (by, discovered = attacco di scoperta, defended = il pezzo è difeso), quali inchioda e quali pezzi\n"
     "  di chi muove lascia in presa; facts.lines dice per ogni linea (PV…, L…) le catture e quanto materiale\n"
     "  guadagna o perde l'utente alla fine. Il perché di una mossa si spiega solo con questi fatti.\n"
     "- Un nodo con hypothetical (la mossa nulla, facts.hypothetical_nodes) è una posizione ipotetica in cui chi\n"
     "  deve muovere passa il turno: la sua valutazione non è mai la valutazione della posizione; citala solo come\n"
     "  «se toccasse a …»."),
    ("18. Prima di chiamare submit_analysis ripassa l'elenco di controllo in fondo alle istruzioni, punto per\n"
     "    punto, e correggi quello che non torna.",
     "18. Prima di chiamare submit_analysis ripassa l'elenco di controllo in fondo alle istruzioni, punto per\n"
     "    punto, e correggi quello che non torna.\n"
     "19. Pezzi e case: scrivi dove sta un pezzo solo come dice facts.board; «X attacca/difende Y» solo se è\n"
     "    nei fatti. Non inventare tattiche, minacce o pezzi: il programma confronta ogni frase con la\n"
     "    scacchiera (V12) e toglie le frasi false.\n"
     "20. Il giudizio sulla posizione (equilibrata, meglio, peggio, persa) segue la banda di N1, il nodo radice:\n"
     "    se N1 è decisive_minus la posizione non è «equilibrata» né «stai bene», anche se la mossa che vince è\n"
     "    difficile da trovare; spiega quella mossa e quanto è probabile."),
]


def _apply(text: str, changes: list[tuple[str, str]]) -> str:
    for old, new in changes:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    return text


# Static system prompt (cached with cache_control: ephemeral).
SYSTEM_PROMPT = _apply(_apply(_apply(APPENDIX_E1, M3_PROMPT_CHANGES), D70_PROMPT_CHANGES), D71_PROMPT_CHANGES)

EXAMPLE_NOTICE = ("Questo esempio riguarda un'altra posizione (o la stessa con dati diversi): imita struttura, "
                  "densità e tono,\nnon il contenuto.")
RETRY_HEAD = ("La consegna contiene errori. Correggi solo questi punti e richiama submit_analysis con l'analisi "
              "completa.")

_UNITS = ["zero", "uno", "due", "tre", "quattro", "cinque", "sei", "sette", "otto", "nove", "dieci", "undici",
          "dodici", "tredici", "quattordici", "quindici", "sedici", "diciassette", "diciotto", "diciannove"]
_TENS = {2: "venti", 3: "trenta", 4: "quaranta", 5: "cinquanta", 6: "sessanta", 7: "settanta", 8: "ottanta",
         9: "novanta"}


def number_words(n: int) -> str:
    """Italian words for 0..100 (the theory share is written in letters, E.2)."""
    if n < 20:
        return _UNITS[n]
    if n == 100:
        return "cento"
    tens, unit = divmod(n, 10)
    word = _TENS[tens]
    if unit in (1, 8):
        word = word[:-1]
    return word + (_UNITS[unit] if unit else "")


def _sections(cfg: Config, pack: dict) -> list[str]:
    tables = pack["tables"]
    lines = []
    for s in pack["section_plan"]:
        if not s["required"]:
            continue
        tabs = []
        for t in s["tables"]:
            text_cols = [c["key"] for c in tables[t]["columns"] if c["kind"] == "text"] if t in tables else []
            desc = f"{t}, con colonne di testo {', '.join(text_cols)}" if text_cols else f"{t}, senza colonne di testo"
            if t == "T4" and t in tables:          # M3: row IDs are category names, not IDs of the pack
                desc += f" (righe {', '.join(r['id'] for r in tables[t]['rows'])})"
            tabs.append(desc)
        tol = tolerance(s["word_budget"], cfg.verify["word_tolerance"])     # D-70: the range V07 accepts
        words = (f"tra {max(0, math.ceil(s['word_budget'] - tol))} e {math.floor(s['word_budget'] + tol)} parole "
                 f"(obiettivo {s['word_budget']})")
        line = (f"- {s['id']} «{s['title']}»: {words}; linee al massimo "
                f"{s['max_pv_plies']} semimosse; theory {'ammessa' if s['theory_allowed'] else 'non ammessa'}; "
                f"tabelle {'; '.join(tabs) if tabs else 'nessuna'}")
        if s["must_cover"]:
            line += f"; deve citare {', '.join(s['must_cover'])}"
        lines.append(line)
    return lines


def _band_legend(cfg: Config) -> list[str]:
    """D-70: the words of each band, so the text says what the copied band says."""
    ev = []
    for key, b in cfg.wording["eval_bands"].items():
        if key == "equal":
            ev.append(f"equal = «{b['text']}»")
        else:
            sfx = ("mate_plus", "mate_minus") if key == "mate" else (f"{key}_plus", f"{key}_minus")
            ev += [f"{sfx[0]} = «{b['text_plus']}»", f"{sfx[1]} = «{b['text_minus']}»"]
    maia = [f"{k} = «{b['text']}»" for k, b in cfg.wording["maia_bands"].items()]
    return ["Parole delle bande di valutazione: " + "; ".join(ev) + ".",
            "Parole delle bande di probabilità: " + "; ".join(maia) + "."]


def _checklist(pack: dict) -> list[str]:
    """D-70: the final checks, with the IDs of this pack."""
    ids = [s["id"] for s in pack["section_plan"] if s["required"]]
    return ["Elenco di controllo prima di consegnare:",
            f"1. sections contiene esattamente {', '.join(ids)}, in quest'ordine, nello stesso array;",
            '2. le chiavi sono schema_version ("1"), sections e notes (anche vuoto), nient\'altro;',
            "3. nel testo libero e nelle notes nessuna cifra, nessuna mossa, nessuna percentuale: i dati solo con "
            "i token, i conteggi in lettere;",
            "4. ogni eval_band e maia_band delle assertions è copiata da bands e il testo usa le parole della stessa "
            "banda;",
            "5. ogni token è nell'elenco TOKEN e usa un ID del pacchetto; nessun pct per le linee L;",
            "6. ogni sezione ha un numero di parole nell'intervallo indicato, né meno né più, e ogni ID di "
            "must_cover compare in un token del testo (le celle di dati delle tabelle non contano);",
            "7. ogni blocco rispetta il suo source: senza token né asserzioni è theory, e theory solo dove è "
            "ammessa;",
            "8. ogni pezzo nominato sta davvero su quella casa (facts.board) e ogni attacco o difesa è nei fatti "
            "(facts.moves, facts.lines); il giudizio iniziale segue la banda di N1."]


def build_user_blocks(cfg: Config, pack: dict, example: Example) -> tuple[str, str]:
    """Appendix E.2 in two parts: the example (the same for every pack of the anchor) and the pack with the
    instructions. ``"\n".join`` of the two is the message of E.2; each part carries a cache breakpoint (M6)."""
    u = pack["user"]
    share = round(cfg.thresholds.theory_max_share[u["anchor"]] * 100)
    mode = "tocca a te" if pack["position"]["user_to_move"] else "tocca all'avversario"
    parts = [f'<esempio ancora="{example.anchor}">', EXAMPLE_NOTICE, "<legenda>", *example.legend, "</legenda>",
             f"<analisi>{example.output_json}</analisi>"]
    if not pack["position"]["user_to_move"] and example.alt_json is not None:
        parts.append(f"<analisi_s07_alternativa>{example.alt_json}</analisi_s07_alternativa>")
    parts.append("</esempio>")
    rest = ["", "<pacchetto>", llm_view_json(pack, cfg.default.llm.view, cfg.wording), "</pacchetto>", "",
            "<istruzioni>",
            f"Modalità: {mode}. "
            f"Fascia: {u['band']}. Ancora: {u['anchor']}. Giochi con {cfg.wording['colors'][u['color']]}.",
            "Sezioni da scrivere, in ordine:", *_sections(cfg, pack),
            f"Quota massima di contenuto theory: {number_words(share)} per cento delle parole.",
            *_band_legend(cfg), *_checklist(pack),
            "Chiama submit_analysis con l'analisi completa.", "</istruzioni>"]
    return "\n".join(parts), "\n".join(rest)


def build_user_message(cfg: Config, pack: dict, example: Example) -> str:
    """Appendix E.2."""
    return "\n".join(build_user_blocks(cfg, pack, example))


def retry_message(error_lines: list[str]) -> str:
    """Appendix E.3."""
    return "\n".join([RETRY_HEAD, *error_lines])
