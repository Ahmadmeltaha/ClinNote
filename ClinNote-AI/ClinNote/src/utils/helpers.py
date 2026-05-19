"""
Shared Utilities: General Helper Functions

Miscellaneous helpers used across multiple pipeline stages.
"""

import time
import random
import logging
from contextlib import contextmanager
from typing import Any

import numpy as np
import torch

logger = logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """
    Set random seed for Python, NumPy, and PyTorch for reproducibility.

    Parameters
    ----------
    seed : int
        Random seed value. Defaults to MODEL_CFG.random_seed (42).
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    logger.info("Random seed set to %d", seed)


@contextmanager
def timer(name: str = ""):
    """
    Context manager that logs the elapsed time for a code block.

    Usage:
        with timer("Stage 1 loading"):
            df = loader.load()

    Parameters
    ----------
    name : str
        Label for the timed block (appears in log output).
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("[%s] elapsed: %.2f seconds", name, elapsed)
        print(f"  [{name}] elapsed: {elapsed:.2f}s")


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """
    Flatten a nested dict to a single-level dict with dotted keys.

    Example:
        {"a": {"b": 1, "c": 2}} → {"a.b": 1, "a.c": 2}

    Parameters
    ----------
    d : dict
        Nested dictionary.
    parent_key : str
        Prefix for keys (used in recursion).
    sep : str
        Separator character.

    Returns
    -------
    dict
        Flattened dictionary.
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunked(lst: list, chunk_size: int):
    """
    Yield successive chunks from a list.

    Parameters
    ----------
    lst : list
        Input list to split.
    chunk_size : int
        Size of each chunk.

    Yields
    ------
    list
        Sublist of up to chunk_size elements.
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i: i + chunk_size]


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Divide two numbers, returning `default` if denominator is zero.

    Parameters
    ----------
    numerator : float
    denominator : float
    default : float
        Value returned when denominator == 0.

    Returns
    -------
    float
    """
    return numerator / denominator if denominator != 0 else default


def format_elapsed(seconds: float) -> str:
    """
    Format elapsed seconds as a human-readable string.

    Examples:
        45.2 → "45.2s"
        125.0 → "2m 5s"
        3700.0 → "1h 1m 40s"
    """
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


if __name__ == "__main__":
    print("--- set_seed ---")
    set_seed(42)
    print("  set_seed(42): OK")

    print("\n--- timer ---")
    with timer("test block"):
        import time; time.sleep(0.1)

    print("\n--- flatten_dict ---")
    nested = {"a": {"b": 1, "c": 2}, "d": 3}
    flat = flatten_dict(nested)
    print(f"  {nested} -> {flat}")

    print("\n--- chunked ---")
    chunks = list(chunked([1,2,3,4,5], 2))
    print(f"  [1..5] in chunks of 2 -> {chunks}")

    print("\n--- safe_divide ---")
    print(f"  10/2 = {safe_divide(10, 2)}")
    print(f"  10/0 = {safe_divide(10, 0)}")

    print("\n--- format_elapsed ---")
    for s in [45, 125, 3700]:
        print(f"  {s}s -> {format_elapsed(s)}")

    print("\nAll helpers: OK")
