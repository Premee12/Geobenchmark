# Generate Two-Concept (Distance + Direction) Data
import os, random, pandas as pd
random.seed(42)
BASE_DIR = os.path.join("..", "geodata", "results")
REL_DIR = os.path.join("..", "geodata", "relations")
YESNO_DIR = os.path.join(BASE_DIR, "binary")
MCQ_DIR = os.path.join(BASE_DIR, "mcqs")

os.makedirs(YESNO_DIR, exist_ok=True)
os.makedirs(MCQ_DIR, exist_ok=True)

# Tokens and opposites
DIS_TOKENS = ["near", "close", "distant", "far"]
DIR_TOKENS = ["north", "south", "east", "west"]
DIST_OPPOSITES = {"near": "far", "far": "near", "close": "distant", "distant": "close"}
DIR_OPPOSITES = {"north": "south", "south": "north", "east": "west", "west": "east"}

TEMPLATES = [
    "Which city is {dis} to {y} and also {dir} from {z}?",
    "Is {x} {dis} to {y} and {dir} of {z}?"]

# Load input data
def load_data():
    dis_df = pd.read_csv(os.path.join(REL_DIR, "dis.csv"))
    dir_df = pd.read_csv(os.path.join(REL_DIR, "dir.csv"))
    dis_df = dis_df[dis_df["relation"].isin(DIS_TOKENS)]
    dir_df = dir_df[dir_df["relation"].isin(DIR_TOKENS)]
    return dis_df, dir_df
def get_random_distractor(correct, all_places):
    return random.choice([p for p in all_places if p != correct])

# Core generation
def generate_all(dis_df, dir_df, all_places):
    results_yesno, results_mcq = [], []
    common_places = list(set(dis_df["place1"]) & set(dir_df["place1"]))
    random.shuffle(common_places)

    for place in common_places:
        dis_subset = dis_df[dis_df["place1"] == place]
        dir_subset = dir_df[dir_df["place1"] == place]
        if dis_subset.empty or dir_subset.empty:
            continue

        used_dirs = []
        for dist in DIS_TOKENS:
            filtered_dis = dis_subset[dis_subset["relation"] == dist]
            available_dirs = [d for d in DIR_TOKENS if d not in used_dirs]
            filtered_dir = dir_subset[dir_subset["relation"].isin(available_dirs)]
            if filtered_dis.empty or filtered_dir.empty:
                continue

            dis_row = filtered_dis.sample(n=1, random_state=random.randint(0, 10000))
            dir_row = filtered_dir.sample(n=1, random_state=random.randint(0, 10000))
            d, r = dis_row.iloc[0], dir_row.iloc[0]

            dis_token, dir_token = d["relation"], r["relation"]
            y, z = d["place2"], r["place2"]
            used_dirs.append(dir_token)
            triplet = f"{place} is {dis_token} {y}, {dir_token} {z}"

            #  Yes/No 
            yes_q = TEMPLATES[1].format(x=place, dis=dis_token, y=y, dir=dir_token, z=z)
            results_yesno.append([place, dis_token, y, dir_token, z, triplet, yes_q, "Yes", "no_change"])

            r_val = random.random()
            if r_val < 0.33:
                opp_dis = DIST_OPPOSITES[dis_token]
                no_q = TEMPLATES[1].format(x=y, dis=opp_dis, y=place, dir=dir_token, z=z)
                t_label = "flip_place_replace_distance"
            elif r_val < 0.66:
                opp_dis = DIST_OPPOSITES[dis_token]
                no_q = TEMPLATES[1].format(x=place, dis=opp_dis, y=y, dir=dir_token, z=z)
                t_label = "replace_distance"
            else:
                opp_dir = DIR_OPPOSITES[dir_token]
                no_q = TEMPLATES[1].format(x=place, dis=dis_token, y=y, dir=opp_dir, z=z)
                t_label = "replace_direction"

            results_yesno.append([place, dis_token, y, dir_token, z, triplet, no_q, "No", t_label])

            # MCQ 
            partial_dis = dis_df[
                (dis_df["place1"] != place) &
                (dis_df["relation"] == dis_token) &
                (dis_df["place2"] == y)
            ]["place1"].tolist()
            partial_dir = dir_df[
                (dir_df["place1"] != place) &
                (dir_df["relation"] == dir_token) &
                (dir_df["place2"] == z)
            ]["place1"].tolist()

            partial_candidates = list(set(partial_dis + partial_dir))
            partial_neg = random.choice(partial_candidates) if partial_candidates else get_random_distractor(place, all_places)
            rand_neg = get_random_distractor(place, all_places)

            opts = [place, partial_neg, rand_neg]
            sources = ["correct", "partial", "random"]
            combined = list(zip(opts, sources))
            random.shuffle(combined)
            opts, sources = zip(*combined)
            ans_letter = ["A", "B", "C"][opts.index(place)]
            mcq_q = TEMPLATES[0].format(dis=dis_token, y=y, dir=dir_token, z=z)

            results_mcq.append([
                place, dis_token, y, dir_token, z, triplet,
                mcq_q, "\n".join(f"{l}. {o}" for l, o in zip("ABC", opts)),
                f"{ans_letter}. {place}", ",".join(sources)
            ])
    return results_yesno, results_mcq

# Save outputs
def save_to_csv(data, folder, filename, columns):
    path = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(data, columns=columns).to_csv(path, index=False)

if __name__ == "__main__":
    dis_df, dir_df = load_data()
    all_places = sorted(set(pd.concat([
        dis_df["place1"], dis_df["place2"],
        dir_df["place1"], dir_df["place2"]
    ]).unique()))
    data_yesno, data_mcq = generate_all(dis_df, dir_df, all_places)
    save_to_csv(
        data_yesno, YESNO_DIR, "dis_dir_yesno.csv",
        ["place1","dis","place2_Y","dir","place2_Z","triplet","question","answer","transition"])
    save_to_csv(
        data_mcq, MCQ_DIR, "dis_dir_mcq.csv",
        ["place1","dis","place2_Y","dir","place2_Z","triplet","question","options","answer","option_sources"])