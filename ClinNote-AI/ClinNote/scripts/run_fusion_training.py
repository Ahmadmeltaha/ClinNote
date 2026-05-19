"""
Script: Train the Disentangled Fusion Model (Stage 4)

Trains the DisentangledTransformer on the extracted features:
  - Loads features from FeatureStore (text_embeddings.h5, lab_features.h5, vitals_features.h5)
  - Creates train/val/test splits
  - Trains with two optimizers: main model + CLUB variational network
  - Logs metrics to TensorBoard
  - Saves best checkpoint by val AUROC

Usage:
    python scripts/run_fusion_training.py [--epochs N] [--batch-size N] [--lr LR] [--debug]
"""

import argparse
import logging
import pickle
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.utils.logger import setup_logger
from src.utils.helpers import set_seed
from src.utils.metrics import compute_classification_metrics
from src.stage3_feature_extraction.feature_store import FeatureStore
from src.stage4_fusion.disentangled_transformer import DisentangledTransformer
from configs.model_config import MODEL_CFG
from configs.pipeline_config import PIPELINE_CFG
from configs.paths import PATHS

logger = setup_logger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ClinNote Fusion Model Training")
    parser.add_argument("--epochs", type=int, default=MODEL_CFG.num_epochs)
    parser.add_argument("--batch-size", type=int, default=MODEL_CFG.batch_size)
    parser.add_argument("--lr", type=float, default=MODEL_CFG.learning_rate)
    parser.add_argument("--debug", action="store_true", help="2 epochs only")
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    set_seed(MODEL_CFG.random_seed)
    n_epochs = 2 if args.debug else args.epochs

    logger.info("Training DisentangledTransformer for %d epochs", n_epochs)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    # ------------------------------------------------------------------
    # 1. Load features
    # ------------------------------------------------------------------
    store = FeatureStore()
    if not store.all_features_exist():
        logger.error("Feature files missing — run scripts/run_feature_extraction.py first.")
        sys.exit(1)

    text_feats,   hadm_ids_text   = store.load_text_embeddings()
    lab_feats,    hadm_ids_labs   = store.load_lab_features()
    vitals_feats, stay_ids_vitals = store.load_vitals_features()
    logger.info(
        "Features loaded: text=%s  labs=%s  vitals=%s",
        text_feats.shape, lab_feats.shape, vitals_feats.shape,
    )

    # ------------------------------------------------------------------
    # 2. Load labels from cohort (hospital_expire_flag)
    # ------------------------------------------------------------------
    cohort_path = PATHS.cohort_file
    if not cohort_path.exists():
        logger.error("Cohort file not found: %s", cohort_path)
        sys.exit(1)

    with open(cohort_path, "rb") as f:
        cohort = pickle.load(f)

    # Build hadm_id → label mapping
    label_map = dict(zip(cohort["hadm_id"].values, cohort["hospital_expire_flag"].values))
    labels = np.array([label_map.get(hid, 0) for hid in hadm_ids_text], dtype=np.float32)
    logger.info(
        "Labels: n=%d  positives=%d  (%.1f%%)",
        len(labels), labels.sum(), 100 * labels.mean(),
    )

    # ------------------------------------------------------------------
    # 3. Train / val / test split (stratified, 70/15/15)
    # ------------------------------------------------------------------
    n = len(labels)
    idx = np.arange(n)

    # Use simple split when sample size is very small (< 30)
    strat = labels if labels.sum() >= 2 and (labels == 0).sum() >= 2 else None
    idx_train, idx_tmp = train_test_split(idx, test_size=0.30, random_state=MODEL_CFG.random_seed, stratify=strat)
    strat_tmp = labels[idx_tmp] if strat is not None else None
    idx_val, idx_test = train_test_split(idx_tmp, test_size=0.50, random_state=MODEL_CFG.random_seed, stratify=strat_tmp)

    def make_loader(indices: np.ndarray, shuffle: bool) -> DataLoader:
        ds = TensorDataset(
            torch.tensor(text_feats[indices],   dtype=torch.float32),
            torch.tensor(lab_feats[indices],    dtype=torch.float32),
            torch.tensor(vitals_feats[indices], dtype=torch.float32),
            torch.tensor(labels[indices],       dtype=torch.float32).unsqueeze(1),
        )
        return DataLoader(ds, batch_size=args.batch_size, shuffle=shuffle)

    train_loader = make_loader(idx_train, shuffle=True)
    val_loader   = make_loader(idx_val,   shuffle=False)
    test_loader  = make_loader(idx_test,  shuffle=False)
    logger.info("Split: train=%d  val=%d  test=%d", len(idx_train), len(idx_val), len(idx_test))

    # ------------------------------------------------------------------
    # 4. Model + two optimizers
    # ------------------------------------------------------------------
    model = DisentangledTransformer().to(device)
    logger.info("Model parameters: %d", model.n_parameters)

    optimizer_main = AdamW(
        model.parameters(), lr=args.lr, weight_decay=MODEL_CFG.weight_decay
    )
    club_params = (
        list(model.fusion.mi_text_common.parameters())
        + list(model.fusion.mi_lab_common.parameters())
        + list(model.fusion.mi_vitals_common.parameters())
    )
    optimizer_club = AdamW(club_params, lr=args.lr * 10)
    scheduler = CosineAnnealingLR(optimizer_main, T_max=n_epochs)

    # ------------------------------------------------------------------
    # 5. TensorBoard writer (optional — skip gracefully if unavailable)
    # ------------------------------------------------------------------
    try:
        from torch.utils.tensorboard import SummaryWriter
        PATHS.ensure_output_dirs()
        writer = SummaryWriter(log_dir=str(PATHS.logs_dir / "tensorboard"))
    except ImportError:
        writer = None
        logger.warning("TensorBoard not available — skipping logging.")

    # ------------------------------------------------------------------
    # 6. Training loop
    # ------------------------------------------------------------------
    PATHS.ensure_output_dirs()
    best_auroc = 0.0
    patience_counter = 0

    for epoch in range(1, n_epochs + 1):
        # --- Train ---
        model.train()
        train_total_loss = 0.0
        for text_b, lab_b, vitals_b, labels_b in train_loader:
            text_b   = text_b.to(device)
            lab_b    = lab_b.to(device)
            vitals_b = vitals_b.to(device)
            labels_b = labels_b.to(device)

            # Step A: update CLUB variational network
            optimizer_club.zero_grad()
            with torch.no_grad():
                text_p, lab_p, vitals_p = model.fusion.projections(text_b, lab_b, vitals_b)
                s_text   = model.fusion.text_self_attn(text_p)
                s_lab    = model.fusion.lab_self_attn(lab_p)
                s_vitals = model.fusion.vitals_self_attn(vitals_p)
                s_common = model.fusion.cross_attn(s_text, s_lab, s_vitals)
            club_loss = (
                model.fusion.mi_text_common.learning_loss(s_text, s_common)
                + model.fusion.mi_lab_common.learning_loss(s_lab, s_common)
                + model.fusion.mi_vitals_common.learning_loss(s_vitals, s_common)
            )
            club_loss.backward()
            optimizer_club.step()

            # Step B: update main model
            optimizer_main.zero_grad()
            output = model(text_b, lab_b, vitals_b, labels_b)
            output["total_loss"].backward()
            nn.utils.clip_grad_norm_(model.parameters(), MODEL_CFG.gradient_clip_norm)
            optimizer_main.step()

            train_total_loss += output["total_loss"].item()

        scheduler.step()
        avg_train_loss = train_total_loss / len(train_loader)

        # --- Validate ---
        model.eval()
        val_probs, val_labels = [], []
        with torch.no_grad():
            for text_b, lab_b, vitals_b, labels_b in val_loader:
                out = model(text_b.to(device), lab_b.to(device), vitals_b.to(device))
                val_probs.append(out["mortality_prob"].cpu().numpy())
                val_labels.append(labels_b.numpy())

        val_probs  = np.concatenate(val_probs).squeeze()
        val_labels = np.concatenate(val_labels).squeeze()
        val_preds  = (val_probs >= 0.5).astype(int)

        try:
            metrics = compute_classification_metrics(val_labels, val_preds, val_probs)
            val_auroc = metrics.get("auroc", 0.0)
        except Exception:
            val_auroc = 0.0

        logger.info(
            "Epoch %3d/%d  train_loss=%.4f  val_auroc=%.4f",
            epoch, n_epochs, avg_train_loss, val_auroc,
        )

        if writer:
            writer.add_scalar("Loss/train", avg_train_loss, epoch)
            writer.add_scalar("AUROC/val",  val_auroc,       epoch)

        # --- Save best checkpoint (always save epoch 1 as baseline) ---
        if val_auroc > best_auroc or epoch == 1:
            best_auroc = val_auroc
            patience_counter = 0
            PATHS.models_dir.mkdir(parents=True, exist_ok=True)
            torch.save(
                {"epoch": epoch, "model_state_dict": model.state_dict(), "val_auroc": val_auroc},
                PATHS.fusion_model_checkpoint,
            )
            logger.info("  Saved checkpoint (auroc=%.4f)", best_auroc)
        else:
            patience_counter += 1
            if patience_counter >= MODEL_CFG.early_stopping_patience:
                logger.info("Early stopping at epoch %d (patience=%d)", epoch, MODEL_CFG.early_stopping_patience)
                break

    # ------------------------------------------------------------------
    # 7. Test evaluation on best checkpoint
    # ------------------------------------------------------------------
    if not PATHS.fusion_model_checkpoint.exists():
        logger.warning("No checkpoint found — skipping test evaluation.")
        return

    checkpoint = torch.load(PATHS.fusion_model_checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    test_probs, test_labels = [], []
    with torch.no_grad():
        for text_b, lab_b, vitals_b, labels_b in test_loader:
            out = model(text_b.to(device), lab_b.to(device), vitals_b.to(device))
            test_probs.append(out["mortality_prob"].cpu().numpy())
            test_labels.append(labels_b.numpy())

    test_probs  = np.concatenate(test_probs).squeeze()
    test_labels = np.concatenate(test_labels).squeeze()
    test_preds  = (test_probs >= 0.5).astype(int)

    try:
        test_metrics = compute_classification_metrics(test_labels, test_preds, test_probs)
        logger.info("Test results: %s", test_metrics)
        print("\n=== Test Evaluation ===")
        for k, v in test_metrics.items():
            print(f"  {k:<20} {v:.4f}")
    except Exception as e:
        logger.warning("Could not compute test metrics: %s", e)

    if writer:
        writer.close()

    logger.info("Training complete. Best val AUROC: %.4f", best_auroc)


if __name__ == "__main__":
    run(parse_args())
