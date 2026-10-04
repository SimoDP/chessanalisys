"""Configuration loading and validation (§11.4, Appendix D).

Every file in ``config/`` is loaded with ``yaml.safe_load`` and validated by a
strict pydantic model: unknown keys are an error and so are non-string keys
(PyYAML reads an unquoted ``1200_1600`` as the integer 12001600, §0.7 #1).
``config/local.yaml`` (generated, not versioned) is deep-merged over
``config/default.yaml``.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from chessanalyst.errors import ConfigError

CONFIG_FILES = (
    "default.yaml",
    "exploration.yaml",
    "thresholds.yaml",
    "wording.yaml",
    "elo_conversion.yaml",
    "maia2_limits.yaml",
    "section_titles.yaml",
    "section_budget.yaml",
    "tables.yaml",
    "verify.yaml",
)
HASHED_FILES = ("exploration.yaml", "thresholds.yaml", "maia2_limits.yaml", "elo_conversion.yaml")

BAND_KEYS = ("lt1200", "1200_1600", "1600_2000", "2000_2400", "ge2400")
ANCHOR_KEYS = ("1500", "1900", "2400")
SECTION_IDS = tuple(f"S{i:02d}" for i in range(1, 14))


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# --- default.yaml -----------------------------------------------------------


class UserCfg(Strict):
    color: Literal["white", "black", "both"]
    elo: int
    elo_scale: Literal["fide", "lichess", "chesscom"]
    opp_elo: int | None
    elo_white: int | None
    elo_black: int | None
    detail_level: int
    language: Literal["it"]


class InputCfg(Strict):
    method: Literal["example", "fen", "pgn"] | None
    example_fen_file: str
    pgn_default_position: str
    max_attempts: int
    confirm: bool


class StockfishCfg(Strict):
    path: str | None
    version_pin: str | None
    hash_mb: int
    poll_s: float
    hash_max_ram_fraction: float


class Maia2Cfg(Strict):
    model_type: Literal["rapid", "blitz"]
    device: str
    version_pin: str | None
    up_delta: int


class SyzygyCfg(Strict):
    path: str | None
    max_pieces: int


class OpeningsCfg(Strict):
    index_file: str


class EnginesCfg(Strict):
    stockfish: StockfishCfg
    maia2: Maia2Cfg
    syzygy: SyzygyCfg
    openings: OpeningsCfg


class ExplorationChoiceCfg(Strict):
    profile: Literal["fast", "standard", "deep"]


class LlmViewCfg(Strict):
    multipv_lines: int
    pv_plies: int
    policy_moves: int


class OpenRouterCfg(Strict):
    base_url: str
    timeout_s: float
    cache_control_prefixes: list[str]
    extra_body: dict[str, Any]


class AnthropicCfg(Strict):
    timeout_s: float


class LlmCfg(Strict):
    provider: Literal["openrouter", "anthropic"]
    model: str
    max_tokens: int
    temperature: float
    max_retries: int
    network_attempts: int
    network_backoff_s: list[float]
    on_fail: Literal["mark", "drop"]
    critic: bool
    plan_max_moves: int
    view: LlmViewCfg
    openrouter: OpenRouterCfg
    anthropic: AnthropicCfg


class RenderCfg(Strict):
    mark_theory: str


class OutputCfg(Strict):
    dir: str
    slug_max_chars: int


class DefaultCfg(Strict):
    user: UserCfg
    input: InputCfg
    engines: EnginesCfg
    exploration: ExplorationChoiceCfg
    llm: LlmCfg
    render: RenderCfg
    output: OutputCfg


# --- exploration.yaml -------------------------------------------------------


class DminCfg(Strict):
    root: int
    nodes: int
    pvwalk: int


class MultipvCfg(Strict):
    root: int
    nodes: int
    pvwalk: int


class ProfileCfg(Strict):
    B_s: float
    dmin: DminCfg
    node_cap_factor: float
    deadline_factor: float
    multipv: MultipvCfg
    e3_levels: int
    e3_M: int
    e3_R: int
    e4_max_moves: int
    max_nodes: int


class PhaseShares(Strict):
    E0: float
    E4: float
    E1: float
    E2: float
    E3: float
    E2b: float


class ExplorationCfg(Strict):
    reference_time_s: float | None
    phase_shares: PhaseShares
    e2c_time_factor: float
    e4_min_p: float
    profiles: dict[Literal["fast", "standard", "deep"], ProfileCfg]
    milestone_max_e3_level: int


# --- thresholds.yaml --------------------------------------------------------


class Range(Strict):
    lo: int | None
    hi: int | None


class EloInput(Strict):
    min: int
    max: int


class BandParams(Strict):
    plies_max: int
    explained_min: int
    K: int
    listed_max: int
    L_max: int
    prose_words: int
    A: float
    B: float


class DetailParams(Strict):
    words: float
    plies_delta: int


class NaturalTrap(Strict):
    p_user_min: float
    loss_min: int
    loss_min_low_bands: int
    low_bands: list[str]


class HardMove(Strict):
    p_user_max: float
    loss_max: int


class Solid(Strict):
    p_user_min: float
    loss_max: int


class PracticalAlt(Strict):
    loss_gt: int
    max_loss: int
    complexity_max: int


class ImprobableError(Strict):
    p_user_max: float
    loss_min: int
    p_up_min: float


class Classification(Strict):
    natural_trap: NaturalTrap
    hard_move: HardMove
    solid: Solid
    practical_alt: PracticalAlt
    improbable_error: ImprobableError


class Selection(Strict):
    quiet_spread_cp: int
    forced_gap_cp: int
    rec_tie_points: float
    replies_min_p: float
    replies_best_sf: int
    context_spread_cp: int
    context_candidates: int
    context_min_p: float          # D-68


class TacticalCfg(Strict):
    gap_cp: int
    mate_plies: int


class ProfileThresholds(Strict):
    endgame_nonpawn_total_max: int
    endgame_no_queens_max_minors_per_side: int
    opening_fullmove_max: int
    tactical: TacticalCfg
    closed_min_blocked_pairs: int
    unresolved_capture_see_min: int


class EloRules(Strict):
    e3_mandatory_from: int
    s11_from: int


class SectionPlanThresholds(Strict):
    c3_loss_max_cp: int
    c5_pv_plies: int          # c5: plies of the PVs whose moving pieces are «involved»
    c5_pvs: int               # c5: PVs of the first candidates (or replies)


class MaiaThresholds(Strict):
    policy_min_p: float


class FeatureGeometry(Strict):
    weak_square_files: str
    weak_square_ranks: tuple[int, int]
    outpost_ranks: tuple[int, int]
    queenside_files: str
    kingside_files: str
    inactive_mobility_max: int
    bishop_open_min_moves: int
    tempo_plies: int
    tempo_threat_see_min: int
    minority_pawn_files: str
    minority_own_pawns: int
    minority_opp_pawns: int
    minority_piece_files: str
    space_min_diff: int
    pawn_chain_min: int


class ScoringLines(Strict):
    null_lines: int
    impact_min_cp: int
    impact_cap_cp: int
    mate_cp: int
    att_plies: int
    parry_share: float
    quiescence_see_min: int
    quiescence_max_plies: int


class ScoringOverride(Strict):
    p_att_min: float
    t_max: int


class ScoringTags(Strict):
    material_min: int
    center_shift_min: int
    mobility_shift_min: int
    tempo_min: int
    leaf_plies: int


class StaticCategory(Strict):
    own: dict[str, float]
    opp: dict[str, float]
    per_value: list[str]
    relative: bool = False
    center_points: float | None = None
    pawn_points: float | None = None


class ScoringComplexity(Strict):
    entropy_max_bits: float
    unique_gap_cp: int
    entropy_weight: float
    unique_weight: float


class ScoringRelevance(Strict):
    weights: dict[str, float]
    proximity_plies: int
    phase: dict[str, dict[str, float]]


class ScoringCfg(Strict):
    """§5-bis (M3). Initial hypotheses, calibrated in M5 (§0.5)."""

    categories: list[str]
    lines: ScoringLines
    theta: dict[str, float]
    decisive_cp: int
    visible_p_att_min: float
    override: ScoringOverride
    k: dict[str, float]
    w: dict[str, float]
    tags: ScoringTags
    static: dict[str, StaticCategory]
    complexity: ScoringComplexity
    relevance: ScoringRelevance
    advice: dict[str, int]


class GoldenThresholds(Strict):
    ac09_max_diff_cp: int
    ac09_top_n: int


class ThresholdsCfg(Strict):
    elo_input: EloInput
    bands: dict[str, Range]
    anchors: dict[str, Range]
    band_params: dict[str, BandParams]
    detail: dict[str, DetailParams]
    classification: Classification
    selection: Selection
    profile: ProfileThresholds
    elo_rules: EloRules
    theory_max_share: dict[str, float]
    section_plan: SectionPlanThresholds
    maia: MaiaThresholds
    features: FeatureGeometry
    golden: GoldenThresholds
    scoring: ScoringCfg


# --- smaller files ----------------------------------------------------------


class EloConversionCfg(Strict):
    fide_to_lichess: list[tuple[int, int]]
    chesscom_to_lichess: list[tuple[int, int]]


class Maia2LimitsCfg(Strict):
    elo_max_model: int
    bucket_width: int
    first_bucket_upper: int
    top_bucket_lower: int
    models: list[str]


class Loose(BaseModel):
    """Files whose structure is text-heavy (wording, tables, verify): keys are
    still checked to be strings, the content is kept as a plain dict."""

    model_config = ConfigDict(extra="allow", frozen=True)


class Config(Strict):
    default: DefaultCfg
    exploration: ExplorationCfg
    thresholds: ThresholdsCfg
    elo_conversion: EloConversionCfg
    maia2_limits: Maia2LimitsCfg
    section_titles: dict[str, dict[str, str | None]]
    section_budget: dict[str, dict[str, float]]
    tables: dict[str, Any]
    wording: dict[str, Any]
    verify: dict[str, Any]
    project_root: Path
    config_hash: str

    def resolve_path(self, value: str | None) -> Path | None:
        """Relative paths are resolved against the project folder (Appendix D)."""
        if value is None:
            return None
        p = Path(value).expanduser()
        return p if p.is_absolute() else self.project_root / p

    @property
    def profile(self) -> ProfileCfg:
        return self.exploration.profiles[self.default.exploration.profile]


# --- loading ----------------------------------------------------------------


def find_project_root(start: Path | None = None) -> Path:
    """The project folder is the one that contains ``config/default.yaml``.

    Order: ``CHESSANALYST_HOME``; the current directory and its parents; the
    source checkout this package lives in (editable install)."""
    env = os.environ.get("CHESSANALYST_HOME")
    if env:
        return Path(env).resolve()
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if (d / "config" / "default.yaml").is_file():
            return d
    pkg = Path(__file__).resolve()
    for d in pkg.parents:
        if (d / "config" / "default.yaml").is_file():
            return d
    raise ConfigError("Cartella del progetto non trovata: manca config/default.yaml")


def _check_string_keys(node: Any, where: str) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if not isinstance(k, str):
                raise ConfigError(
                    f"{where}: chiave non stringa {k!r} ({type(k).__name__}); "
                    "le chiavi numeriche vanno scritte tra virgolette"
                )
            _check_string_keys(v, f"{where}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _check_string_keys(v, f"{where}[{i}]")


def load_yaml(path: Path) -> Any:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ConfigError(f"File di configurazione mancante: {path}") from e
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML non valido in {path}: {e}") from e
    _check_string_keys(data, path.name)
    return {} if data is None else data


def deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def compute_config_hash(raw: dict[str, Any]) -> str:
    """sha1 of the canonical serialization of the files that influence exploration."""
    canon = {name: raw[name] for name in HASHED_FILES}
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def _validate_tables(th: ThresholdsCfg, where: Path) -> None:
    for name, keys in (("bands", BAND_KEYS), ("band_params", BAND_KEYS), ("anchors", ANCHOR_KEYS),
                       ("theory_max_share", ANCHOR_KEYS)):
        got = set(getattr(th, name))
        if got != set(keys):
            raise ConfigError(f"{where.name}: {name} deve avere le chiavi {list(keys)}, trovate {sorted(got)}")


def load_config(root: Path | None = None) -> Config:
    root = find_project_root() if root is None else Path(root).resolve()
    cdir = root / "config"
    raw: dict[str, Any] = {}
    for fname in CONFIG_FILES:
        raw[fname] = load_yaml(cdir / fname)
    local = cdir / "local.yaml"
    default_raw = raw["default.yaml"]
    if local.is_file():
        default_raw = deep_merge(default_raw, load_yaml(local))
    try:
        cfg = Config(
            default=DefaultCfg.model_validate(default_raw),
            exploration=ExplorationCfg.model_validate(raw["exploration.yaml"]),
            thresholds=ThresholdsCfg.model_validate(raw["thresholds.yaml"]),
            elo_conversion=EloConversionCfg.model_validate(raw["elo_conversion.yaml"]),
            maia2_limits=Maia2LimitsCfg.model_validate(raw["maia2_limits.yaml"]),
            section_titles=raw["section_titles.yaml"],
            section_budget=raw["section_budget.yaml"],
            tables=raw["tables.yaml"],
            wording=raw["wording.yaml"],
            verify=raw["verify.yaml"],
            project_root=root,
            config_hash=compute_config_hash(raw),
        )
    except ValidationError as e:
        raise ConfigError(f"Configurazione non valida in {cdir}:\n{e}") from e
    _validate_tables(cfg.thresholds, cdir / "thresholds.yaml")
    unknown_sections = set(cfg.section_titles) - set(SECTION_IDS) - {"S07_alt"}
    if unknown_sections:
        raise ConfigError(f"section_titles.yaml: sezioni sconosciute {sorted(unknown_sections)}")
    for anchor in cfg.section_budget:
        if anchor not in ANCHOR_KEYS:
            raise ConfigError(f"section_budget.yaml: ancora sconosciuta {anchor!r}")
    return cfg


def write_local_config(root: Path, updates: dict[str, Any]) -> Path:
    """Merge ``updates`` into ``config/local.yaml`` (used by setup_engines.py)."""
    path = root / "config" / "local.yaml"
    current = load_yaml(path) if path.is_file() else {}
    merged = deep_merge(current, updates)
    # validate before writing: the merged default must still load
    DefaultCfg.model_validate(deep_merge(load_yaml(root / "config" / "default.yaml"), merged))
    path.write_text(
        "# Generato da scripts/setup_engines.py: non versionato (§11.2)\n"
        + yaml.safe_dump(merged, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return path
