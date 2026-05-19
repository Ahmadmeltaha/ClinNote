"""
Stage 2 - Preprocessing: Clinical Text Cleaner

Cleans free-text clinical notes from MIMIC-IV before they are
passed to the ClinicalBERT encoder (Stage 3 NLP Pipeline).

Cleaning steps:
  1. Replace MIMIC de-identification placeholders (___) with [REDACTED]
  2. Remove section divider lines (--- or === lines)
  3. Normalize excessive whitespace (multiple spaces, tabs, newlines)
  4. Optionally truncate notes to a maximum character length
  5. Strip leading/trailing whitespace

MIMIC-IV-Note uses triple underscore (___) as a PHI placeholder for
de-identified names, dates, institutions, etc.
"""

import re
import logging
from typing import Callable

import pandas as pd

from configs.data_config import DATA_CFG

logger = logging.getLogger(__name__)


class TextCleaner:
    """
    Cleans clinical note text for NLP processing.

    Designed to process the `text` column of the clinical notes DataFrame
    produced by NotesLoader.

    Parameters
    ----------
    phi_replacement : str
        String to substitute for MIMIC PHI placeholders (___).
        Defaults to "[REDACTED]".
    max_length : int | None
        Maximum character length after cleaning. Notes longer than this
        are truncated at the nearest sentence boundary. None = no limit.
    lowercase : bool
        Whether to lowercase the text. False by default - ClinicalBERT
        was pretrained on mixed case clinical text.
    custom_cleaners : list[Callable[[str], str]]
        Optional list of additional cleaning functions applied in order.
    """

    # MIMIC de-identification placeholder pattern
    PHI_PATTERN = re.compile(r"_{2,}")

    # Excessive whitespace (multiple spaces, tabs, newlines -> single space)
    WHITESPACE_PATTERN = re.compile(r"\s+")

    # Lines that are just dashes or equals (section dividers common in MIMIC notes)
    DIVIDER_PATTERN = re.compile(r"^[-=_*]{3,}\s*$", re.MULTILINE)

    def __init__(
        self,
        phi_replacement: str = "[REDACTED]",
        max_length: int | None = DATA_CFG.max_note_length_chars,
        lowercase: bool = False,
        custom_cleaners: list[Callable[[str], str]] | None = None,
    ) -> None:
        self.phi_replacement = phi_replacement
        self.max_length = max_length
        self.lowercase = lowercase
        self.custom_cleaners = custom_cleaners or []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clean(self, text: str) -> str:
        """
        Apply the full cleaning pipeline to a single note string.

        Parameters
        ----------
        text : str
            Raw clinical note text from the `text` column.

        Returns
        -------
        str
            Cleaned text ready for tokenization.
        """
        if not isinstance(text, str) or not text.strip():
            return ""

        text = self._replace_phi(text)
        text = self._remove_dividers(text)
        text = self._normalize_whitespace(text)

        if self.lowercase:
            text = text.lower()

        for fn in self.custom_cleaners:
            text = fn(text)

        if self.max_length:
            text = self._truncate(text, self.max_length)

        return text.strip()

    def clean_series(self, text_series: pd.Series) -> pd.Series:
        """
        Apply the cleaning pipeline to an entire pandas Series of note texts.

        Parameters
        ----------
        text_series : pd.Series
            Series of raw note strings (the `text` column of the notes DataFrame).

        Returns
        -------
        pd.Series
            Cleaned text Series, same index as input.
        """
        return text_series.fillna("").apply(self.clean)

    def clean_dataframe(self, df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
        """
        Apply the full cleaning pipeline to a notes DataFrame.

        This is the primary entry point for Stage 2 preprocessing.

        Parameters
        ----------
        df : pd.DataFrame
            Notes DataFrame with a `text` column (from NotesLoader).
        text_col : str
            Name of the column containing note text. Defaults to "text".

        Returns
        -------
        pd.DataFrame
            DataFrame with cleaned text and a `text_cleaned` column added.
            Empty-text rows are dropped.
        """
        df = df.copy()

        rows_before = len(df)
        print(f"\n[TextCleaner] Rows before cleaning: {rows_before:,}")

        df["text_cleaned"] = self.clean_series(df[text_col])
        df[text_col] = df["text_cleaned"]

        # Drop rows that became empty after cleaning
        df = df[df["text_cleaned"].str.len() > 0].reset_index(drop=True)

        rows_after = len(df)
        avg_len = df["text_cleaned"].str.len().mean()

        print(f"[TextCleaner] Rows after cleaning:  {rows_after:,}")
        print(f"[TextCleaner] Dropped (empty after clean): {rows_before - rows_after:,}")
        print(f"[TextCleaner] Avg text length after: {avg_len:,.0f} characters")

        logger.info("Cleaned %d notes.", rows_after)
        return df

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _replace_phi(self, text: str) -> str:
        """Replace PHI placeholders (___) with self.phi_replacement."""
        return self.PHI_PATTERN.sub(self.phi_replacement, text)

    def _remove_dividers(self, text: str) -> str:
        """Remove section divider lines (--- or === lines)."""
        return self.DIVIDER_PATTERN.sub("", text)

    def _normalize_whitespace(self, text: str) -> str:
        """Collapse multiple whitespace characters into a single space."""
        return self.WHITESPACE_PATTERN.sub(" ", text)

    def _truncate(self, text: str, max_length: int) -> str:
        """
        Truncate text to at most max_length characters, breaking at a
        sentence boundary if possible.

        Parameters
        ----------
        text : str
            Input text (post-cleaning).
        max_length : int
            Maximum number of characters to keep.

        Returns
        -------
        str
            Truncated text.
        """
        if len(text) <= max_length:
            return text
        truncated = text[:max_length]
        # Try to cut at the last period before the limit
        last_period = truncated.rfind(".")
        if last_period > max_length * 0.8:
            return truncated[:last_period + 1]
        return truncated


if __name__ == "__main__":
    cleaner = TextCleaner()
    sample = "Patient ___ was admitted on ___ with complaints of chest pain.\n\n---\n\nLabs show elevated troponin."
    print(cleaner.clean(sample))
