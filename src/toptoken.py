# Extract topological spatial relations (borders, within) using a GeoSPARQL endpoint.

from SPARQLWrapper import SPARQLWrapper, JSON
import urllib.request
import pandas as pd
import re
import os
import sys

GRAPHDB_ENDPOINT = os.getenv("GRAPHDB_ENDPOINT", "http://localhost:X/repositories/yago")
OUTPUT_PATH = "./results/relations/top.csv"

# Disable proxy interference
proxy_support = urllib.request.ProxyHandler({})
urllib.request.install_opener(urllib.request.build_opener(proxy_support))

queries = [
    # Touches (borders)
    """
    PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
    PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>
    SELECT ?ward1 ?ward2 ?predicate WHERE {
      ?ward1 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry ?g1 .
      ?ward2 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry ?g2 .
      VALUES ?predicate { geo:sfTouches }
      ?ward1 ?predicate ?ward2 .
    }
    """,
    # Within (ward inside larger region)
    """
    PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
    PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>
    SELECT ?ward1 ?ward2 ?predicate WHERE {
      ?ward1 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry ?g1 .
      ?ward2 a yago:OS_EuropeanRegion .
      VALUES ?predicate { geo:sfWithin }
      ?ward1 ?predicate ?ward2 .
      FILTER(str(?ward1) < str(?ward2))
    }
    """,
    # Within (ward inside metropolitan district)
    """
    PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
    PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>
    SELECT ?ward1 ?ward2 ?predicate WHERE {
      ?ward1 a yago:OS_MetropolitanDistrictWard ; geo:hasGeometry ?g1 .
      ?ward2 a yago:OS_MetropolitanDistrict .
      VALUES ?predicate { geo:sfWithin }
      ?ward1 ?predicate ?ward2 .
      FILTER(str(?ward1) < str(?ward2))
    }
    """
]

rows = []
sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
sparql.setReturnFormat(JSON)
for q in queries:
    sparql.setQuery(q)
    try:
        res = sparql.queryAndConvert()
    except Exception as e:
        print("[ERROR] SPARQL query failed:", e, file=sys.stderr)
        sys.exit(1)

    for b in res["results"]["bindings"]:
        rows.append({
            "place1": b["ward1"]["value"],
            "place2": b["ward2"]["value"],
            "relation": b["predicate"]["value"]
        })

df = pd.DataFrame(rows)

def clean_uri(uri):
    name = uri.rsplit("/", 1)[-1]
    name = re.sub(r'^(geoentity_|osentity_)', '', name)
    name = re.sub(r'_[0-9]+$', '', name)
    name = re.sub(r'[_\,]', ' ', name)
    name = re.sub(r'\bWard$', '', name)
    return re.sub(r'\s+', ' ', name).strip()

df["place1"] = df["place1"].apply(clean_uri)
df["place2"] = df["place2"].apply(clean_uri)
df["relation"] = df["relation"].map({
    "http://www.opengis.net/ont/geosparql#sfTouches": "borders",
    "http://www.opengis.net/ont/geosparql#sfWithin":  "within"
})
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")