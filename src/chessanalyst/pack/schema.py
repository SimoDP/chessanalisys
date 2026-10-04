"""Evidence Pack schema (§6.2), pydantic v2. ``pack.json = model_dump_json(indent=2)``."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PositionInfo(M):
    fen: str
    epd: str
    side_to_move: Literal["w", "b"]
    fullmove: int
    legal_moves: int
    in_check: bool
    last_move_san: str | None
    user_to_move: bool


class History(M):
    source: Literal["example", "fen", "pgn"]
    plies: int
    repetitions: int
    start_fen: str | None


class UserInfo(M):
    color: Literal["w", "b"]
    elo_declared: int
    elo_scale: Literal["fide", "lichess", "chesscom"]
    elo_ref_fide: int
    elo_maia: int
    opp_elo_declared: int
    opp_elo_maia: int
    band: str
    anchor: Literal["1500", "1900", "2400"]
    detail_level: int
    language: Literal["it"]
    budget_profile: Literal["fast", "standard", "deep"]


class Material(M):
    w: int
    b: int
    balance: int


class Profile(M):
    phase: Literal["opening", "middlegame", "endgame"]
    castling: dict[str, str]
    tactical: bool
    tactical_reasons: list[str]
    quiet: bool
    spread_cp: int
    closed: bool
    tablebase: bool
    in_book: bool
    material: Material
    matrix_column: int


class Opening(M):
    eco: str
    name: str
    matched_by: Literal["epd", "sequence"]


class StockfishInfo(M):
    version: str
    threads: int | None
    hash_mb: int | None
    profile: str


class Root(M):
    node: str
    depth: int
    eval_user_cp: int
    mate_user: int | None
    wdl_user: list[int] | None


class Candidate(M):
    id: str
    san: str
    uci: str
    node: str | None
    source: Literal["e0", "e4"]
    e0_rank: int | None
    eval_user_cp: int
    mate_user: int | None
    loss_cp: int
    wdl_user: list[int] | None
    pv: str
    p_user: float
    p_up: float | None
    category: str | None
    complexity: int | None
    complexity_partial: bool
    explained: bool
    listed: bool
    rec_score: float | None


class UserBest(M):
    id: str
    san: str
    uci: str
    eval_user_cp: int
    mate_user: int | None
    loss_cp: int
    p_user: float


class Reply(M):
    id: str
    san: str
    uci: str
    node: str
    eval_user_cp: int
    mate_user: int | None
    p_opp: float
    user_best: list[UserBest]


class PV(M):
    id: str
    start_node: str
    plies: list[str]
    eval_end_user_cp: int


class E3Entry(M):
    level: int
    candidate: str
    path: list[str]
    node: str


class ContextRow(M):
    node: str
    path: list[str]
    best_san: str
    best_eval_user_cp: int
    move_eval_user_cp: int
    cost_cp: int
    p_opp: float


class ContextMove(M):
    san_by_node: dict[str, str]
    uci: str
    rows: list[ContextRow]
    spread_cp: int


class Transposition(M):
    a: str
    b: str
    ply_a: int
    ply_b: int


class NullMove(M):
    node: str


class Engine(M):
    stockfish: StockfishInfo
    root: Root
    candidates: list[Candidate]
    replies: list[Reply]
    pvs: list[PV]
    null_move: NullMove | None
    e3: list[E3Entry]
    context_move: ContextMove | None
    transpositions: list[Transposition]


class MaiaInfo(M):
    model_type: str
    package_version: str
    device: str
    bucket_user: int
    bucket_opp: int
    top_bucket_lower: int
    saturated: bool
    confidence: Literal["normal", "low"]
    p_up_elo: int | None
    p_up_bucket: Literal["higher", "top"] | None
    human_expected_score_user: float
    entropy_bits: float


class Recommendation(M):
    id: str
    strength: Literal["normal", "weak"]
    no_unique_best: bool


class Feature(M):
    key: str
    side: Literal["w", "b"] | None
    squares: list[str]
    value: Any = None


class Column(M):
    key: str
    header: str
    kind: Literal["data", "text"]


class Row(M):
    id: str
    cells: dict[str, str | None]


class Table(M):
    id: Literal["T1", "T2", "T3", "T4"]
    section: Literal["S02", "S06", "S07"]
    columns: list[Column]
    rows: list[Row]
    footnote: str | None


class MultiPVLine(M):
    rank: int
    san: str
    uci: str
    eval_white_cp: int
    mate_white: int | None
    eval_user_cp: int
    mate_user: int | None
    wdl_user: list[int] | None
    pv: list[str]


class PolicyEntry(M):
    san: str
    uci: str
    p: float


class NodeMaia(M):
    elo_self: int
    elo_oppo: int
    policy: list[PolicyEntry]
    expected_score_user: float


class Node(M):
    id: str
    fen: str
    epd: str
    parent: str | None
    via_san: str | None
    via_uci: str | None
    phase: Literal["E0", "E1", "E2", "E2b", "E2c", "E3l1", "E3l2", "E3l3", "R"]
    path: list[str]
    side_to_move: Literal["w", "b"]
    citable: bool
    depth: int
    seldepth: int | None
    nodes: int | None
    time_s: float
    unstable_depth: bool
    root_moves: list[str] | None
    multipv: list[MultiPVLine]
    maia: NodeMaia | None


class SectionPlanEntry(M):
    id: str
    title: str | None
    required: bool
    absorbed_into: str | None
    omitted: str | None
    word_budget: int | None
    max_pv_plies: int
    theory_allowed: bool
    tables: list[str]
    must_cover: list[str]
    focus_squares: list[str]
    maia_low_confidence: bool


class Omitted(M):
    id: str
    reason: str


class OmittedPhase(M):
    phase: str
    reason: str


class OmittedNode(M):
    phase: str
    reason: str
    ref: str


class Constraints(M):
    max_pv_plies: int
    plan_max_moves: int


class Pack(M):
    schema_version: Literal["0.9"] = "0.9"
    app_version: str
    created_utc: str
    config_hash: str
    position: PositionInfo
    history: History
    user: UserInfo
    profile: Profile
    opening: Opening | None
    engine: Engine
    maia: MaiaInfo
    recommendation: Recommendation | None
    features: list[Feature]
    categories: list = []
    filtered_lines: list = []
    tablebase: None = None
    tables: dict[str, Table]
    nodes: list[Node]
    section_plan: list[SectionPlanEntry]
    omitted_sections: list[Omitted]
    omitted_phases: list[OmittedPhase]
    omitted_nodes: list[OmittedNode]
    warnings: list[str]
    constraints: Constraints
