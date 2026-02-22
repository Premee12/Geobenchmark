#Generate Two-Concept (Direction + Topology) Benchmark Data
import os, random, pandas as pd
random.seed(42)
# Directory setup
BASE_DIR = os.path.join("..", "geodata", "results")
REL_DIR = os.path.join("..", "geodata", "relations")
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcqs")

os.makedirs(YESNO_DIR, exist_ok=True)
os.makedirs(MCQ_DIR, exist_ok=True)

# Tokens and opposites
DIR_TOKENS = ["north", "east", "south", "west"]
TOP_TOKENS = ["within", "borders"]

DIR_OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}
TOP_OPPOSITES = {"within": "borders", "borders": "within"}

TEMPLATES = [
    "Which city lies {dir} to {y} and {top} {z}?",
    "Is {x} {dir} of {y} and {top} {z}?"
]

def load_data():
    dir_df = pd.read_csv(os.path.join(REL_DIR, "dir.csv"))
    top_df = pd.read_csv(os.path.join(REL_DIR, "top.csv"))
    dir_df = dir_df[dir_df["relation"].isin(DIR_TOKENS)]
    top_df = top_df[top_df["relation"].isin(TOP_TOKENS)]
    return dir_df, top_df

def get_random_distractor(correct, all_places):
    return random.choice([p for p in all_places if p != correct])

# Core generation
def generate_all(dir_df, top_df, all_places):
    results_yesno, results_mcq = [], []
    common_places = list(set(dir_df["place1"]).intersection(set(top_df["place1"])))
    random.shuffle(common_places)

    for place in common_places:
        dir_subset = dir_df[dir_df["place1"] == place]
        top_subset = top_df[top_df["place1"] == place]
        if dir_subset.empty or top_subset.empty:
            continue

        used_dirs = []
        random.shuffle(DIR_TOKENS)

        for top_type in TOP_TOKENS:
            filtered_top = top_subset[top_subset["relation"] == top_type]
            if filtered_top.empty:
                continue
            top_row = filtered_top.sample(n=1, random_state=random.randint(0, 10000))

            available_dirs = [d for d in DIR_TOKENS if d not in used_dirs]
            filtered_dir = dir_subset[dir_subset["relation"].isin(available_dirs)]
            if filtered_dir.empty:
                continue
            dir_row = filtered_dir.sample(n=1, random_state=random.randint(0, 10000))

            d, t = dir_row.iloc[0], top_row.iloc[0]
            dir_token, top_token = d["relation"], t["relation"]
            y, z = d["place2"], t["place2"]
            used_dirs.append(dir_token)
            triplet = f"{place} is {dir_token} {y}, {top_token} {z}"

            # Yes/No 
            yes_q = TEMPLATES[1].format(x=place, dir=dir_token, y=y, top=top_token, z=z)
            results_yesno.append([place, dir_token, y, top_token, z, triplet, yes_q, "Yes", "no_change"])

            r = random.random()
            if r < 0.25:
                no_q = TEMPLATES[1].format(x=y, dir=dir_token, y=place, top=top_token, z=z)
                t_label = "flip_place_y"
            elif r < 0.5:
                no_q = TEMPLATES[1].format(x=place, dir=DIR_OPPOSITES[dir_token], y=y, top=top_token, z=z)
                t_label = "replace_dir_token"
            elif r < 0.75:
                no_q = TEMPLATES[1].format(x=place, dir=dir_token, y=y, top=TOP_OPPOSITES[top_token], z=z)
                t_label = "replace_top_token"
            else:
                no_q = TEMPLATES[1].format(x=z, dir=dir_token, y=y, top=top_token, z=place)
                t_label = "flip_place_z"

            results_yesno.append([place, dir_token, y, top_token, z, triplet, no_q, "No", t_label])

            #  MCQ
            dir_matches = dir_df[
                (dir_df["place1"] != place) &
                (dir_df["relation"] == dir_token) &
                (dir_df["place2"] == y)
            ]["place1"].tolist()

            top_matches = top_df[
                (top_df["place1"] != place) &
                (top_df["relation"] == top_token) &
                (top_df["place2"] == z)
            ]["place1"].tolist()

            partial_candidates = list(set(dir_matches + top_matches))
            partial_neg = random.choice(partial_candidates) if partial_candidates else get_random_distractor(place, all_places)
            rand_neg = get_random_distractor(place, all_places)

            options = [place, partial_neg, rand_neg]
            sources = ["correct", "partial", "random"]
            combined = list(zip(options, sources))
            random.shuffle(combined)
            options, sources = zip(*combined)

            ans_letter = ["A", "B", "C"][options.index(place)]
            mcq_q = TEMPLATES[0].format(dir=dir_token, y=y, top=top_token, z=z)

            results_mcq.append([
                place, dir_token, y, top_token, z, triplet,
                mcq_q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", options)),
                f"{ans_letter}. {place}", ",".join(sources)
            ])
    return results_yesno, results_mcq

# Save outputs
def save_to_csv(data, folder, filename, columns):
    out_path = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    pd.DataFrame(data, columns=columns).to_csv(out_path, index=False)
    print(f"[INFO] Saved {out_path}")

if __name__ == "__main__":
    dir_df, top_df = load_data()
    all_places = sorted(set(pd.concat([
        dir_df["place1"], dir_df["place2"],
        top_df["place1"], top_df["place2"]
    ]).unique()))
    data_yesno, data_mcq = generate_all(dir_df, top_df, all_places)
    save_to_csv(
        data_yesno, YESNO_DIR, "dir_top_yesno.csv",
        ["place1","dir","place2_Y","top","place2_Z","triplet","question","answer","transition"])
    save_to_csv(
        data_mcq, MCQ_DIR, "dir_top_mcq.csv",
        ["place1","dir","place2_Y","top","place2_Z","triplet","question","options","answer","option_sources"])