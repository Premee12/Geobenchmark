# Generate Three-Concept (Direction + Topology + Distance) Benchmark Data
import os, random, pandas as pd
from collections import defaultdict
random.seed(42)

BASE_DIR = os.path.join("..", "geodata", "results")
REL_DIR = os.path.join("..", "geodata", "relations")
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcq")
os.makedirs(YESNO_DIR, exist_ok=True)
os.makedirs(MCQ_DIR, exist_ok=True)

# Tokens and opposites
DIR_TOKENS = ["north", "east", "south", "west"]
TOP_TOKENS = ["within", "borders"]
DIS_TOKENS = ["near", "close", "distant", "far"]
DIR_OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}
DIS_OPPOSITES = {"near": "far", "far": "near", "close": "distant", "distant": "close"}
TOP_OPPOSITES = {"within": "borders", "borders": "within"}

TEMPLATES_3 = {
    "within": [
        "Which city is within {y} and also {dis} to {z} and {dir} of {w}?",
        "Is {x} within {y} and {dis} to {z} and {dir} of {w}?"
    ],
    "borders": [
        "Which city borders {y} and is also {dis} to {z} and {dir} of {w}?",
        "Does {x} border {y} and {dis} to {z} and {dir} of {w}?"
    ]
}

# Load input data
def load_csv(name, valid_tokens):
    df = pd.read_csv(os.path.join(REL_DIR, name))
    return df[df["relation"].isin(valid_tokens)]

def get_random_distractor(correct, all_places):
    return random.choice([p for p in all_places if p != correct])

# Generate 3-concept samples
def generate_three_concept(dir_df, top_df, dis_df, all_places, target_per_combo=22):
    yesno_rows, mcq_rows, used_place1 = [], [], set()
    dir_idx, top_idx, dis_idx = defaultdict(list), defaultdict(list), defaultdict(list)

    for _, r in dir_df.iterrows():
        dir_idx[(r["place1"], r["relation"])].append(r["place2"])
    for _, r in top_df.iterrows():
        top_idx[(r["place1"], r["relation"])].append(r["place2"])
    for _, r in dis_df.iterrows():
        dis_idx[(r["place1"], r["relation"])].append(r["place2"])

    combo_map = defaultdict(list)
    for x in set(dir_df["place1"]) & set(top_df["place1"]) & set(dis_df["place1"]):
        for d in DIR_TOKENS:
            for t in TOP_TOKENS:
                for dis in DIS_TOKENS:
                    if (x, d) in dir_idx and (x, t) in top_idx and (x, dis) in dis_idx:
                        combo_map[(d, t, dis)].append(x)

    for (dir_tok, top_tok, dis_tok), candidates in combo_map.items():
        random.shuffle(candidates)
        count = 0
        for x in candidates:
            if x in used_place1:
                continue
            y = random.choice(top_idx[(x, top_tok)])
            z = random.choice(dis_idx[(x, dis_tok)])
            w = random.choice(dir_idx[(x, dir_tok)])
            triplet = f"{x} is {top_tok} {y}, {dis_tok} to {z}, and {dir_tok} of {w}"
            templates = TEMPLATES_3[top_tok]

            # Yes/No
            q_yes = templates[1].format(x=x, y=y, z=z, w=w, dis=dis_tok, dir=dir_tok)
            yesno_rows.append([x, dir_tok, w, top_tok, y, dis_tok, z, triplet, q_yes, "Yes", "no_change"])

            r = random.random()
            if r < 0.25:
                opp_top = TOP_OPPOSITES[top_tok]
                q_no = TEMPLATES_3[opp_top][1].format(x=x, y=y, z=z, w=w, dis=dis_tok, dir=dir_tok)
                t_label = "replace_top_token"
            elif r < 0.5:
                opp_dis = DIS_OPPOSITES[dis_tok]
                q_no = templates[1].format(x=x, y=y, z=z, w=w, dis=opp_dis, dir=dir_tok)
                t_label = "replace_dis_token"
            elif r < 0.75:
                opp_dir = DIR_OPPOSITES[dir_tok]
                q_no = templates[1].format(x=x, y=y, z=z, w=w, dis=dis_tok, dir=opp_dir)
                t_label = "replace_dir_token"
            else:
                q_no = templates[1].format(x=y, y=x, z=z, w=w, dis=dis_tok, dir=dir_tok)
                t_label = "flip_place"
            yesno_rows.append([x, dir_tok, w, top_tok, y, dis_tok, z, triplet, q_no, "No", t_label])

            # MCQ
            top_m = top_df[(top_df["place1"] != x) & (top_df["relation"] == top_tok) & (top_df["place2"] == y)]["place1"].tolist()
            dis_m = dis_df[(dis_df["place1"] != x) & (dis_df["relation"] == dis_tok) & (dis_df["place2"] == z)]["place1"].tolist()
            dir_m = dir_df[(dir_df["place1"] != x) & (dir_df["relation"] == dir_tok) & (dir_df["place2"] == w)]["place1"].tolist()
            matches = top_m + dis_m + dir_m

            counts = defaultdict(int)
            for p in matches:
                counts[p] += 1
            partial_candidates = [p for p, c in counts.items() if c >= 2]
            partial_neg = random.choice(partial_candidates) if partial_candidates else get_random_distractor(x, all_places)
            rand_neg = get_random_distractor(x, all_places)

            opts = [x, partial_neg, rand_neg]
            sources = ["correct", "partial", "random"]
            combined = list(zip(opts, sources))
            random.shuffle(combined)
            opts, sources = zip(*combined)

            ans_letter = ["A", "B", "C"][opts.index(x)]
            mcq_q = templates[0].format(x=x, y=y, z=z, w=w, dis=dis_tok, dir=dir_tok)
            mcq_rows.append([
                x, dir_tok, w, top_tok, y, dis_tok, z, triplet,
                mcq_q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", opts)),
                f"{ans_letter}. {x}", ",".join(sources)
            ])

            used_place1.add(x)
            count += 1
            if count >= target_per_combo:
                break
    return yesno_rows, mcq_rows

# Save outputs
def save_to_csv(data, folder, filename, columns):
    path = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(data, columns=columns).to_csv(path, index=False)
    print(f"[INFO] Saved → {path}")

if __name__ == "__main__":
    dir_df = load_csv("dir.csv", DIR_TOKENS)
    top_df = load_csv("top.csv", TOP_TOKENS)
    dis_df = load_csv("dis.csv", DIS_TOKENS)

    all_places = sorted(set(pd.concat([
        dir_df["place1"], dir_df["place2"],
        top_df["place1"], top_df["place2"],
        dis_df["place1"], dis_df["place2"]
    ]).unique()))
    data_yesno, data_mcq = generate_three_concept(dir_df, top_df, dis_df, all_places)
    save_to_csv(
        data_yesno, YESNO_DIR, "3_concept_yesno.csv",
        ["place1","dir","place2_Y","top","place2_Z","dis","place2_W","triplet","question","answer","transition"])
    save_to_csv(
        data_mcq, MCQ_DIR, "3_concept_mcq.csv",
        ["place1","dir","place2_Y","top","place2_Z","dis","place2_W","triplet","question","options","answer","option_sources"])