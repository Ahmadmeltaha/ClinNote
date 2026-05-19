"""
Run the full pipeline on all 500 new synthetic patients.
Saves a summary JSON for each patient to outputs/summaries/.
Prints progress every 10 patients.
"""
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from api.pipeline_runner import run_for_patient

new = pd.read_csv("data/new data/patients.csv", on_bad_lines="skip", engine="python")
subject_ids = new["subject_id"].tolist()

print(f"Processing {len(subject_ids)} patients...")
ok, failed = 0, []

for i, sid in enumerate(subject_ids, 1):
    try:
        run_for_patient(str(sid))
        ok += 1
        if i % 10 == 0 or i == 1:
            print(f"  [{i}/{len(subject_ids)}] done={ok} failed={len(failed)}")
    except Exception as e:
        failed.append((sid, str(e)))
        if i <= 5 or len(failed) <= 3:
            traceback.print_exc()
        print(f"  [{i}/{len(subject_ids)}] FAILED sid={sid}: {e}")

print()
print(f"FINISHED: {ok} succeeded, {len(failed)} failed")
if failed:
    print("Failed subject_ids:", [s for s, _ in failed[:10]])
