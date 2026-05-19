"""
Stage 3 — Feature Extraction: Feature Store

Persists and retrieves extracted feature matrices to/from disk.
Supports HDF5 (via h5py) as the primary format for large arrays,
and pickle as a fallback for metadata DataFrames.

Feature store layout (HDF5):
    text_embeddings.h5
        /embeddings        — float32 array (n_patients, 768)
        /hadm_ids          — int64 array   (n_patients,)
    lab_features.h5
        /features          — float32 array (n_patients, 50)
        /hadm_ids          — int64 array   (n_patients,)
    vitals_features.h5
        /features          — float32 array (n_patients, 32)
        /stay_ids          — int64 array   (n_patients,)

All arrays are aligned: row i corresponds to the same patient across all files.
"""

import logging
from pathlib import Path

import numpy as np
import h5py

from configs.paths import PATHS

logger = logging.getLogger(__name__)


class FeatureStore:
    """
    Saves and loads extracted feature matrices in HDF5 format.

    Parameters
    ----------
    features_dir : Path
        Directory where .h5 feature files are stored.
        Defaults to PATHS.features_dir.
    """

    def __init__(self, features_dir: Path = PATHS.features_dir) -> None:
        self.features_dir = features_dir

    # ------------------------------------------------------------------
    # Text embeddings (768-dim)
    # ------------------------------------------------------------------

    def save_text_embeddings(
        self,
        embeddings: np.ndarray,
        hadm_ids: np.ndarray,
        path: Path | None = None,
    ) -> None:
        """
        Save ClinicalBERT text embeddings to HDF5.

        Parameters
        ----------
        embeddings : np.ndarray
            Float32 array of shape (n, 768).
        hadm_ids : np.ndarray
            Int64 array of shape (n,) — hospital admission IDs.
        path : Path, optional
            Output path. Defaults to PATHS.text_features_file.
        """
        out = path or PATHS.text_features_file
        out.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(out, "w") as f:
            f.create_dataset("embeddings", data=embeddings.astype(np.float32),
                             compression="gzip")
            f.create_dataset("hadm_ids", data=hadm_ids.astype(np.int64))
        logger.info("Saved text embeddings: %s  shape=%s", out, embeddings.shape)
        print(f"[FeatureStore] Saved text embeddings -> {out}  shape={embeddings.shape}")

    def load_text_embeddings(
        self,
        path: Path | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Load text embeddings from HDF5.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (embeddings (n, 768), hadm_ids (n,))
        """
        src = path or PATHS.text_features_file
        if not src.exists():
            raise FileNotFoundError(f"Text features not found: {src}")
        with h5py.File(src, "r") as f:
            embeddings = f["embeddings"][:]
            hadm_ids = f["hadm_ids"][:]
        logger.info("Loaded text embeddings: %s  shape=%s", src, embeddings.shape)
        return embeddings, hadm_ids

    # ------------------------------------------------------------------
    # Lab features (50-dim)
    # ------------------------------------------------------------------

    def save_lab_features(
        self,
        features: np.ndarray,
        hadm_ids: np.ndarray,
        path: Path | None = None,
    ) -> None:
        """
        Save lab feature vectors to HDF5.

        Parameters
        ----------
        features : np.ndarray
            Float32 array of shape (n, 50).
        hadm_ids : np.ndarray
            Int64 array of shape (n,).
        path : Path, optional
            Defaults to PATHS.lab_features_file.
        """
        out = path or PATHS.lab_features_file
        out.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(out, "w") as f:
            f.create_dataset("features", data=features.astype(np.float32),
                             compression="gzip")
            f.create_dataset("hadm_ids", data=hadm_ids.astype(np.int64))
        logger.info("Saved lab features: %s  shape=%s", out, features.shape)
        print(f"[FeatureStore] Saved lab features    -> {out}  shape={features.shape}")

    def load_lab_features(
        self,
        path: Path | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Load lab features from HDF5.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (features (n, 50), hadm_ids (n,))
        """
        src = path or PATHS.lab_features_file
        if not src.exists():
            raise FileNotFoundError(f"Lab features not found: {src}")
        with h5py.File(src, "r") as f:
            features = f["features"][:]
            hadm_ids = f["hadm_ids"][:]
        logger.info("Loaded lab features: %s  shape=%s", src, features.shape)
        return features, hadm_ids

    # ------------------------------------------------------------------
    # Vitals features (32-dim)
    # ------------------------------------------------------------------

    def save_vitals_features(
        self,
        features: np.ndarray,
        stay_ids: np.ndarray,
        path: Path | None = None,
    ) -> None:
        """
        Save vitals feature vectors to HDF5.

        Parameters
        ----------
        features : np.ndarray
            Float32 array of shape (n, 32).
        stay_ids : np.ndarray
            Int64 array of shape (n,).
        path : Path, optional
            Defaults to PATHS.vitals_features_file.
        """
        out = path or PATHS.vitals_features_file
        out.parent.mkdir(parents=True, exist_ok=True)
        with h5py.File(out, "w") as f:
            f.create_dataset("features", data=features.astype(np.float32),
                             compression="gzip")
            f.create_dataset("stay_ids", data=stay_ids.astype(np.int64))
        logger.info("Saved vitals features: %s  shape=%s", out, features.shape)
        print(f"[FeatureStore] Saved vitals features -> {out}  shape={features.shape}")

    def load_vitals_features(
        self,
        path: Path | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Load vitals features from HDF5.

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            (features (n, 32), stay_ids (n,))
        """
        src = path or PATHS.vitals_features_file
        if not src.exists():
            raise FileNotFoundError(f"Vitals features not found: {src}")
        with h5py.File(src, "r") as f:
            features = f["features"][:]
            stay_ids = f["stay_ids"][:]
        logger.info("Loaded vitals features: %s  shape=%s", src, features.shape)
        return features, stay_ids

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def all_features_exist(self) -> bool:
        """
        Check whether all three feature files exist on disk.

        Returns
        -------
        bool
        """
        return (
            PATHS.text_features_file.exists()
            and PATHS.lab_features_file.exists()
            and PATHS.vitals_features_file.exists()
        )

    def print_summary(self) -> None:
        """Print a summary of stored feature dimensions."""
        print("\n[FeatureStore] Feature file summary:")
        files = [
            ("text_embeddings.h5", PATHS.text_features_file,
             "embeddings", "hadm_ids"),
            ("lab_features.h5",    PATHS.lab_features_file,
             "features",   "hadm_ids"),
            ("vitals_features.h5", PATHS.vitals_features_file,
             "features",   "stay_ids"),
        ]
        for name, path, feat_key, id_key in files:
            if path.exists():
                with h5py.File(path, "r") as f:
                    shape = f[feat_key].shape
                print(f"  {name:<25}  shape={shape}")
            else:
                print(f"  {name:<25}  MISSING")


if __name__ == "__main__":
    store = FeatureStore()
    print("All features exist:", store.all_features_exist())
    store.print_summary()
