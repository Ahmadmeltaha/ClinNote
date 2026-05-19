"""
Stage 1 — Data Sources: Vital Signs Loader

Loads vital sign measurements from the pre-extracted CSV:
    data/vital_signs.csv  (13 columns)

Schema:
    subject_id  : int   — patient identifier
    hadm_id     : int   — hospital admission identifier
    stay_id     : int   — ICU stay identifier
    itemid      : int   — measurement type
    label       : str   — measurement name (e.g. "Heart Rate")
    category    : str   — vital sign category
    vital_source: str   — source system
    charttime   : str   — time of measurement
    storetime   : str   — time stored in system
    value       : str   — raw value (text)
    valuenum    : float — numeric value
    valueuom    : str   — unit of measure
    warning     : int   — 1 if nurse marked as unusual
"""

import logging
from pathlib import Path

import pandas as pd

from configs.paths import VITAL_SIGNS_PATH
from configs.data_config import VITAL_ITEMIDS

logger = logging.getLogger(__name__)


class VitalsLoader:
    """
    Loads vital sign measurements from the pre-extracted vital_signs.csv.

    Parameters
    ----------
    chartevents_path : Path, optional
        Path to vital_signs.csv. Defaults to VITAL_SIGNS_PATH from configs.
    d_items_path : Path, optional
        Unused (kept for API compatibility with original skeleton).
    icustays_path : Path, optional
        Unused (kept for API compatibility).
    itemids : list[int], optional
        Unused (all vitals already filtered in vital_signs.csv).
    chunksize : int, optional
        Unused (kept for API compatibility).
    """

    def __init__(
        self,
        chartevents_path: Path = VITAL_SIGNS_PATH,
        d_items_path: Path | None = None,
        icustays_path: Path | None = None,
        itemids: list[int] | None = None,
        chunksize: int = 2_000_000,
    ) -> None:
        self.chartevents_path = chartevents_path
        self.d_items_path = d_items_path
        self.icustays_path = icustays_path
        self.itemids = itemids or VITAL_ITEMIDS.as_list()
        self.chunksize = chunksize
        self._vitals_df: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self) -> pd.DataFrame:
        """
        Load vital_signs.csv into a clean DataFrame.

        Steps
        -----
        - Load data/vital_signs.csv (all 13 columns)
        - Drop rows where subject_id is null
        - Drop rows where both value AND valuenum are null
        - Convert charttime to datetime
        - Print shape, vital_source distribution, top-15 labels, unique subject count

        Returns
        -------
        pd.DataFrame
            Clean vitals DataFrame with all 13 original columns.
        """
        if self._vitals_df is not None:
            logger.debug("Returning cached vitals DataFrame.")
            return self._vitals_df

        logger.info("Loading vital signs from %s ...", self.chartevents_path)
        df = pd.read_csv(self.chartevents_path)

        # Drop rows with null subject_id
        before = len(df)
        df = df.dropna(subset=["subject_id"])
        logger.info("Dropped %d rows with null subject_id.", before - len(df))

        # Drop rows where both value and valuenum are null
        before = len(df)
        both_null = df["value"].isna() & df["valuenum"].isna()
        df = df[~both_null]
        logger.info("Dropped %d rows where both value and valuenum are null.", before - len(df))

        df["subject_id"] = df["subject_id"].astype(int)

        # Parse charttime
        df["charttime"] = pd.to_datetime(df["charttime"], errors="coerce")

        self._vitals_df = df.reset_index(drop=True)

        # ---- Print summary ----
        print(f"\n[VitalsLoader] Shape: {df.shape}")
        if "vital_source" in df.columns:
            print("  vital_source distribution:")
            for src, cnt in df["vital_source"].value_counts().items():
                print(f"    {src}: {cnt:,}")
        if "label" in df.columns:
            print("  Top 15 most frequent labels:")
            top15 = df["label"].value_counts().head(15)
            for lbl, cnt in top15.items():
                print(f"    {lbl}: {cnt:,}")
        print(f"  Unique subject_ids: {df['subject_id'].nunique():,}")

        return self._vitals_df

    # Legacy alias so existing skeleton code calling load_vitals() still works
    def load_vitals(self) -> pd.DataFrame:
        return self.load()

    def load_icustays(self) -> pd.DataFrame:
        """Stub — ICU stay info is embedded in vital_signs.csv via stay_id."""
        raise NotImplementedError(
            "Separate icustays table not used; stay_id is already in vital_signs.csv."
        )

    def load_d_items(self) -> pd.DataFrame:
        """Stub — item labels are already in vital_signs.csv."""
        raise NotImplementedError(
            "d_items not needed; label/category are already in vital_signs.csv."
        )

    def get_vitals_for_stay(self, stay_id: int) -> pd.DataFrame:
        """Return all vital measurements for a single ICU stay, sorted by charttime."""
        df = self.load()
        return df[df["stay_id"] == stay_id].sort_values("charttime")

    def get_vitals_for_stay_window(self, stay_id: int, hours: int = 48) -> pd.DataFrame:
        """Return vital signs from the first `hours` of a stay."""
        vitals = self.get_vitals_for_stay(stay_id)
        if vitals.empty:
            return vitals
        intime = vitals["charttime"].min()
        cutoff = intime + pd.Timedelta(hours=hours)
        return vitals[vitals["charttime"] <= cutoff]

    def pivot_vitals(self, vitals_df: pd.DataFrame) -> pd.DataFrame:
        """Pivot vital measurements from long to wide format."""
        label_map = VITAL_ITEMIDS.label_map()
        vitals_df = vitals_df.copy()
        vitals_df["vital_name"] = vitals_df["itemid"].map(label_map)
        return vitals_df.pivot_table(
            index=["stay_id", "charttime"],
            columns="vital_name",
            values="valuenum",
            aggfunc="mean",
        ).reset_index()

    def load_from_input(self, vitals_input: list, subject_id: int,
                        hadm_id: int) -> pd.DataFrame:
        if not vitals_input:
            return pd.DataFrame()
        stay_id = abs(hash(str(subject_id))) % 1_000_000
        rows = [{
            "subject_id": subject_id, "hadm_id": hadm_id,
            "stay_id": stay_id, "itemid": 0,
            "label": v.label, "category": "Vitals",
            "vital_source": "manual_entry",
            "charttime": pd.to_datetime(v.charttime),
            "storetime": pd.to_datetime(v.charttime),
            "value": str(v.valuenum), "valuenum": v.valuenum,
            "valueuom": v.valueuom, "warning": 0,
        } for v in vitals_input]
        return pd.DataFrame(rows)


if __name__ == "__main__":
    loader = VitalsLoader()
    df = loader.load()
    print(df.head())
    print(f"Loaded {len(df)} vital measurements for {df['subject_id'].nunique()} patients.")
