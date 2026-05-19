"""
Stage 1 — Data Sources: Clinical Notes Loader

Loads clinical notes from the pre-extracted CSV:
    data/clinical_notes.csv  (24 columns)

Key columns:
    note_id     : str   — unique note identifier
    subject_id  : int   — patient identifier
    hadm_id     : int   — hospital admission identifier
    note_type   : str   — type of clinical note
    note_source : str   — source system
    charttime   : str   — datetime the note was charted
    storetime   : str   — datetime the note was stored
    text        : str   — full free-text clinical note
"""

import logging
from pathlib import Path

import pandas as pd

from configs.paths import CLINICAL_NOTES_PATH

logger = logging.getLogger(__name__)


class NotesLoader:
    """
    Loads and performs basic validation of clinical notes.

    Parameters
    ----------
    discharge_path : Path, optional
        Path to clinical_notes.csv. Defaults to CLINICAL_NOTES_PATH from configs.
    chunksize : int, optional
        Unused (kept for API compatibility). Loading is done all at once.
    """

    USECOLS = [
        "subject_id", "hadm_id", "note_id", "note_type",
        "note_seq", "charttime", "storetime", "text",
    ]
    DATETIME_COLS = ["charttime", "storetime"]

    def __init__(
        self,
        discharge_path: Path = CLINICAL_NOTES_PATH,
        chunksize: int | None = None,
    ) -> None:
        self.discharge_path = discharge_path
        self.chunksize = chunksize  # retained for API compatibility
        self._df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """
        Load clinical_notes.csv into a clean DataFrame.

        Steps
        -----
        - Load data/clinical_notes.csv
        - Drop rows where text is null or empty string
        - Drop rows where subject_id is null
        - Keep only the 8 key columns
        - Convert charttime and storetime to datetime
        - Print shape, note_source distribution, avg text length

        Returns
        -------
        pd.DataFrame
            Clean notes DataFrame with columns:
            subject_id, hadm_id, note_id, note_type, note_source,
            charttime, storetime, text.
        """
        if self._df is not None:
            logger.debug("Returning cached notes DataFrame.")
            return self._df

        logger.info("Loading clinical notes from %s ...", self.discharge_path)
        df = pd.read_csv(self.discharge_path, engine="python",
                         on_bad_lines="skip")

        # Drop rows with null or empty text
        before = len(df)
        df = df[df["text"].notna()]
        df = df[df["text"].str.strip() != ""]
        logger.info("Dropped %d rows with null/empty text.", before - len(df))

        # Drop rows with null subject_id; coerce non-numeric values
        df = df.dropna(subset=["subject_id"])
        df["subject_id"] = pd.to_numeric(df["subject_id"], errors="coerce")
        df = df.dropna(subset=["subject_id"])
        df["subject_id"] = df["subject_id"].astype(int)

        # Keep only the required columns (drop any that don't exist gracefully)
        keep = [c for c in self.USECOLS if c in df.columns]
        df = df[keep]

        # Parse datetimes
        for col in self.DATETIME_COLS:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        self._df = df.reset_index(drop=True)

        # ---- Print summary ----
        print(f"\n[NotesLoader] Shape: {df.shape}")
        if "note_type" in df.columns:
            print("  note_type distribution:")
            for ntype, cnt in df["note_type"].value_counts().items():
                print(f"    {ntype}: {cnt:,}")
        avg_len = df["text"].str.len().mean()
        print(f"  Average text length: {avg_len:,.0f} characters")

        return self._df

    def load_for_subject(self, subject_id: int) -> pd.DataFrame:
        """Return all notes for a single patient."""
        return self.load()[self.load()["subject_id"] == subject_id]

    def load_for_admission(self, hadm_id: int) -> pd.DataFrame:
        """Return all notes for a single hospital admission."""
        return self.load()[self.load()["hadm_id"] == hadm_id]

    def validate_schema(self, df: pd.DataFrame) -> None:
        """Assert expected columns and basic dtype checks."""
        missing = [c for c in self.USECOLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in notes DataFrame: {missing}")
        if not pd.api.types.is_integer_dtype(df["subject_id"]):
            raise ValueError("subject_id must be integer dtype.")

    def stream_chunks(self):
        """Yield the full DataFrame as a single chunk (compatibility stub)."""
        yield self.load()

    def load_from_input(self, note_input, subject_id: int,
                        hadm_id: int) -> pd.DataFrame:
        if note_input is None:
            return pd.DataFrame(columns=self.USECOLS)
        return pd.DataFrame([{
            "subject_id": subject_id, "hadm_id": hadm_id,
            "note_id": f"manual_{hadm_id}",
            "note_type": note_input.note_type,
            "note_seq": 1,
            "charttime": pd.to_datetime(note_input.charttime),
            "storetime": pd.to_datetime(note_input.charttime),
            "text": note_input.text,
        }])

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def n_notes(self) -> int:
        """Number of notes in the loaded DataFrame."""
        if self._df is None:
            raise RuntimeError("Call load() first.")
        return len(self._df)

    @property
    def unique_patients(self) -> int:
        """Number of unique subject_ids in the loaded notes."""
        if self._df is None:
            raise RuntimeError("Call load() first.")
        return self._df["subject_id"].nunique()


if __name__ == "__main__":
    loader = NotesLoader()
    df = loader.load()
    print(df.head())
    print(f"Loaded {loader.n_notes} notes for {loader.unique_patients} patients.")
