"""
Stage 1 — Data Sources: Laboratory Results Loader

Loads laboratory events from the pre-extracted CSV:
    data/labs_final.csv  (42 columns)

Key columns after rename:
    subject_id      : int   — patient identifier
    hadm_id         : int   — hospital admission
    itemid          : int   — lab test identifier
    label           : str   — human-readable test name
    charttime       : str   — time specimen was charted  (renamed from charttime_x)
    storetime       : str   — time result was stored     (renamed from storetime_x)
    value           : str   — raw result value
    valuenum        : float — numeric result value
    valueuom        : str   — unit of measure
    ref_range_lower : float — reference range lower bound
    ref_range_upper : float — reference range upper bound
    flag            : str   — "abnormal" | "delta" | null
    priority        : str   — "ROUTINE" | "STAT"
    fluid           : str   — specimen fluid
    category        : str   — lab category
"""

import logging
from pathlib import Path

import pandas as pd

from configs.paths import LABS_PATH
from configs.data_config import LAB_ITEMIDS, LABS_CHARTTIME_COL, LABS_STORETIME_COL

logger = logging.getLogger(__name__)


class LabsLoader:
    """
    Loads MIMIC-IV laboratory events from the pre-extracted labs_final.csv.

    Parameters
    ----------
    labevents_path : Path, optional
        Path to labs_final.csv. Defaults to LABS_PATH from configs.
    d_labitems_path : Path, optional
        Unused (kept for API compatibility with original skeleton).
    itemids : list[int], optional
        Unused (all labs are already in labs_final.csv).
    chunksize : int, optional
        Unused (kept for API compatibility).
    """

    KEEP_COLS = [
        "subject_id", "hadm_id", "itemid", "label",
        "charttime", "storetime",
        "value", "valuenum", "valueuom",
        "ref_range_lower", "ref_range_upper",
        "flag", "priority", "fluid", "category",
    ]

    def __init__(
        self,
        labevents_path: Path = LABS_PATH,
        d_labitems_path: Path | None = None,
        itemids: list[int] | None = None,
        chunksize: int | None = None,
    ) -> None:
        self.labevents_path = labevents_path
        self.d_labitems_path = d_labitems_path  # unused, for API compat
        self.itemids = itemids or LAB_ITEMIDS.as_list()
        self.chunksize = chunksize
        self._labevents_df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """
        Load labs_final.csv into a clean DataFrame.

        Steps
        -----
        - Load data/labs_final.csv
        - Rename charttime_x → charttime, storetime_x → storetime
        - Drop rows where subject_id is null
        - Drop rows where valuenum is null
        - Keep only the 15 key columns
        - Convert charttime to datetime
        - Print shape, unique itemid/label counts, flag distribution

        Returns
        -------
        pd.DataFrame
            Clean labs DataFrame.
        """
        if self._labevents_df is not None:
            logger.debug("Returning cached labs DataFrame.")
            return self._labevents_df

        logger.info("Loading labs from %s ...", self.labevents_path)
        df = pd.read_csv(self.labevents_path, low_memory=False)

        # Rename duplicate-suffixed columns
        rename_map = {}
        if LABS_CHARTTIME_COL in df.columns:
            rename_map[LABS_CHARTTIME_COL] = "charttime"
        if LABS_STORETIME_COL in df.columns:
            rename_map[LABS_STORETIME_COL] = "storetime"
        if rename_map:
            df = df.rename(columns=rename_map)

        # Drop nulls on key columns
        before = len(df)
        df = df.dropna(subset=["subject_id"])
        df = df.dropna(subset=["valuenum"])
        logger.info("Dropped %d rows with null subject_id or valuenum.", before - len(df))

        df["subject_id"] = df["subject_id"].astype(int)

        # Keep only the required columns (gracefully skip missing ones)
        keep = [c for c in self.KEEP_COLS if c in df.columns]
        df = df[keep]

        # Parse charttime
        df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")

        self._labevents_df = df.reset_index(drop=True)

        # ---- Print summary ----
        print(f"\n[LabsLoader] Shape: {df.shape}")
        print(f"  Unique itemids: {df['itemid'].nunique():,}")
        if "label" in df.columns:
            print(f"  Unique labels:  {df['label'].nunique():,}")
        if "flag" in df.columns:
            print("  Flag distribution:")
            flag_counts = df["flag"].fillna("(normal/null)").value_counts()
            for flag, cnt in flag_counts.items():
                print(f"    {flag}: {cnt:,}")

        return self._labevents_df

    # Legacy alias so existing skeleton code calling load_labevents() still works
    def load_labevents(self) -> pd.DataFrame:
        return self.load()

    def load_d_labitems(self) -> pd.DataFrame:
        """Stub — label info is already in labs_final.csv."""
        raise NotImplementedError(
            "d_labitems is not needed; label/fluid/category are already in labs_final.csv."
        )

    def merge_with_labels(self, labevents_df: pd.DataFrame) -> pd.DataFrame:
        """No-op — labels are already merged in labs_final.csv."""
        return labevents_df

    def get_labs_for_admission(self, hadm_id: int) -> pd.DataFrame:
        """Return all lab events for a single hospital admission, sorted by charttime."""
        df = self.load()
        return df[df["hadm_id"] == hadm_id].sort_values("charttime")

    def get_latest_values_per_lab(self, hadm_id: int) -> pd.DataFrame:
        """Return most recent value per itemid within an admission."""
        df = self.get_labs_for_admission(hadm_id)
        return df.sort_values("charttime").groupby("itemid").last().reset_index()

    def validate_schema(self, df: pd.DataFrame) -> None:
        """Assert expected columns are present."""
        missing = [c for c in self.KEEP_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in labs DataFrame: {missing}")

    def load_from_input(self, labs_input: list, subject_id: int,
                        hadm_id: int) -> pd.DataFrame:
        if not labs_input:
            return pd.DataFrame(columns=self.KEEP_COLS)
        rows = [{
            "subject_id": subject_id, "hadm_id": hadm_id,
            "itemid": l.itemid or 0, "label": l.label,
            "charttime": pd.to_datetime(l.charttime),
            "storetime": pd.to_datetime(l.charttime),
            "value": str(l.valuenum), "valuenum": l.valuenum,
            "valueuom": l.valueuom,
            "ref_range_lower": l.ref_range_lower,
            "ref_range_upper": l.ref_range_upper,
            "flag": None, "priority": "STAT",
            "fluid": "Blood", "category": "Chemistry",
        } for l in labs_input]
        return pd.DataFrame(rows)


if __name__ == "__main__":
    loader = LabsLoader()
    df = loader.load()
    print(df.head())
    print(f"Loaded {len(df)} lab events across {df['subject_id'].nunique()} patients.")
