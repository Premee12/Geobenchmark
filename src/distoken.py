#Extraction of distance spatial relations (near, close, distant, far)

from SPARQLWrapper import SPARQLWrapper, JSON
import pandas as pd
import urllib.request
import re
import os
import sys

# Configurable endpoint
GRAPHDB_ENDPOINT = os.getenv("GRAPHDB_ENDPOINT", "http://localhost:X/repositories/yago")
OUTPUT_PATH = "./results/relations/dis.csv"

# Disable proxy interference
proxy_support = urllib.request.ProxyHandler({})
urllib.request.install_opener(urllib.request.build_opener(proxy_support))

sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
sparql.setReturnFormat(JSON)
sparql.setQuery("""
PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX uom:  <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>

SELECT ?ward1 ?ward2 ?dist
       (IF(?dist <= 5000,   "near",
        IF(?dist <= 25000,  "close",
        IF(?dist <= 80000,  "distant", "far")))
        AS ?distanceToken)
WHERE {
  ?ward1 a yago:OS_MetropolitanDistrictWard ;
         geo:hasGeometry/geo:asWKT ?wkt1 .
  ?ward2 a yago:OS_MetropolitanDistrictWard ;
         geo:hasGeometry/geo:asWKT ?wkt2 .
  FILTER(str(?ward1) < str(?ward2))
  BIND(geof:distance(?wkt1, ?wkt2, uom:metre) AS ?dist)
}
""")
try:
    result = sparql.queryAndConvert()
except Exception as e:
    print("[ERROR] SPARQL query failed:", e, file=sys.stderr)
    sys.exit(1)
rows = []
for b in result["results"]["bindings"]:
    rows.append({
        "ward1": b["ward1"]["value"],
        "ward2": b["ward2"]["value"],
        "distance_m": float(b["dist"]["value"]),
        "relation": b["distanceToken"]["value"]
    })
def clean_uri(uri):
    name = uri.rsplit("/", 1)[-1]
    name = re.sub(r'^(geoentity_|osentity_)', '', name)
    name = re.sub(r'_[0-9]+$', '', name)
    name = re.sub(r'[_\,]', ' ', name)
    name = re.sub(r'\bWard$', '', name)
    return re.sub(r'\s+', ' ', name).strip()

df = pd.DataFrame(rows)
df["place1"] = df["ward1"].apply(clean_uri)
df["place2"] = df["ward2"].apply(clean_uri)

df_out = df[["place1", "place2", "relation", "distance_m"]].copy()
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")