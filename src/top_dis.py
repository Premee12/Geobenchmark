# Generate Two-Concept (Topology + Distance) Benchmark Data
import os, random, pandas as pd
random.seed(42)

BASE_DIR = os.path.join("..", "geodata", "results")
REL_DIR = os.path.join("..", "geodata", "relations")
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcqs")
os.makedirs(YESNO_DIR, exist_ok=True)
os.makedirs(MCQ_DIR, exist_ok=True)

# Tokens and opposites
TOP_TOKENS = ["within", "borders"]
DIS_TOKENS = ["near", "close", "distant", "far"]

TOP_OPPOSITES = {"within": "borders", "borders": "within"}
DIS_OPPOSITES = {"near": "far", "far": "near", "close": "distant", "distant": "close"}

TEMPLATE_MAP = {
    "within": [
        "Which city is {top} {y} and also {dis} to {z}?",
        "Is {x} {top} {y} and {dis} to {z}?"
    ],
    "borders": [
        "Which city {top} {y} and is also {dis} to {z}?",
        "Does {x} {top} {y} and {dis} to {z}?"
    ]}

# Load input data
def load_data():
    top_df = pd.read_csv(os.path.join(REL_DIR, "top.csv"))
    dis_df = pd.read_csv(os.path.join(REL_DIR, "dis.csv"))
    top_df = top_df[top_df["relation"].isin(TOP_TOKENS)]
    dis_df = dis_df[dis_df["relation"].isin(DIS_TOKENS)]
    return top_df, dis_df

def get_random_distractor(correct, all_places):
    return random.choice([p for p in all_places if p != correct])

# Create balanced sample pairs
def create_sampled_pairs(top_df, dis_df):
    pairs, common = [], list(set(top_df["place1"]) & set(dis_df["place1"]))
    random.shuffle(common)

    for place in common:
        top_subset = top_df[top_df["place1"] == place]
        dis_subset = dis_df[dis_df["place1"] == place]
        if top_subset.empty or dis_subset.empty:
            continue

        used_dists = []
        for topo in TOP_TOKENS:
            top_rows = top_subset[top_subset["relation"] == topo]
            if top_rows.empty:
                continue
            top_row = top_rows.sample(n=1, random_state=random.randint(0, 10000))

            preferred_pool = ["near", "close"] if topo == "borders" else ["distant", "far"]
            dist_priority = preferred_pool + [d for d in DIS_TOKENS if d not in preferred_pool]

            for _ in range(2):
                available_dists = [d for d in dist_priority if d not in used_dists]
                if not available_dists:
                    break
                chosen_dist = available_dists[0]
                dist_rows = dis_subset[dis_subset["relation"] == chosen_dist]
                if dist_rows.empty:
                    continue

                dis_row = dist_rows.sample(n=1, random_state=random.randint(0, 10000))
                d, t = dis_row.iloc[0], top_row.iloc[0]
                pairs.append((place, t["relation"], t["place2"], d["relation"], d["place2"]))
                used_dists.append(d["relation"])
    return pairs

# Generate Yes/No and MCQ
def generate_all(pairs, all_places, top_df, dis_df):
    yesno_data, mcq_data = [], []

    for place, top_token, y, dis_token, z in pairs:
        triplet = f"{place} is {top_token} {y}, {dis_token} {z}"
        templates = TEMPLATE_MAP[top_token]

        # Yes/No 
        q_yes = templates[1].format(x=place, top=top_token, y=y, dis=dis_token, z=z)
        yesno_data.append([place, top_token, y, dis_token, z, triplet, q_yes, "Yes", "no_change"])

        r = random.random()
        if r < 0.33:
            opp_top = TOP_OPPOSITES[top_token]
            q_no = TEMPLATE_MAP[opp_top][1].format(x=place, top=opp_top, y=y, dis=dis_token, z=z)
            t_label = "replace_top_token"
        elif r < 0.66:
            opp_dis = DIS_OPPOSITES[dis_token]
            q_no = templates[1].format(x=place, top=top_token, y=y, dis=opp_dis, z=z)
            t_label = "replace_dis_token"
        else:
            q_no = templates[1].format(x=y, top=top_token, y=place, dis=dis_token, z=z)
            t_label = "flip_place"

        yesno_data.append([place, top_token, y, dis_token, z, triplet, q_no, "No", t_label])

        # MCQ 
        partial_top = top_df[
            (top_df["place1"] != place) &
            (top_df["relation"] == top_token) &
            (top_df["place2"] == y)
        ]["place1"].tolist()
        partial_dis = dis_df[
            (dis_df["place1"] != place) &
            (dis_df["relation"] == dis_token) &
            (dis_df["place2"] == z)
        ]["place1"].tolist()

        partial_candidates = list(set(partial_top + partial_dis))
        partial_neg = random.choice(partial_candidates) if partial_candidates else get_random_distractor(place, all_places)
        rand_neg = get_random_distractor(place, all_places)

        opts = [place, partial_neg, rand_neg]
        sources = ["correct", "partial", "random"]
        combined = list(zip(opts, sources))
        random.shuffle(combined)
        opts, sources = zip(*combined)

        ans_letter = ["A", "B", "C"][opts.index(place)]
        mcq_q = templates[0].format(top=top_token, y=y, dis=dis_token, z=z)
        mcq_data.append([
            place, top_token, y, dis_token, z, triplet,
            mcq_q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", opts)),
            f"{ans_letter}. {place}", ",".join(sources)
        ])
    return yesno_data, mcq_data

def save_to_csv(data, folder, filename, columns):
    path = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(data, columns=columns).to_csv(path, index=False)
    
if __name__ == "__main__":
    top_df, dis_df = load_data()
    all_places = sorted(set(pd.concat([
        top_df["place1"], top_df["place2"],
        dis_df["place1"], dis_df["place2"]
    ]).unique()))

    pairs = create_sampled_pairs(top_df, dis_df)
    data_yesno, data_mcq = generate_all(pairs, all_places, top_df, dis_df)

    save_to_csv(
        data_yesno, YESNO_DIR, "top_dis_yesno.csv",
        ["place1","top","place2_Y","dis","place2_Z","triplet","question","answer","transition"])
    save_to_csv(
        data_mcq, MCQ_DIR, "top_dis_mcq.csv",
        ["place1","top","place2_Y","dis","place2_Z","triplet","question","options","answer","option_sources"])