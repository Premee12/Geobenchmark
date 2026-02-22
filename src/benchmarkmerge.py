# Merge All GeoBenchmark Subsets into Final Benchmark Files
import os
import pandas as pd

BASE_DIR = "./Geodata/results"
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcqs")

DIR_TOKENS = {"north", "south", "east", "west"}
DIS_TOKENS = {"near", "far", "close", "distant"}
TOP_TOKENS = {"within", "borders"}

MCQ_FILES = {
    "atomic_mcq.csv": {"concept": 1, "relations": None},
    "dis_dir_mcq.csv": {"concept": 2, "relations": {"dir": 1, "dis": 1, "top": 0}},
    "dir_top_mcq.csv": {"concept": 2, "relations": {"dir": 1, "dis": 0, "top": 1}},
    "top_dis_mcq.csv": {"concept": 2, "relations": {"dir": 0, "dis": 1, "top": 1}},
    "3_concept_mcq.csv": {"concept": 3, "relations": {"dir": 1, "dis": 1, "top": 1}},}

YESNO_FILES = {
    "atomic_yesno.csv": {"concept": 1, "relations": None},
    "dis_dir_yesno.csv": {"concept": 2, "relations": {"dir": 1, "dis": 1, "top": 0}},
    "dir_top_yesno.csv": {"concept": 2, "relations": {"dir": 1, "dis": 0, "top": 1}},
    "top_dis_yesno.csv": {"concept": 2, "relations": {"dir": 0, "dis": 1, "top": 1}},
    "3_concept_yesno.csv": {"concept": 3, "relations": {"dir": 1, "dis": 1, "top": 1}},}

def parse_relations(rel):
    rel = str(rel).strip().lower()
    return {
        "dir": 1 if rel in DIR_TOKENS else 0,
        "dis": 1 if rel in DIS_TOKENS else 0,
        "top": 1 if rel in TOP_TOKENS else 0,}

# Merge MCQ datasets
def process_mcq():
    rows = []
    for fname, meta in MCQ_FILES.items():
        path = os.path.join(MCQ_DIR, fname)
        if not os.path.exists(path):
            print(f"[WARN] Missing MCQ file: {fname}")
            continue

        df = pd.read_csv(path)
        if "option_sources" not in df.columns:
            df["option_sources"] = "unknown"

        for _, r in df.iterrows():
            flags = parse_relations(r.get("relation", "")) if meta["relations"] is None else meta["relations"]
            rows.append({
                "question": r["question"],
                "options": r["options"],
                "answer": r["answer"],
                "option_sources": r["option_sources"],
                "concept": meta["concept"],
                "dir": flags["dir"],
                "dis": flags["dis"],
                "top": flags["top"],
            })

    df_all = pd.DataFrame(rows)
    out_path = os.path.join(MCQ_DIR, "geobenchmark_all_mcq.csv")
    df_all.to_csv(out_path, index=False)
    print(f"[INFO] Wrote merged MCQ benchmark {out_path} ({len(df_all)} rows)")

# Merge Yes/No datasets
def process_yesno():
    rows = []
    for fname, meta in YESNO_FILES.items():
        path = os.path.join(YESNO_DIR, fname)
        if not os.path.exists(path):
            print(f"[WARN] Missing Yes/No file: {fname}")
            continue

        df = pd.read_csv(path)
        for _, r in df.iterrows():
            flags = parse_relations(r.get("relation", "")) if meta["relations"] is None else meta["relations"]
            rows.append({
                "question": r["question"],
                "answer": r["answer"],
                "transition": r.get("transition", "unknown"),
                "concept": meta["concept"],
                "dir": flags["dir"],
                "dis": flags["dis"],
                "top": flags["top"],
            })

    df_all = pd.DataFrame(rows)
    out_path = os.path.join(YESNO_DIR, "geoBenchmark_all_yesno.csv")
    df_all.to_csv(out_path, index=False)
    print(f"[INFO] Wrote merged Yes/No benchmark {out_path} ({len(df_all)} rows)")

if __name__ == "__main__":
    process_mcq()
    process_yesno()