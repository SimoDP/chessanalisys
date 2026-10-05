"""D-72: prompt of the document made of key points. For each section the model receives ONLY the facts of its
key point, the guide sentence of the point's type, the tokens it may use and the assertions already written.
The pack is not sent: everything the text may say is in the facts.

The system prompt is short and the same for every pack (cached); the user message is one block per section.
"""

from __future__ import annotations

import json
import math

from chessanalyst.config import Config
from chessanalyst.verify.resolve import ResolveError, Resolver
from chessanalyst.verify.tokens import clean_san
from chessanalyst.verify.wordcount import tolerance

SYSTEM_PROMPT_KP = """Scrivi in italiano le sezioni brevi di un'analisi di scacchi per un giocatore di un dato livello.
Il programma ha già scelto, ordinato e verificato i fatti (Stockfish, Maia-2, la scacchiera): tu li racconti
con frasi chiare, senza aggiungere nulla. Consegni solo chiamando lo strumento submit_analysis.

REGOLE
1. Scrivi una sezione per ogni <punto>, con il suo id, nell'ordine dato, nell'intervallo di parole indicato.
   Niente titoli e niente tabelle: li inserisce il programma.
2. Ogni mossa, valutazione, perdita, probabilità e variante si scrive SOLO con i token che trovi nei fatti
   del punto (i valori di mossa, valutazione, perdita, probabilita, variante), copiati esattamente. Nel testo libero: nessuna cifra, nessuna mossa in notazione, nessuna percentuale, nessuna catena
   di case; ammessi le case isolate (e4), i nomi dei pezzi, i conteggi in lettere («tre isole»).
3. Racconta solo i fatti del punto. Non usare token né fatti di altri punti, non inventare pezzi, attacchi,
   minacce o piani: ogni frase è confrontata con la scacchiera e con i dati, e le frasi false vengono tolte.
4. Le parole delle bande: band dice il giudizio (legenda sotto), maia_band quanto è probabile. Il verdetto
   segue sempre la banda di N1.
5. Ogni blocco è {"type": "p", "text": …, "source": …, "assertions": […]} oppure un elenco
   {"type": "ul" | "ol", "items": [{"text": …, "source": …, "assertions": […]}]}. source è mixed se il blocco
   ha almeno un token o un'asserzione, theory se non ne ha (solo dove il punto ammette theory). Le asserzioni
   sono solo quelle pronte del punto: copia nel blocco quelle che il suo testo afferma, nessun'altra.
6. Gli argomenti di submit_analysis sono {"schema_version": "1", "sections": [...], "notes": []}.

ESEMPIO (un'altra posizione: imita la forma, non il contenuto)
<punto id="S01" tipo="verdict" parole="25-45" theory="no">
Fatti: {"valutazione":"{{ev:N1}}","band":"clear_plus","better":"user","material_balance_user":0,"positional":true,
"best":{"piece":"cavallo bianco","from":"f3","to":"g5","told_in":"recommendation"}}
</punto>
<punto id="S03" tipo="recommendation" parole="35-60" theory="no">
Fatti: {"mossa":"{{mv:C1}}","valutazione":"{{ev:C1}}","probabilita":"{{pct:C1.p_user}}","piece":"cavallo bianco",
"from":"f3","to":"g5","attacks":[{"square":"f7","piece":"pedone nero","defended":false}],"band":"clear_plus",
"maia_band":"possible","only_move":true,"second":{"mossa":"{{mv:C2}}","perdita":"{{loss:C2}}"}}
</punto>
Consegna:
{"schema_version":"1","notes":[],"sections":[
{"id":"S01","blocks":[{"type":"p","source":"mixed","text":"Hai un vantaggio netto ({{ev:N1}}). Il materiale è pari: il vantaggio viene dall'attività dei pezzi, e una mossa di cavallo lo rende concreto.","assertions":[{"kind":"eval_band","ref":"N1","band":"clear_plus"}]}]},
{"id":"S03","blocks":[{"type":"p","source":"mixed","text":"Gioca {{mv:C1}} ({{ev:C1}}): il cavallo va in g5 e attacca il pedone indifeso in f7. È l'unica mossa che tiene, perché {{mv:C2}} perde {{loss:C2}}. Al tuo livello è una scelta possibile ({{pct:C1.p_user}}): va cercata.","assertions":[{"kind":"maia_band","ref":"C1.p_user","band":"possible"}]}]}]}"""

GUIDE = {
    "verdict": "Chi sta meglio e di quanto, con le parole della banda e il token di N1; poi il perché in una "
               "frase (la mossa migliore e che cosa fa, il materiale; compensation: perché il materiale non basta; "
               "easy_for: per chi muove è facile trovare una buona mossa). Se la mossa migliore è raccontata in "
               "un altro punto (told_in), nominala solo a parole («una mossa forte»), senza token.",
    "recommendation": "La mossa da giocare, perché (che cosa fa sulla scacchiera) e quanto è probabile che la "
                      "trovi; se only_move, dì che è l'unica che tiene e quanto perde la seconda; la trappola da "
                      "evitare se c'è (is_trap: la seconda è anche la trappola naturale); reply: la risposta quasi "
                      "obbligata dell'avversario e come continui.",
    "systems": "Non c'è una mossa unica: presenta le mosse equivalenti come scelte di stile, con la loro idea.",
    "plan": "Il piano per le mosse tranquille dai fatti: debolezze dell'avversario da attaccare, pezzi da "
            "difendere, punti forti propri, la mossa tipica dell'avversario. Una frase per fatto. pinned: il "
            "pezzo inchiodato (by inchioda, behind è dietro); king_square: casa vicino al re difesa solo dal "
            "re e i pezzi che la possono colpire; pawn_break: la spinta di pedone che attacca i pedoni "
            "centrali (hits) e apre il gioco; secondary: un tuo punto forte che non cambia il giudizio, "
            "dillo («non basta»).",
    "main_danger": "La mossa più pericolosa dell'avversario: che cosa fa, quanto danno fa e quanto è probabile "
                   "che la giochi; la risposta migliore se c'è. Se hypothetical, è ciò che l'avversario "
                   "farebbe se tu non reagissi: dillo così.",
    "likely_reply": "Le risposte più probabili dell'avversario, una frase o due ciascuna (gains_space: il pedone guadagna "
                    "spazio su quell'ala): la risposta giusta "
                    "(only_answer = l'unica) e la trappola naturale (trap: la risposta istintiva che perde).",
    "opportunity": "Le mosse probabili dell'avversario che ti regalano qualcosa: che cosa sbaglia e come ne "
                   "approfitti (answer).",
    "reasoning": "Un elenco ol di {items} punti brevi, source theory, su come ragionare in questa posizione: "
                 "le domande da farsi prima di muovere, legate ai punti precedenti ma senza token.",
}

LEVEL = {
    "lt1200": "frasi brevi, istruzioni dirette, idee prima del calcolo",
    "1200_1600": "frasi brevi, istruzioni dirette, idee prima del calcolo",
    "1600_2000": "tecnico: strutture, piani e perché funzionano",
    "2000_2400": "sintetico e preciso, senza spiegare l'ovvio",
    "ge2400": "sintetico e preciso, senza spiegare l'ovvio",
}


def _token_forms(ref: str) -> list[str]:
    if ref == "root":
        return ["{{pct:root.win}}", "{{pct:root.draw}}", "{{pct:root.loss}}"]
    if "@" in ref:
        return [f"{{{{m:{ref}}}}}", f"{{{{ev:{ref}}}}}", f"{{{{loss:{ref}}}}}", f"{{{{pct:{ref}}}}}"]
    if ref.startswith("PV"):
        return [f"{{{{pv:{ref}:{{n}}}}}}"]
    if ref.startswith("L"):
        return [f"{{{{pv:{ref}:1}}}}", f"{{{{ev:{ref}}}}}", f"{{{{loss:{ref}}}}}", f"{{{{pv:{ref}:{{n}}}}}}"]
    if ref.startswith("N"):
        return [f"{{{{ev:{ref}}}}}"]
    if ref.startswith("C"):
        return [f"{{{{mv:{ref}}}}}", f"{{{{ev:{ref}}}}}", f"{{{{loss:{ref}}}}}", f"{{{{pct:{ref}.p_user}}}}"]
    if "." in ref:
        return [f"{{{{mv:{ref}}}}}", f"{{{{ev:{ref}}}}}", f"{{{{loss:{ref}}}}}", f"{{{{pct:{ref}.p_user}}}}"]
    return [f"{{{{mv:{ref}}}}}", f"{{{{ev:{ref}}}}}", f"{{{{pct:{ref}.p_opp}}}}"]


TOKEN_NAMES = {"mv": "mossa", "m": "mossa", "ev": "valutazione", "loss": "perdita", "pct": "probabilita",
               "pv": "variante"}
# numbers and notation of the facts: the model reads them as tokens (D-72, data given ready-made)
RAW_KEYS = {"ref", "san", "move", "eval_user_cp", "mate_user", "p_opp", "p_user", "p_att", "loss_cp", "damage_cp",
            "gain_cp", "impact_cp", "line", "after", "material_balance_user"}


def _tokens_of(ref: str, section: dict, r: Resolver) -> dict[str, str]:
    """name → token of the forms of ``ref`` that resolve on the pack (a token to a null value is not offered)."""
    out = {}
    for form in _token_forms(ref):
        if "{n}" in form:
            n = len((r.pvs.get(ref) or r.lines.get(ref) or {}).get("plies", []))
            form = form.replace("{n}", str(min(n, section["max_pv_plies"])))
        try:
            r.resolve(form)
        except (ResolveError, KeyError, TypeError, ValueError):
            continue
        kind = form[2:].split(":", 1)[0]
        out.setdefault("mossa" if kind == "pv" and form.endswith(":1}}") else TOKEN_NAMES[kind], form)
    return out


def allowed_tokens(cfg: Config, pack: dict, section: dict, resolver: Resolver | None = None) -> list[str]:
    r = resolver or Resolver(pack, cfg.wording)
    return [t for ref in section["cites_allowed"] for t in _tokens_of(ref, section, r).values()]


def _pv_of(ref: str, pack: dict) -> str | None:
    """The variation that follows a candidate (its pv) or an opponent's reply (PV of the same number)."""
    if ref.startswith("C"):
        return next((c.get("pv") for c in pack["engine"]["candidates"] if c["id"] == ref), None)
    if ref.startswith("R") and "." not in ref and "@" not in ref:
        return f"PV{ref[1:]}"
    return None


def facts_view(pack: dict, kp: dict, section: dict, r: Resolver) -> dict:
    """The facts of the point as the model reads them: every move, value and probability is already its token;
    no number of the engine, no notation. A fact of a move told in another section keeps only its words."""
    allowed = set(section["cites_allowed"])

    def norm(ref: str) -> str:
        if "@" in ref:
            san, node = ref.split("@", 1)
            return f"{clean_san(san)}@{node}"
        return ref

    def view(x):
        if isinstance(x, list):
            return [view(v) for v in x]
        if not isinstance(x, dict):
            return x
        out = {}
        refs = [x.get("ref"), x.get("line")]
        if isinstance(x.get("san"), str) and not x.get("ref"):        # a move of the plan, cited where first played
            refs += [a for a in allowed if a.startswith(clean_san(x["san"]) + "@")][:1]
        for ref in refs:
            if isinstance(ref, str) and norm(ref) in allowed:
                out.update(_tokens_of(norm(ref), section, r))
                pv = _pv_of(norm(ref), pack)
                if pv in allowed:
                    out.update({k: v for k, v in _tokens_of(pv, section, r).items() if k == "variante"})
        if isinstance(x.get("move"), dict):
            out.update({k: v for k, v in x["move"].items() if k != "move"})
        out.update({k: view(v) for k, v in x.items() if k not in RAW_KEYS})
        if isinstance(out.get("diagonal"), str):
            out["diagonal"] = "{{diag:" + out["diagonal"] + "}}"
        return out

    head = _tokens_of("N1", section, r) if kp["type"] == "verdict" else {}
    return head | view(kp["facts"])


def _with_maia(node) -> list[dict]:
    """Every fact (at any depth) with a ref and a Maia-2 band."""
    if isinstance(node, list):
        return [d for x in node for d in _with_maia(x)]
    if not isinstance(node, dict):
        return []
    own = [node] if "maia_band" in node and node.get("ref") and not node["ref"].startswith("L") else []
    return own + [d for v in node.values() for d in _with_maia(v)]


def ready_assertions(pack: dict, kp: dict) -> list[dict]:
    """Assertions the text of the point can copy: the band of N1 in the verdict, the features of the plan."""
    f, out = kp["facts"], []
    user = pack["user"]["color"]
    side = {"user": user, "opp": "b" if user == "w" else "w"}
    if kp["type"] == "verdict":
        out.append({"kind": "eval_band", "ref": "N1", "band": f["band"]})
    for d in _with_maia(f):
        ref = d["ref"]
        pct = ref if "@" in ref else f"{ref}.p_opp" if "p_opp" in d else f"{ref}.p_user"
        out.append({"kind": "maia_band", "ref": pct, "band": d["maia_band"]})
    if kp["type"] == "plan":
        keys = {(x["key"], x["side"]) for x in pack["features"]}
        for i in f["items"]:
            if i.get("squares") is not None and (i["key"], side[i["of"]]) in keys:
                out.append({"kind": "feature", "key": i["key"], "side": side[i["of"]],
                            "squares": i.get("squares") or []})
    return out


def _legend(cfg: Config, facts: str) -> list[str]:
    ev = []
    for key, b in cfg.wording["eval_bands"].items():
        pairs = [(key, b.get("text"))] if key == "equal" else [
            (f"{key}_plus", b["text_plus"]), (f"{key}_minus", b["text_minus"])]
        ev += [f"{k} = «{t}»" for k, t in pairs if f'"{k}"' in facts]
    maia = [f"{k} = «{b['text']}»" for k, b in cfg.wording["maia_bands"].items() if f'"{k}"' in facts]
    return ([("Bande: " + "; ".join(ev) + ".")] if ev else []) + (
        [("Probabilità: " + "; ".join(maia) + ".")] if maia else [])


def section_block(cfg: Config, pack: dict, kp: dict, section: dict, resolver: Resolver | None = None) -> str:
    tol = tolerance(section["word_budget"], cfg.verify["word_tolerance"])
    lo, hi = max(0, math.ceil(section["word_budget"] - tol)), math.floor(section["word_budget"] + tol)
    guide = GUIDE[kp["type"]].replace("{items}", str(kp["facts"].get("items", "")))
    facts = json.dumps(facts_view(pack, kp, section, resolver or Resolver(pack, cfg.wording)), ensure_ascii=False,
                       separators=(",", ":"))
    lines = [f'<punto id="{section["id"]}" tipo="{kp["type"]}" parole="{lo}-{hi}" '
             f'theory="{"ammessa" if section["theory_allowed"] else "no"}">',
             f"Guida: {guide}"]
    if section["must_cover"]:
        lines.append("Da citare: ogni mossa dei fatti, con il suo token")
    ready = ready_assertions(pack, kp)
    if ready:
        lines.append(f"Asserzioni pronte: {json.dumps(ready, ensure_ascii=False, separators=(',', ':'))}")
    lines += [f"Fatti: {facts}", "</punto>"]
    return "\n".join(lines)


def build_user_message_kp(cfg: Config, pack: dict, sections: list[str] | None = None) -> str:
    """The message of the keypoint document; ``sections`` limits it to some sections (one call per section)."""
    u = pack["user"]
    plan = {s["id"]: s for s in pack["section_plan"]}
    resolver = Resolver(pack, cfg.wording)
    me = cfg.wording["colors"][u["color"]]
    mode = "tocca a te" if pack["position"]["user_to_move"] else "tocca all'avversario"
    blocks, all_facts = [], ""
    for kp in pack["key_points"]:
        if sections is not None and kp["section"] not in sections:
            continue
        blocks.append(section_block(cfg, pack, kp, plan[kp["section"]], resolver))
        all_facts += json.dumps(kp["facts"], ensure_ascii=False)
    head = [f"Giochi con {me}, {mode}. Livello: {LEVEL[u['band']]}. «Tu» è sempre il giocatore.",
            *_legend(cfg, all_facts), ""]
    ids = [kp["section"] for kp in pack["key_points"] if sections is None or kp["section"] in sections]
    tail = ["", f"Consegna con submit_analysis le sezioni {', '.join(ids)}, in quest'ordine."]
    return "\n".join(head + blocks + tail)


def prune_assertions(pack: dict, response: dict) -> int:
    """Feature assertions on a key the pack does not have (``pinned``, ``king_square``… are facts of the key
    points, not features) can never be true: they are dropped before the check. Returns how many."""
    keys = {x["key"] for x in pack["features"]}
    dropped = 0
    for block in response.get("content", []):
        if block.get("type") != "tool_use" or not isinstance(block.get("input"), dict):
            continue
        for sec in block["input"].get("sections") or []:
            for b in sec.get("blocks") or []:
                for unit in [b, *(b.get("items") or [])]:
                    if not isinstance(unit, dict) or not isinstance(unit.get("assertions"), list):
                        continue
                    keep = [a for a in unit["assertions"]
                            if not (isinstance(a, dict) and a.get("kind") == "feature" and a.get("key") not in keys)]
                    dropped += len(unit["assertions"]) - len(keep)
                    unit["assertions"] = keep
    return dropped
