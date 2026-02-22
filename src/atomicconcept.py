# Generate single Concept Data
import os, random, pandas as pd
random.seed(42)

# Directory
BASE_DIR = os.path.join("..", "geodata", "results")       
REL_DIR = os.path.join("..", "geodata", "relations")     
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcqs")

os.makedirs(YESNO_DIR, exist_ok=True)
os.makedirs(MCQ_DIR, exist_ok=True)

YESNO_FILE, MCQ_FILE = "atomic_yesno.csv", "atomic_mcq.csv"

# Token definitions
DIR_TOKENS = ["north", "south", "east", "west"]
DIS_TOKENS = ["near", "close", "distant", "far"]
TOP_TOKENS = ["within", "borders"]

DIRECTION_OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}
DISTANCE_OPPOSITES = {"near": "far", "far": "near", "close": "distant", "distant": "close"}
TOPOLOGY_OPPOSITES = {"within": "borders", "borders": "within"}

def load_csv(name, tokens):
    df = pd.read_csv(f"{REL_DIR}/{name}")
    return df[df["relation"].isin(tokens)]

def balance_dataset(df, token_col, group_size):
    return pd.concat([
        df[df[token_col] == token].sample(
            n=min(group_size, len(df[df[token_col] == token])),
            random_state=42
        ) for token in sorted(df[token_col].unique())
    ])

def process_topology(df, within_target, borders_target):
    borders_df = df[df["relation"] == "borders"]
    within_df = df[df["relation"] == "within"]
    return pd.concat([
        borders_df.sample(n=min(borders_target, len(borders_df)), random_state=42),
        within_df.sample(n=min(within_target, len(within_df)), random_state=42)
    ])

# Question generators
def get_random_distractor(correct, all_places):
    return random.choice([p for p in all_places if p != correct])

def generate_yes(p1, p2, rel):
    if rel in DIRECTION_OPPOSITES:
        return [(f"Is {p1} {rel} of {p2}?", "Yes", "no_change")]
    if rel in DISTANCE_OPPOSITES:
        return [(f"Is {p1} {rel} to {p2}?", "Yes", "no_change")]
    if rel == "within":
        return [(f"Is {p1} within {p2}?", "Yes", "no_change")]
    if rel == "borders":
        return [(f"Does {p1} border {p2}?", "Yes", "no_change")]
    return []

def generate_no(p1, p2, rel):
    if rel in DIRECTION_OPPOSITES or rel in DISTANCE_OPPOSITES:
        if random.random() < 0.5:
            return [(f"Is {p2} {rel} of {p1}?", "No", "flip_place")]
        opp = DIRECTION_OPPOSITES.get(rel, DISTANCE_OPPOSITES.get(rel))
        connector = "of" if rel in DIRECTION_OPPOSITES else "to"
        label = "replace_dir_token" if rel in DIRECTION_OPPOSITES else "replace_dis_token"
        return [(f"Is {p1} {opp} {connector} {p2}?", "No", label)]
    if rel == "within":
        return [(f"Does {p1} border {p2}?", "No", "replace_top_token")]
    if rel == "borders":
        return [(f"Is {p1} within {p2}?", "No", "replace_top_token")]
    return []

# MCQ generation
def generate_mcq(dir_df, dis_df, top_df, all_places):
    rows = []

    # Direction and Distance
    for df, rel_type in [(dir_df, "direction"), (dis_df, "distance")]:
        for _, row in df.iterrows():
            p1, rel, p2 = row["place1"], row["relation"], row["place2"]
            q = f"Which city is located in {rel} of {p2}?" if rel_type == "direction" else f"Which city is {rel} to {p2}?"

            rel_df = dir_df if rel_type == "direction" else dis_df
            hard_negatives = rel_df[
                (rel_df["relation"] == rel) &
                (rel_df["place2"] == p2) &
                (rel_df["place1"] != p1)
            ]["place1"].tolist()

            hard_neg = random.choice(hard_negatives) if hard_negatives else get_random_distractor(p1, all_places)
            rand_neg = get_random_distractor(p1, all_places)

            opts = [p1, hard_neg, rand_neg]
            sources = ["correct", "hard", "random"]
            combined = list(zip(opts, sources))
            random.shuffle(combined)
            opts, sources = zip(*combined)

            ans = ["A", "B", "C"][opts.index(p1)]
            rows.append([
                p1, rel, p2, f"{p1} is {rel} {p2}",
                q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", opts)),
                f"{ans}. {p1}", ",".join(sources)
            ])

    # Topology
    for _, row in top_df.iterrows():
        p1, rel, p2 = row["place1"], row["relation"], row["place2"]
        q = f"Which city is within {p2}?" if rel == "within" else f"Which city borders {p2}?"

        same_df = top_df[top_df["relation"] == rel]
        opp_df = top_df[top_df["relation"] != rel]

        hard_neg = random.choice(same_df["place1"].tolist()) if not same_df.empty else get_random_distractor(p1, all_places)
        opp_neg = random.choice(opp_df["place1"].tolist()) if not opp_df.empty else get_random_distractor(p1, all_places)

        opts = [p1, hard_neg, opp_neg]
        sources = ["correct", "hard", "random"]
        combined = list(zip(opts, sources))
        random.shuffle(combined)
        opts, sources = zip(*combined)

        ans = ["A", "B", "C"][opts.index(p1)]
        rows.append([
            p1, rel, p2, f"{p1} is {rel} {p2}",
            q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", opts)),
            f"{ans}. {p1}", ",".join(sources)
        ])

    return rows

# Data loading
dir_df = balance_dataset(load_csv("dir.csv", DIR_TOKENS), "relation", 500)
dis_df = balance_dataset(load_csv("dis.csv", DIS_TOKENS), "relation", 500)
top_df = process_topology(load_csv("top.csv", TOP_TOKENS), 500, 500)

all_places = sorted(set(pd.concat([
    dir_df["place1"], dir_df["place2"],
    dis_df["place1"], dis_df["place2"],
    top_df["place1"], top_df["place2"]
]).unique()))

# Build Yes/No dataset
yesno_data = []
for df in [dir_df, dis_df, top_df]:
    for _, row in df.iterrows():
        yesno_data.extend([[row["place1"], row["relation"], row["place2"], q, a, t]
            for q, a, t in generate_yes(row["place1"], row["place2"], row["relation"])])
        yesno_data.extend([[row["place1"], row["relation"], row["place2"], q, a, t]
            for q, a, t in generate_no(row["place1"], row["place2"], row["relation"])])

# Build MCQ dataset
mcq_data = generate_mcq(dir_df, dis_df, top_df, all_places)

# outputs
pd.DataFrame(
    yesno_data,
    columns=["place1", "relation", "place2", "question", "answer", "transition"]
).to_csv(f"{YESNO_DIR}/{YESNO_FILE}", index=False)
pd.DataFrame(
    mcq_data,
    columns=["place1", "relation", "place2", "triplet", "question", "options", "answer", "option_sources"]
).to_csv(f"{MCQ_DIR}/{MCQ_FILE}", index=False)