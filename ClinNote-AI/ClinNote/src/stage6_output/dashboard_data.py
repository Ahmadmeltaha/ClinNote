"""
Stage 6 — Clinical Output: Dashboard Data Exporter

Prepares and exports all AI pipeline outputs in formats consumable by
Ahmad Meltaha's web frontend (separate repo).

Export formats:
  - Per-patient JSON summaries (one file per admission)
  - Aggregated cohort JSON (all patients — for overview dashboard)
  - Evaluation metrics JSON (model performance)

JSON files are written to outputs/summaries/ and consumed by the web API.
"""

import json
import logging
from pathlib import Path
from datetime import datetime

from configs.paths import PATHS

logger = logging.getLogger(__name__)


class DashboardDataExporter:
    """
    Exports AI pipeline results to JSON files for the web dashboard.

    Parameters
    ----------
    output_dir : Path
        Directory where JSON files are written. Defaults to PATHS.summaries_dir.
    indent : int
        JSON indentation for human readability.
    """

    def __init__(
        self,
        output_dir: Path = PATHS.summaries_dir,
        indent: int = 2,
    ) -> None:
        self.output_dir = output_dir
        self.indent = indent

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_patient_summary(self, summary: dict) -> Path:
        """
        Write a single patient summary to a JSON file.

        Parameters
        ----------
        summary : dict
            Output of PatientSummaryBuilder.build().

        Returns
        -------
        Path
            Path to the written JSON file.

        File naming: {output_dir}/patient_{subject_id}_{hadm_id}.json
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"patient_{summary['subject_id']}_{summary['hadm_id']}.json"
        out_path = self.output_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=self.indent, default=str, ensure_ascii=False)
        logger.info("Exported patient summary: %s", out_path)
        return out_path

    def export_cohort_overview(
        self,
        summaries: list[dict],
        filename: str = "cohort_overview.json",
    ) -> Path:
        """
        Export aggregated overview of all patient summaries.

        Parameters
        ----------
        summaries : list[dict]
            List of all patient summary dicts.
        filename : str
            Output filename.

        Returns
        -------
        Path
            Path to the written JSON file.

        Overview format:
        {
            "n_patients"         : 1234,
            "n_high_risk"        : 89,
            "mean_mortality_prob": 0.12,
            "generated_at"       : "...",
            "patients"           : [list of summary dicts]
        }
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        high_risk = [s for s in summaries if s.get("predicted_mortality", {}).get("risk_level") == "HIGH"]
        probs = [s.get("predicted_mortality", {}).get("probability", 0.0) for s in summaries]
        overview = {
            "n_patients"         : len(summaries),
            "n_high_risk"        : len(high_risk),
            "mean_mortality_prob": float(sum(probs) / len(probs)) if probs else 0.0,
            "generated_at"       : datetime.utcnow().isoformat(),
            "patients"           : summaries,
        }
        out_path = self.output_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(overview, f, indent=self.indent, default=str, ensure_ascii=False)
        logger.info("Exported cohort overview: %s", out_path)
        return out_path

    def export_evaluation_metrics(
        self,
        metrics: dict,
        filename: str = "evaluation_metrics.json",
    ) -> Path:
        """
        Export model evaluation metrics to JSON.

        Parameters
        ----------
        metrics : dict
            Output of MortalityPredictor.evaluate().
        filename : str
            Output filename.

        Returns
        -------
        Path
            Path to the written JSON file.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        metrics["generated_at"] = datetime.utcnow().isoformat()
        out_path = self.output_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=self.indent, default=str)
        logger.info("Exported evaluation metrics: %s", out_path)
        return out_path

    def load_patient_summary(self, subject_id: int, hadm_id: int) -> dict:
        """
        Load a previously exported patient summary from JSON.

        Parameters
        ----------
        subject_id : int
        hadm_id : int

        Returns
        -------
        dict
            Patient summary dict.

        Raises
        ------
        FileNotFoundError
            If the summary file does not exist.
        """
        path = self.output_dir / f"patient_{subject_id}_{hadm_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"No summary found for {subject_id}/{hadm_id} at {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    # exporter = DashboardDataExporter()
    # path = exporter.export_patient_summary(summary_dict)
    # print(f"Summary saved to {path}")
    pass
