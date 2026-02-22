#Extraction of directional spatial relations (north, south, east, west)

from SPARQLWrapper import SPARQLWrapper, JSON
import urllib.request
import pandas as pd
from shapely import wkt
import math
import re
import os

# Configurable endpoint for reproducibility
GRAPHDB_ENDPOINT = os.getenv("GRAPHDB_ENDPOINT", "http://yourserver/repositories/yago")
OUTPUT_PATH = "./results/relations/dir.csv"

# Disable proxy interference
proxy_support = urllib.request.ProxyHandler({})
urllib.request.install_opener(urllib.request.build_opener(proxy_support))

sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
sparql.setReturnFormat(JSON)
sparql.setQuery("""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>
SELECT ?place1 ?wkt1 ?place2 ?wkt2 WHERE {
  ?place1 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry/geo:asWKT ?wkt1 .
  ?place2 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry/geo:asWKT ?wkt2 .
  FILTER(?place1 != ?place2)
}
""")

try:
    res = sparql.queryAndConvert()
    bindings = res["results"]["bindings"]
    records = [{
        "place1": b["place1"]["value"],
        "wkt1": b["wkt1"]["value"],
        "place2": b["place2"]["value"],
        "wkt2": b["wkt2"]["value"]
    } for b in bindings]
except Exception as e:
    print("SPARQL error:", e)
    records = []
df = pd.DataFrame(records)
def clean_uri(uri):
    name = uri.rsplit("/", 1)[-1]
    name = re.sub(r'^(geoentity_|osentity_)', '', name)
    name = re.sub(r'_[0-9]+$', '', name)
    name = re.sub(r'[_\,]', ' ', name)
    name = re.sub(r'\bWard$', '', name)
    return re.sub(r'\s+', ' ', name).strip()

def clean_wkt(wkt_str):
    if wkt_str.startswith("<"):
        return " ".join(wkt_str.split()[1:])
    return wkt_str

def get_centroid(wkt_str):
    try:
        geom = wkt.loads(clean_wkt(wkt_str))
        return geom.centroid
    except Exception:
        return None

def calculate_bearing(lat1, lon1, lat2, lon2):
    dLon = math.radians(lon2 - lon1)
    y = math.sin(dLon) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(dLon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_cardinal_direction(bearing):
    if bearing >= 315 or bearing < 45:
        return "north"
    elif bearing < 135:
        return "east"
    elif bearing < 225:
        return "south"
    else:
        return "west"

results = []
for _, row in df.iterrows():
    c1, c2 = get_centroid(row["wkt1"]), get_centroid(row["wkt2"])
    if c1 and c2:
        bearing = calculate_bearing(c2.y, c2.x, c1.y, c1.x)
        direction = get_cardinal_direction(bearing)
        results.append({
            "place1": clean_uri(row["place1"]),
            "place2": clean_uri(row["place2"]),
            "bearing": round(bearing, 2),
            "relation": direction
        })

df_out = pd.DataFrame(results)
df_out.dropna(inplace=True)
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_out.to_csv(OUTPUT_PATH, index=False)