"""Application errors. Messages are in Italian (user-visible)."""

from chessanalyst import exit_codes


class AnalystError(Exception):
    exit_code = exit_codes.BUG


class ConfigError(AnalystError):
    exit_code = exit_codes.ENVIRONMENT


class EnvironmentProblem(AnalystError):
    """Engine or weights missing, folder not writable, ... (exit code 4)."""

    exit_code = exit_codes.ENVIRONMENT


class UsageError(AnalystError):
    exit_code = exit_codes.USAGE
