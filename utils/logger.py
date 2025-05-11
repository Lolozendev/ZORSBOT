from pathlib import Path
import logging
from loguru import logger
from sys import stdout, stderr

_event_format = "{time:DD/MM/YYYY HH:mm:ss:SS} | <lvl>{level}</> | <lvl>{message}</>"
_issue_format = "{time:DD/MM/YYYY HH:mm:ss:SS} | <lvl>{level}</> | <lvl>{message}</> | {file}:{line}"
_rotation_duration = "1 week"
_retention_duration = "1 month"
_compression_type = "gz"
_default_event_level = "TRACE"
_default_issue_level = "WARNING"


def setup_logger(log_folder_path: Path, level: str) -> None:
    logger.remove()
    add_event_console(_default_event_level)
    add_issue_console(_default_issue_level)
    add_event_log_file(_default_event_level, log_folder_path)
    add_issue_log_file(_default_issue_level, log_folder_path)
    set_colors()


def add_event_console(log_level: str) -> None:
    logger.add(
        stdout,
        format=_event_format,
        level=log_level,
        colorize=True,
        filter=lambda record: record["level"].no
        < logger.level(_default_issue_level).no,
    )


def add_issue_console(log_level: str) -> None:
    logger.add(stderr, format=_issue_format, level=log_level, colorize=True)


def add_event_log_file(log_level: str, log_folder_path: Path) -> None:
    logger.add(
        log_folder_path / "events" / "events.log",
        format=_event_format,
        rotation=_rotation_duration,
        retention=_retention_duration,
        level=log_level,
        filter=lambda record: record["level"].no
        < logger.level(_default_issue_level).no,
        compression=_compression_type,
    )


def add_issue_log_file(log_level: str, log_folder_path: Path) -> None:
    logger.add(
        log_folder_path / "issues" / "issues.log",
        format=_issue_format,
        rotation=_rotation_duration,
        retention=_retention_duration,
        level=log_level,
        compression=_compression_type,
    )


def set_colors() -> None:
    logger.level("TRACE", color="<magenta>")
    logger.level("DEBUG", color="<cyan>")
    logger.level("INFO", color="<blue>")
    logger.level("SUCCESS", color="<green>")
    logger.level("WARNING", color="<yellow>")
    logger.level("ERROR", color="<red>")
    logger.level("CRITICAL", color="<b><RED><white>")


class _InterceptHandler(logging.Handler):
    def emit(self, record):
        # Prevent infinite recursion: if this record has already been processed, skip it.
        if getattr(record, "_from_loguru", False):
            return

        # Try to get the Loguru level based on the record's level name.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Determine the call stack depth. This ensures that the log message points to the original source.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Mark the record to prevent re-processing it
        setattr(record, "_from_loguru", True)

        # Forward the message to Loguru, including exception info if present.
        logger_with_opts = logger.opt(depth=depth, exception=record.exc_info)
        try:
            # Using structured logging: the "{}" is a placeholder for the message.
            logger_with_opts.log(level, "{}", record.getMessage())
        except Exception as e:
            # Fallback: safely construct a message and log a warning if an exception occurs.
            safe_msg = getattr(record, "msg", None) or str(record)
            logger_with_opts.warning(
                "Exception logging the following native logger message: {}, {!r}",
                safe_msg,
                e,
            )


def intercept_logger(
    logger_name: str, propagate: bool = False, level: int = logging.DEBUG
) -> None:
    target_logger = logging.getLogger(logger_name)
    # Add the intercept handler without removing existing ones
    target_logger.propagate = propagate
    target_logger.addHandler(_InterceptHandler())
    # Optionally, set the logger level
    target_logger.setLevel(level)
