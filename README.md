# GeoBenchmark: Probing Large Language Models for Geo-Spatial Knowledge

<div align="center">
    <br>
    <img align="center" src="https://github.com/irit/GeoBenchmark/blob/main/logo/geobenchmark_logo.png" alt="GeoBenchmark" width="400"/>
    <br><br>
    <strong>A comprehensive geospatial reasoning benchmark for evaluating large language models on geographic commonsense reasoning tasks.</strong>
    <br><br>
    <a href="https://arxiv.org/abs/YOUR_PAPER_ID"><img src="https://img.shields.io/badge/Paper-LREC%202026-blue"/></a>
    <a href="https://huggingface.co/datasets/your-username/GeoBenchmark"><img src="https://img.shields.io/badge/🤗%20Hugging%20Face-Dataset-yellow"/></a>
    <a href="https://creativecommons.org/licenses/by-sa/4.0/"><img src="https://img.shields.io/badge/License-CC%20BY--SA%204.0-green"/></a>
</div>

---

## Overview

**GeoBenchmark** is a structured benchmark of **39,378 question–answer pairs** designed to systematically probe the geospatial reasoning capabilities of language models. The benchmark evaluates model performance across three core spatial relation families:

- **Direction** — cardinal relations: *north, south, east, west*
- **Distance** — proximity relations: *near, close, distant, far*
- **Topology** — geometric relations: *within, borders*

Questions are available in two complementary formats — **Binary Yes/No** and **Multiple-Choice (MCQ)** — and span three levels of compositional complexity, from single-relation atomic queries to multi-relation three-concept chains.

The dataset is derived from the United Kingdom subset of [YAGO2geo](https://yago2geo.di.uoa.gr/) and generated automatically from RDF triples following [GeoSPARQL](http://www.opengis.net/ont/geosparql#) conventions, ensuring full reproducibility and methodological consistency.

> **The accompanying research paper can be read here:** [GeoBenchmark: Probing Large Language Models for Geo-Spatial Knowledge — LREC 2026](#) *(link to be updated upon publication)*

---

## Team & Authors

<img align="right" src="Geobenchmark/irit.jpeg" alt="ai-team-uoa" width="200"/>

- [**Lynda Tamine-Lechani**](https://www.irit.fr/~Lynda.Tamine-Lechani/), Professor, Universty of Toulouse, France 
- [**Jose G Moreno**](https://www.irit.fr/~Jose.Moreno/), Associate Professor, Universty of Toulouse, France
- [**Abayomi-Alli Ayomide**](https://www.linkedin.com/in/ayomide-abayomi-alli/), Masters Research Student, Université Jean Monnet Saint-Etienne, France
- [**Karim Radouane**](https://), Phd Researcher Student, Universty of Toulouse, France

---

## Repository Structure

```
GeoBenchmark/
├── geodata/
│   ├── relations/                    # Raw spatial relations extracted from GraphDB
│   │   ├── dir.csv                   # Directional relations
│   │   ├── dis.csv                   # Distance relations
│   │   └── top.csv                   # Topological relations
│   └── results/
│       ├── binary/                   # Yes/No QA format
│       │   ├── atomic_yes_no.csv
│       │   ├── dir_topology_yes_no.csv
│       │   ├── dir_distance_yes_no.csv
│       │   ├── top_distance_yes_no.csv
│       │   ├── three_concept_yes_no.csv
│       │   └── geobenchmark_all_yes_no.csv
│       └── mcq/                      # Multiple-choice QA format
│           ├── atomic_mcq.csv
│           ├── dir_topology_mcq.csv
│           ├── dir_distance_mcq.csv
│           ├── top_distance_mcq.csv
│           ├── three_concept_mcq.csv
│           └── geobenchmark_all_mcq.csv
├── src/
│   ├── dirtoken.py                   # Extract directional relations
│   ├── distoken.py                   # Extract distance relations
│   ├── topotoken.py                  # Extract topological relations
│   ├── run_all_relations.py          # Master extraction script
│   ├── atomicconcept.py              # Generate single-relation datasets
│   ├── dir_top.py                    # Direction + Topology combinations
│   ├── dis_dir.py                    # Distance + Direction combinations
│   ├── top_dis.py                    # Topology + Distance combinations
│   ├── three_concept.py              # Three-relation combinations
│   ├── run_all_concepts.py           # Master generation script
│   └── benchmarkmerge.py            # Merge all subsets into final benchmark
├── geoBenchmark_all_mcq.csv
├── geoBenchmark_all_binary.csv
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Dataset Statistics

The table below summarises the composition of GeoBenchmark across relation levels and relation types. Each level introduces greater compositional complexity, requiring models to jointly reason over multiple spatial concepts.

| Relation Level | Yes/No QA | MCQ QA | Distinct Entities / Notes |
|---|---|---|---|
| **Atomic (1 Relation)** | 10,000 | 5,000 | 783 subjects, 820 objects; 10 relation tokens evenly distributed (500 each). |
| **Two-Relation** | 14,844 | 7,422 | Balanced coverage across Direction+Distance, Direction+Topology, and Topology+Distance configurations. |
| **Three-Relation** | 1,408 | 704 | 704 subjects, 512 objects; triplets span all three relation families simultaneously. |
| **Total QA Pairs** | **26,252** | **13,126** | Combined total of **39,378** question–answer pairs (Yes/No + MCQ). |

### Relation Token Distribution

| Relation Family | Token | Count |
|---|---|---|
| **Direction** | North | 1,859 |
| | South | 1,859 |
| | East | 1,749 |
| | West | 1,760 |
| **Distance** | Near | 2,164 |
| | Close | 2,196 |
| | Far | 2,119 |
| | Distant | 2,111 |
| **Topology** | Within | 3,017 |
| | Borders | 3,124 |

## Installation

### Prerequisites

- Python ≥ 3.8
- [GraphDB (Ontotext)](https://graphdb.ontotext.com/) with GeoSPARQL support enabled
- YAGO2geo dataset (UK region)

### Quick Start

```bash
git clone https://github.com/irit/GeoBenchmark.git
cd GeoBenchmark
pip install -r requirements.txt
```

### Setting Up the Knowledge Base

1. Download the YAGO2geo UK subset from [https://yago2geo.di.uoa.gr/](https://yago2geo.di.uoa.gr/)
2. Install GraphDB from [Ontotext](https://graphdb.ontotext.com/)
3. Create a repository named `yago` and import the YAGO2geo RDF data
4. Verify the SPARQL endpoint is accessible at: `http://localhost:7200/repositories/yago`

### Configure the GraphDB Endpoint

```bash
export GRAPHDB_ENDPOINT="http://localhost:7200/repositories/yago"
```

---

## SPARQL Prefixes

The following namespace prefixes are used consistently throughout all SPARQL queries in this project:

```sparql
PREFIX geo:  <http://www.opengis.net/ont/geosparql#>
PREFIX geof: <http://www.opengis.net/def/function/geosparql/>
PREFIX uom:  <http://www.opengis.net/def/uom/OGC/1.0/>
PREFIX yago: <http://kr.di.uoa.gr/yago2geo/ontology/>
```

These prefixes cover:

- **`geo:`** — Core GeoSPARQL ontology (geometries, spatial relations)
- **`geof:`** — GeoSPARQL spatial functions (e.g., `geof:distance`)
- **`uom:`** — OGC units of measure (e.g., `uom:metre`)
- **`yago:`** — YAGO2geo ontology for UK geographic entity types

### Example Queries

**Distance-based relations** with binned labels:

```sparql
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
```

---

## Running the Pipeline

### Stage 1 — Extract Spatial Relations

```bash
python3 src/run_all_relations.py
```

Extracts directional, distance, and topological relations from the GraphDB SPARQL endpoint and writes them to `geodata/relations/`.

**Expected runtime:** 15–45 minutes

### Stage 2 — Generate QA Datasets

```bash
python3 src/run_all_concepts.py
```

Generates concept-level question–answer pairs for all relation levels (atomic, two-concept, three-concept) in both binary and MCQ formats.

**Expected runtime:** 30–90 minutes

### Stage 3 — Assemble the Final Benchmark

```bash
python3 src/benchmarkmerge.py
```

Merges all subsets into two unified files:

- `geobenchmark_all_yes_no.csv` — 26,252 binary pairs
- `geobenchmark_all_mcq.csv` — 13,126 MCQ pairs

---

## Dataset Usage

### Load with Pandas

```python
import pandas as pd

binary_data = pd.read_csv("geodata/results/binary/geobenchmark_all_yes_no.csv")
mcq_data    = pd.read_csv("geodata/results/mcq/geobenchmark_all_mcq.csv")

# Filter by complexity level
atomic      = binary_data[binary_data['concept_level'] == 1]
two_concept = binary_data[binary_data['concept_level'] == 2]
three_concept = binary_data[binary_data['concept_level'] == 3]
```

### Load from Hugging Face

```python
from datasets import load_dataset

binary = load_dataset("your-username/GeoBenchmark", "binary")
mcq    = load_dataset("your-username/GeoBenchmark", "mcq")
```

---

## Distance Definitions
The full distance token mapping (near / close / distant / far) applies the following bins computed in metres via `geof:distance`:

| Token | Distance Range |
|---|---|
| **near** | ≤ 5,000 m |
| **close** | 5,001 – 25,000 m |
| **distant** | 25,001 – 80,000 m |
| **far** | > 80,000 m |

---

## File Format

### Binary (Yes/No) QA Format

```csv
question,answer,transition,concept,top,dis,dir
Is Bradford near to Harpurhey?,Yes,no_change,1,0,1,0
```

| Field | Description |
|---|---|
| `question` | Natural language question |
| `answer` | `Yes` or `No` |
| `transition` | Distractor strategy: `no_change`, `flip_place`, `replace_dir_token` |
| `concept_level` | 1 (atomic), 2 (two-concept), or 3 (three-concept) |
| `top` | 1 indicates topology relation present |
| `dis` | 1 indicates distance relation present |
| `dir` | 1 indicates directional relation present |

### Multiple-Choice (MCQ) Format

```csv
question,options,answer,option_sources,concept,top,dis,dir
Which city is close to Westerhope and also east from Newburn?,"A. Whiteleas
B. Chopwell and Rowlands Gill
C. Longbenton",C. Longbenton,"partial,random,correct",2,0,1,1
```

| Field | Description |
|---|---|
| `question` | Natural language question |
| `options` | Answer choices (A-C) |
| `answer` | Correct option letter |
| `option_sources` | Distractor sampling strategy (`random`, `partial`, `correct`) |
| `concept` | Complexity level (1–3) |
| `top` | 1 indicates topology relation present |
| `dis` | 1 indicates distance relation present |
| `dir` | 1 indicates directional relation present |


---

## Citation

If you use GeoBenchmark in your research, please cite:

```bibtex
@dataset{geobenchmark2026,
  title     = {GeoBenchmark: Probing Large Language Models for Geo-Spatial Knowledge},
  author    = { },
  year      = {2026},
  publisher = {LREC 2026 Dataset Track},
  url       = {https://github.com/irit/GeoBenchmark}
}
```

---

## License

GeoBenchmark is released under **CC BY-SA 4.0** (Creative Commons Attribution-ShareAlike 4.0 International). See `LICENSE` for full terms.

---

## Contributing

Contributions are welcome. To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your contribution'`
4. Push to your fork: `git push origin feature/your-feature`
5. Open a Pull Request

---

## Changelog

### Version 1.0 — LREC 2026
- Initial public release
- 39,378 Q&A pairs across binary and MCQ formats
- Complete SPARQL extraction and generation pipeline
- Full reproducibility documentation

---

**Last Updated:** February 2026 | **Repository:** [https://github.com/irit/GeoBenchmark](https://github.com/irit/GeoBenchmark)