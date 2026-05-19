"""
Stage 3 — Feature Extraction Pipeline A: NLP (Clinical Notes)

Encodes cleaned discharge summaries using ClinicalBERT:
    Model: emilyalsentzer/Bio_ClinicalBERT (HuggingFace)
    Input: cleaned text strings (from TextCleaner)
    Process: Tokenize → encode with ClinicalBERT → extract [CLS] token embedding
    Output: 768-dimensional float32 embedding per patient admission

Bio_ClinicalBERT is a BERT-base model pretrained on a large corpus of
clinical notes from MIMIC-III. It handles medical abbreviations, drug names,
and clinical terminology better than general-domain BERT models.

The [CLS] token embedding from the final transformer layer serves as a
fixed-length semantic representation of the entire note.

For notes longer than 512 tokens (BERT's max), a sliding window or
truncation strategy is applied (see _handle_long_note()).
"""

import logging
from pathlib import Path

import numpy as np
import torch
from transformers import (
    AutoTokenizer,
    AutoModel,
    BertTokenizer,
    BertModel,
)

from configs.model_config import MODEL_CFG
from configs.paths import PATHS

logger = logging.getLogger(__name__)


class NLPPipeline:
    """
    ClinicalBERT encoding pipeline for clinical discharge summaries.

    Loads the Bio_ClinicalBERT model from HuggingFace and encodes
    text inputs in batches to produce 768-dim [CLS] embeddings.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier. Defaults to MODEL_CFG.clinicalbert_model_name.
    max_length : int
        Maximum token length. Defaults to MODEL_CFG.clinicalbert_max_length (512).
    batch_size : int
        Number of notes to encode per forward pass. Defaults to MODEL_CFG.clinicalbert_batch_size.
    device : str | None
        "cuda", "cpu", or None (auto-detect GPU). Defaults to None.
    freeze_weights : bool
        If True, model weights are not updated during training.
    long_note_strategy : str
        How to handle notes > 512 tokens:
        - "truncate"  : keep first 512 tokens
        - "mean_pool" : encode in 512-token windows, average [CLS] embeddings
    """

    def __init__(
        self,
        model_name: str = MODEL_CFG.clinicalbert_model_name,
        max_length: int = MODEL_CFG.clinicalbert_max_length,
        batch_size: int = MODEL_CFG.clinicalbert_batch_size,
        device: str | None = None,
        freeze_weights: bool = MODEL_CFG.freeze_bert,
        long_note_strategy: str = "truncate",
    ) -> None:
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.freeze_weights = freeze_weights
        self.long_note_strategy = long_note_strategy

        # Auto-select device
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.tokenizer: BertTokenizer | None = None
        self.model: BertModel | None = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_model(self) -> None:
        """
        Load the Bio_ClinicalBERT tokenizer and model from HuggingFace.

        Downloads model weights on first call (~440MB). Subsequent calls
        use the HuggingFace cache.
        """
        if self._loaded:
            return

        logger.info("Loading ClinicalBERT model: %s (device=%s) ...",
                    self.model_name, self.device)

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model = self.model.to(self.device)
        if self.freeze_weights:
            for param in self.model.parameters():
                param.requires_grad = False
        self.model.eval()
        self._loaded = True
        logger.info("ClinicalBERT loaded successfully.")

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Encode a list of cleaned clinical note texts into 768-dim embeddings.

        Processes in batches of self.batch_size.

        Parameters
        ----------
        texts : list[str]
            List of cleaned note texts (from TextCleaner).

        Returns
        -------
        np.ndarray
            Float32 array of shape (len(texts), 768).
        """
        if not self._loaded:
            self.load_model()

        from tqdm import tqdm
        all_embeddings = []
        for i in tqdm(range(0, len(texts), self.batch_size),
                      desc="ClinicalBERT encoding"):
            batch = texts[i: i + self.batch_size]
            all_embeddings.append(self._encode_batch(batch))
        return np.vstack(all_embeddings)

    def encode_single(self, text: str) -> np.ndarray:
        """
        Encode a single clinical note text.

        Returns
        -------
        np.ndarray
            Float32 array of shape (768,).
        """
        return self.encode([text])[0]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _encode_batch(self, texts: list[str]) -> np.ndarray:
        """
        Encode one batch of texts using the loaded model.

        Returns
        -------
        np.ndarray
            Float32 array of shape (len(texts), 768).
        """
        with torch.no_grad():
            encoded = self.tokenizer(
                texts,
                max_length=self.max_length,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            outputs = self.model(**encoded)
            # [CLS] token = first token of last hidden state
            cls_embeddings = outputs.last_hidden_state[:, 0, :]  # (batch, 768)
            return cls_embeddings.cpu().numpy().astype(np.float32)

    def _handle_long_note(self, text: str) -> np.ndarray:
        """
        Handle a note that exceeds self.max_length tokens.

        - "truncate"  : tokenizer handles this automatically
        - "mean_pool" : split into windows, average CLS embeddings

        Returns
        -------
        np.ndarray
            Float32 array of shape (768,).
        """
        if self.long_note_strategy == "truncate":
            return self._encode_batch([text])[0]

        # mean_pool: split into chunks and average
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        window = self.max_length - 2  # reserve [CLS] and [SEP]
        chunks = [tokens[i: i + window] for i in range(0, len(tokens), window)]
        chunk_texts = [self.tokenizer.decode(chunk) for chunk in chunks]
        embeddings = self._encode_batch(chunk_texts)
        return embeddings.mean(axis=0).astype(np.float32)


if __name__ == "__main__":
    pipeline = NLPPipeline(batch_size=8)
    pipeline.load_model()
    test_texts = [
        "Patient presented with chest pain. ECG showed ST elevation.",
        "Admitted for shortness of breath. History of COPD.",
    ]
    embeddings = pipeline.encode(test_texts)
    print(f"Embeddings shape: {embeddings.shape}")  # Expected: (2, 768)
