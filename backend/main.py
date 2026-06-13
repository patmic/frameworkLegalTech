"""
MALTG Architecture Validator — Backend API v3.0 LegalTech Edition
Endpoints:
  GET /api/ontology    → parse MALTG_onto.owl → D3 graph JSON
  GET /api/dt-arch     → serve dt_arch.json + hash
  GET /api/validation  → 9-dimension conformance scores (8 EA + 1 LegalTech)
  GET /api/methodology → formal 5-phase validation methodology metadata
  GET /api/workflow    → parse 141_SUMARIO.json (BPMN JointJS) → procedural flow graph
  GET /api/health      → hashes + existence check
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import json, hashlib
from pathlib import Path

app = FastAPI(
    title="MALTG Architecture Validator API — LegalTech Edition",
    version="3.0.0",
    description=(
        "Validates conformance of a LegalTech enterprise architecture "
        "implementation (Digital Twin) against the MALTG multi-layer "
        "governance ontology (TOGAF + COBIT + NIST + LegalTech Domain)."
    ),
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

DATA_DIR   = Path("/data")
OWL_PATH   = DATA_DIR / "MALTG_onto.owl"
DT_PATH    = DATA_DIR / "dt_arch.json"
WF_DIR     = DATA_DIR / "workflow"        # directory holding BPMN workflow JSON files
EXP_DIR    = DATA_DIR / "LegalCase"        # decided cases (causas/juicios) JSON files
MALTG_PATH = DATA_DIR / "1_MALTG.json"    # JSON-LD multidimensional architecture
FRONT_DIR  = Path("/frontend")

OWL_NS   = "http://www.w3.org/2002/07/owl#"
RDF_NS   = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS  = "http://www.w3.org/2000/01/rdf-schema#"
MALTG_NS = "http://maltg.arch/onto#"

# ═══════════════════════════════════════════════════════════════════
#  9 VALIDATION DIMENSIONS
#  8 standard EA + 1 LegalTech domain (new, justifies paper title)
# ═══════════════════════════════════════════════════════════════════
DIMENSIONS = [
    {
        "key": "TOGAF", "label": "Gobernanza TOGAF",
        "bar_color": "linear-gradient(90deg,#00e5ff,#0072ff)",
        "owl_types": ["togaf"],
        "dt_refs": ["TOGAF","Business_Architecture","Information_Systems_Architecture",
                    "Technology_Architecture","ADM_Cycle","Architecture_Vision","Enterprise_Continuum"],
    },
    {
        "key": "COBIT", "label": "Control COBIT",
        "bar_color": "linear-gradient(90deg,#ffc947,#ff6b35)",
        "owl_types": ["cobit"],
        "dt_refs": ["COBIT","EDM_Domain","APO_Domain","BAI_Domain","DSS_Domain","MEA_Domain"],
    },
    {
        "key": "NIST", "label": "Resiliencia NIST",
        "bar_color": "linear-gradient(90deg,#ff4d6d,#c026d3)",
        "owl_types": ["nist"],
        "dt_refs": ["NIST_CSF","Identify_Function","Protect_Function",
                    "Detect_Function","Respond_Function","Recover_Function"],
    },
    {
        "key": "AI", "label": "Integración IA",
        "bar_color": "linear-gradient(90deg,#a855f7,#6366f1)",
        "owl_types": ["ai"],
        "dt_refs": ["AI_Layer","ML_Models","NLP_Pipeline","Computer_Vision","Predictive_Analytics"],
    },
    {
        "key": "BC", "label": "Blockchain Adoption",
        "bar_color": "linear-gradient(90deg,#10e98c,#06b6d4)",
        "owl_types": ["blockchain"],
        "dt_refs": ["Blockchain_Layer","Smart_Contracts","DLT_Network","Consensus_Protocol","Tokenization"],
    },
    {
        "key": "OD", "label": "Open Data Comply",
        "bar_color": "linear-gradient(90deg,#ff9a3c,#ffc947)",
        "owl_types": ["opendata"],
        "dt_refs": ["OpenData_Layer","APIs","Data_Lakes","Open_Standards","Interoperability"],
    },
    {
        "key": "SEC", "label": "Security Posture",
        "bar_color": "linear-gradient(90deg,#f472b6,#e879f9)",
        "owl_types": ["security"],
        "dt_refs": ["Security_Layer","Zero_Trust","Encryption","IAM","Compliance"],
    },
    {
        "key": "INTEROP", "label": "Interoperabilidad",
        "bar_color": "linear-gradient(90deg,#34d399,#10b981)",
        "owl_types": ["opendata","security"],
        "dt_refs": ["OpenData_Layer","APIs","Data_Lakes","Open_Standards","Interoperability",
                    "Security_Layer","Zero_Trust","Compliance","Technology_Architecture"],
    },
    # ── NEW: LegalTech Domain Dimension ───────────────────────────
    {
        "key": "LEGALTECH", "label": "LegalTech Compliance",
        "bar_color": "linear-gradient(90deg,#60a5fa,#3b82f6)",
        "owl_types": ["legaltech"],
        "dt_refs": [
            "LegalTech_Domain",                      # root (40% base)
            "Contract_Lifecycle_Management",          # sub-concepts
            "eDiscovery_Pipeline",
            "Legal_DLT_Notarization",
            "Regulatory_Compliance_Engine",
            "GDPR_Compliance",
            "eIDAS_Compliance",
            "NIS2_Compliance",
            "Attorney_Client_Confidentiality",
            "Smart_Legal_Contracts",
            "Legal_Knowledge_Base",
            "Court_System_Integration",
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════
#  FORMAL METHODOLOGY — 5-phase framework for academic paper
# ═══════════════════════════════════════════════════════════════════
METHODOLOGY = {
    "title": "MALTG Multi-Layer Conformance Validation Methodology",
    "formal_model": {
        "notation": "MALTG = ⟨Ω, Δ, Γ, Ψ, δ⟩",
        "components": [
            {
                "symbol": "Ω",
                "name": "Ontological Reference Model",
                "definition": "OWL 2 ontology with taxonomy C (classes), properties P (object/annotation), instances I. MALTG_onto.owl is the canonical Ω.",
                "formal": "Ω = ⟨C, P, I, ≤, A⟩ where ≤ is the subsumption relation and A are annotation axioms"
            },
            {
                "symbol": "Δ",
                "name": "Structural Digital Twin",
                "definition": "Directed graph G(V, E) representing the microservice architecture. dt_arch.json is the canonical Δ.",
                "formal": "Δ = ⟨V, E, τ, μ⟩ where V are services, E connections, τ: V→ColorType, μ: V→2^C maltg_refs"
            },
            {
                "symbol": "Γ",
                "name": "Conformance Mapping",
                "definition": "Function mapping ontology concepts to Digital Twin services via maltg_ref annotations.",
                "formal": "Γ: C → 2^V  where  Γ(c) = {v ∈ V | c ∈ μ(v)}"
            },
            {
                "symbol": "Ψ",
                "name": "Hierarchical Coverage Function",
                "definition": "Weighted coverage metric that gives 40% weight to root concept coverage and 60% distributed across sub-concepts.",
                "formal": "Ψ(d) = 0.4·𝟙[root_d ∈ R] + 0.6·(|sub_d ∩ R| / |sub_d|)  where R = ∪_{v∈V} μ(v)"
            },
            {
                "symbol": "δ",
                "name": "Conformance Gap",
                "definition": "Absolute gap between ontological maturity score and achieved Digital Twin coverage.",
                "formal": "δ(d) = score_Ω(d) − score_Ω(d) · Ψ(d) = score_Ω(d) · (1 − Ψ(d))"
            }
        ]
    },
    "phases": [
        {
            "id": "P1",
            "name": "Ontological Reference Elicitation",
            "abbrev": "ORE",
            "color": "#00e5ff",
            "description": "Parse MALTG_onto.owl and extract the formal concept graph Ω. Group classes by maltg:layer annotation into validation dimensions. Compute per-class maturity weights from maltg:score.",
            "inputs":  ["MALTG_onto.owl"],
            "outputs": ["Concept graph Ω", "Dimension clusters C_d", "Score vector score_Ω"],
            "api":     "/api/ontology",
            "academic_ref": "OWL 2 Web Ontology Language Structural Specification (W3C 2012)"
        },
        {
            "id": "P2",
            "name": "Digital Twin Structural Mapping",
            "abbrev": "DTSM",
            "color": "#a855f7",
            "description": "Parse dt_arch.json and construct the directed service graph Δ. Build the coverage set R by collecting all maltg_ref values (string or array) across all services.",
            "inputs":  ["dt_arch.json"],
            "outputs": ["Service graph Δ", "Coverage set R", "Mapping Γ: C → 2^V"],
            "api":     "/api/dt-arch",
            "academic_ref": "Grieves & Vickers (2017) Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems"
        },
        {
            "id": "P3",
            "name": "Hierarchical Conformance Scoring",
            "abbrev": "HCS",
            "color": "#10e98c",
            "description": "Apply Ψ function per dimension. Compute onto_score as mean(maltg:score) for dimension classes. Compute dt_score = onto_score × Ψ(d). Applies to all 9 dimensions including LegalTech.",
            "inputs":  ["Ω from P1", "R from P2", "DIMENSIONS config"],
            "outputs": ["onto_score[d]", "dt_score[d]", "Ψ(d)", "δ(d) for each d"],
            "api":     "/api/validation → dimensions[]",
            "academic_ref": "Lawshe (1975) Content Validity Ratio — adapted for hierarchical ontology coverage"
        },
        {
            "id": "P4",
            "name": "LegalTech Domain Compliance Check",
            "abbrev": "LDCC",
            "color": "#60a5fa",
            "description": "Specialized conformance check for the LegalTech dimension: verify coverage of GDPR, eIDAS, NIS2, Attorney-Client Privilege, Smart Legal Contracts concepts. Identify missing regulatory concepts in Δ.",
            "inputs":  ["LegalTech cluster from P1", "R from P2"],
            "outputs": ["LegalTech coverage score", "Missing regulatory refs", "Compliance risk map"],
            "api":     "/api/validation → dimensions[key=LEGALTECH]",
            "academic_ref": "EU GDPR (2016/679) · eIDAS (910/2014) · NIS2 Directive (2022/2555)"
        },
        {
            "id": "P5",
            "name": "Multi-Dimensional Gap Analysis",
            "abbrev": "MDGA",
            "color": "#ffc947",
            "description": "Aggregate all 9 dimension scores into overall_onto and overall_dt. Rank dimensions by δ(d) to identify priority remediation targets. Generate radar chart (ontology vs DT) and GAP bar chart.",
            "inputs":  ["All δ(d) from P3 and P4"],
            "outputs": ["Radar dataset", "GAP rankings top-3", "Overall maturity score", "Remediation recommendations"],
            "api":     "/api/validation → overall_*, top_gaps",
            "academic_ref": "Zachman (1987) A Framework for Information Systems Architecture — adapted for multi-layer gap analysis"
        }
    ],
    "validation_properties": [
        {
            "property": "Determinism",
            "guarantee": "Given identical Ω and Δ, the methodology always produces the same scores. No stochastic components.",
            "test": "pytest evaluation/test_scoring.py — all assertions use exact float comparisons"
        },
        {
            "property": "Monotonicity",
            "guarantee": "Adding services that cover new maltg_refs never decreases any score. δ(d) is non-negative by construction.",
            "test": "Sensitivity test: add lt_court_api coverage → Interop score increases, others unchanged"
        },
        {
            "property": "Completeness",
            "guarantee": "Every OWL class with a maltg:score annotation contributes to exactly one dimension's onto_score.",
            "test": "Coverage assertion: sum of |scored_nodes per dimension| == total scored OWL classes"
        },
        {
            "property": "Boundedness",
            "guarantee": "All scores ∈ [0, 100]. Coverage Ψ ∈ [0.0, 1.0]. Gap δ ∈ [0, onto_score].",
            "test": "Boundary test: empty dt_arch → all dt_scores = 0; full coverage → dt_score = onto_score"
        }
    ]
}


# ─── Helpers ──────────────────────────────────────────────────────────────────
def local_name(uri):
    if not uri: return ""
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]

def file_hash(path):
    try: return hashlib.md5(path.read_bytes()).hexdigest()
    except: return ""

def safe_int(v, d=0):
    try: return int(str(v).strip())
    except: return d


# ─── OWL Parser ───────────────────────────────────────────────────────────────
def parse_owl():
    if not OWL_PATH.exists():
        return {"error": f"OWL not found: {OWL_PATH}", "nodes": [], "links": [], "hash": ""}
    try:
        root = ET.parse(OWL_PATH).getroot()
    except ET.ParseError as e:
        return {"error": f"XML error: {e}", "nodes": [], "links": [], "hash": ""}

    nodes, links, seen = [], [], set()

    for cls in root.findall(f"{{{OWL_NS}}}Class"):
        uri = cls.get(f"{{{RDF_NS}}}about") or cls.get(f"{{{RDF_NS}}}ID")
        if not uri: continue
        nid = local_name(uri)
        if nid in seen: continue
        seen.add(nid)

        def g(tag):
            el = cls.find(tag)
            return (el.text or "").strip() if el is not None else ""

        reg = g(f"{{{MALTG_NS}}}regulation")
        nodes.append({
            "id":          nid,
            "label":       g(f"{{{RDFS_NS}}}label") or nid.replace("_"," "),
            "type":        g(f"{{{MALTG_NS}}}layer") or "default",
            "r":           safe_int(g(f"{{{MALTG_NS}}}radius"), 10),
            "description": g(f"{{{MALTG_NS}}}description"),
            "score":       g(f"{{{MALTG_NS}}}score"),
            "regulation":  reg,
            "uri":         uri,
        })
        for sc in cls.findall(f"{{{RDFS_NS}}}subClassOf"):
            p = sc.get(f"{{{RDF_NS}}}resource")
            if p:
                links.append({"s": local_name(p), "t": nid, "type": "subClassOf", "w": 1.2, "dash": False})

    for prop in root.findall(f"{{{OWL_NS}}}ObjectProperty"):
        uri = prop.get(f"{{{RDF_NS}}}about")
        if not uri: continue
        d_el = prop.find(f"{{{RDFS_NS}}}domain")
        r_el = prop.find(f"{{{RDFS_NS}}}range")
        w_el = prop.find(f"{{{MALTG_NS}}}weight")
        if d_el is None or r_el is None: continue
        src = local_name(d_el.get(f"{{{RDF_NS}}}resource",""))
        tgt = local_name(r_el.get(f"{{{RDF_NS}}}resource",""))
        w   = float(w_el.text) if w_el is not None and w_el.text else 1.5
        if src and tgt:
            links.append({"s": src, "t": tgt, "type": local_name(uri), "w": w, "dash": True})

    return {"nodes": nodes, "links": links, "hash": file_hash(OWL_PATH),
            "node_count": len(nodes), "link_count": len(links)}


# ─── DT Parser ────────────────────────────────────────────────────────────────
def parse_dt():
    if not DT_PATH.exists():
        return {"error": f"dt_arch.json not found: {DT_PATH}"}
    try:
        data = json.loads(DT_PATH.read_text(encoding="utf-8"))
        data["hash"] = file_hash(DT_PATH)
        return data
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}"}


# ─── Procedural Workflow Parser (BPMN JointJS) ────────────────────────────────
def _is_bpmn_file(path):
    """Cheap sniff: does the file contain a JointJS BPMN diagram?"""
    try:
        with path.open("rb") as fh:
            head = fh.read(200000).decode("utf-8-sig", errors="ignore")
        return '"bpmn"' in head
    except Exception:
        return False

def list_workflow_files():
    """List candidate BPMN workflow JSON files available in /data/workflow."""
    files = []
    if WF_DIR.exists():
        for p in sorted(WF_DIR.glob("*.json")):
            if _is_bpmn_file(p):
                files.append({"file": p.name, "label": p.stem})
    default = files[0]["file"] if files else ""
    # prefer a SUMARIO file as default when present
    for f in files:
        if "SUMARIO" in f["file"].upper():
            default = f["file"]; break
    return {"files": files, "default": default}

def _resolve_wf_path(file):
    """Safely resolve a requested workflow filename inside WF_DIR (no traversal)."""
    if not file:
        lst = list_workflow_files()
        file = lst["default"]
        if not file:
            return None
    name = Path(file).name           # strip any directory component
    cand = (WF_DIR / name).resolve()
    if cand.parent != WF_DIR.resolve() or not cand.exists():
        return None
    return cand

def _wf_rows(raw):
    """
    A workflow file may hold ONE or MANY tab-separated DB rows (one per line):
        codigo \\t nombre \\t <BPMN JointJS JSON> \\t ...metadata...
    Returns a list of {codigo, nombre, bpmn} for every line that carries a BPMN
    diagram in its 3rd column.
    """
    rows = []
    for ln in raw.split("\n"):
        if not ln.strip():
            continue
        cols = ln.split("\t")
        if len(cols) >= 3:
            c = cols[2].strip()
            if c.startswith("{") and '"bpmn"' in c[:120]:
                rows.append({"codigo": cols[0].strip(),
                             "nombre": cols[1].strip(),
                             "bpmn":   c})
    return rows

def _flow_label(cell):
    labs = cell.get("labels") or []
    if not labs:
        return ""
    return (labs[0].get("attrs", {}).get("text", {}).get("text", "") or "").strip()

def _stage_of(node, groups):
    """
    Etapas are 2-D regions (the dashed BPMN group boxes). A node belongs to a
    stage only when its centre falls INSIDE that group's rectangle. Nodes that
    sit outside every box (e.g. the bottom catalogue of activities) get no
    stage. Returns the group id or None.
    """
    if not groups:
        return None
    cx = node["x"] + node.get("w", 0) / 2.0
    cy = node["y"] + node.get("h", 0) / 2.0
    for g in groups:
        if g["x"] <= cx <= g["x"] + g["w"] and g["y"] <= cy <= g["y"] + g["h"]:
            return g["id"]
    return None

def parse_workflow(path=None, row=0):
    """
    A workflow file holds one or many tab-separated DB rows (one per line):
        codigo \\t nombre \\t <BPMN JointJS JSON> \\t ...metadata...
    The 3rd column holds a JointJS 'bpmn' diagram. We pick row ``row`` and
    normalise it into a procedural flow graph: nodes (activities/events),
    flows (edges), stages (Etapa swim-lanes) and annotations — discarding the
    heavy base64 templates. ``processes`` lists every flow available in the file
    so the client can offer a second selector.
    """
    if path is None:
        path = _resolve_wf_path("")
    if path is None or not path.exists():
        return {"error": f"workflow file not found: {path}"}
    try:
        raw = path.read_text(encoding="utf-8-sig")
    except Exception as e:
        return {"error": f"read error: {e}"}

    rows = _wf_rows(raw)
    if not rows:
        return {"error": "no BPMN diagram found in workflow file"}

    try:
        row = int(row)
    except (TypeError, ValueError):
        row = 0
    if row < 0 or row >= len(rows):
        row = 0
    sel = rows[row]

    try:
        diagram = json.loads(sel["bpmn"])
    except json.JSONDecodeError as e:
        return {"error": f"BPMN JSON error: {e}"}

    cells = diagram.get("cells", [])
    codigo, nombre = sel["codigo"], sel["nombre"]
    processes = [{"idx": i, "codigo": r["codigo"], "nombre": r["nombre"]} for i, r in enumerate(rows)]

    groups = []
    for c in cells:
        if c.get("type") == "bpmn.Group":
            p, s = c.get("position", {}), c.get("size", {})
            groups.append({
                "id":     c.get("id"),
                "label":  c.get("attrs", {}).get(".label", {}).get("text", "") or "",
                "numero": c.get("numeroEtapa", ""),
                "tipo":   c.get("tipoGrupo", ""),
                "x": p.get("x", 0), "y": p.get("y", 0),
                "w": s.get("width", 0), "h": s.get("height", 0),
            })
    groups.sort(key=lambda g: g["x"])

    nodes = []
    for c in cells:
        t = c.get("type")
        if t not in ("bpmn.Activity", "bpmn.Event"):
            continue
        p, s = c.get("position", {}), c.get("size", {})
        node = {
            "id":    c.get("id"),
            "kind":  "event" if t == "bpmn.Event" else "activity",
            "label": (c.get("content") or "").strip(),
            "x": p.get("x", 0), "y": p.get("y", 0),
            "w": s.get("width", 0), "h": s.get("height", 0),
            "eventType":     c.get("eventType", ""),
            "activityType":  c.get("activityType", ""),
            "actividad":     str(c.get("actividad", "")),
        }
        node["stage"] = _stage_of(node, groups)
        nodes.append(node)

    flows = []
    for c in cells:
        if c.get("type") != "bpmn.Flow":
            continue
        flows.append({
            "id":       c.get("id"),
            "source":   c.get("source", {}).get("id"),
            "target":   c.get("target", {}).get("id"),
            "label":    _flow_label(c),
            "flowType": c.get("flowType", "normal"),
            "vertices": c.get("vertices", []) or [],
        })

    annotations = []
    for c in cells:
        if c.get("type") != "bpmn.Annotation":
            continue
        p, s = c.get("position", {}), c.get("size", {})
        annotations.append({
            "id":      c.get("id"),
            "content": (c.get("content") or "").strip(),
            "x": p.get("x", 0), "y": p.get("y", 0),
            "w": s.get("width", 0), "h": s.get("height", 0),
        })

    # Bounding box for the front-end SVG viewBox
    xs, ys, xe, ye = [], [], [], []
    for coll in (nodes, groups, annotations):
        for c in coll:
            xs.append(c["x"]); ys.append(c["y"])
            xe.append(c["x"] + c["w"]); ye.append(c["y"] + c["h"])
    bbox = {
        "minX": min(xs) if xs else 0, "minY": min(ys) if ys else 0,
        "maxX": max(xe) if xe else 0, "maxY": max(ye) if ye else 0,
    }

    node_ids = {n["id"] for n in nodes}
    dangling = sum(1 for f in flows if f["source"] not in node_ids or f["target"] not in node_ids)

    return {
        "codigo": codigo,
        "nombre": nombre,
        "nodes": nodes,
        "flows": flows,
        "stages": groups,
        "annotations": annotations,
        "bbox": bbox,
        "stats": {
            "activities":  sum(1 for n in nodes if n["kind"] == "activity"),
            "events":      sum(1 for n in nodes if n["kind"] == "event"),
            "flows":       len(flows),
            "stages":      len(groups),
            "annotations": len(annotations),
            "dangling":    dangling,
        },
        "file":      path.name,
        "row":       row,
        "processes": processes,
        "hash":      file_hash(path),
    }


# ─── Hierarchical Coverage Ψ ──────────────────────────────────────────────────
def psi(svc_refs_set: set, dt_refs: list) -> float:
    """
    Ψ(d) = 0.4·𝟙[root_d ∈ R] + 0.6·(|sub_d ∩ R| / |sub_d|)
    """
    if not dt_refs: return 0.0
    root, subs = dt_refs[0], dt_refs[1:]
    root_ok    = 0.40 if root in svc_refs_set else 0.0
    sub_score  = 0.60 * (sum(1 for r in subs if r in svc_refs_set) / max(1, len(subs))) if subs \
                 else (0.60 if root in svc_refs_set else 0.0)
    return round(root_ok + sub_score, 4)


# ─── Validation Engine ────────────────────────────────────────────────────────
def compute_validation():
    onto = parse_owl()
    dt   = parse_dt()
    if "error" in onto: return {"error": onto["error"]}
    if "error" in dt:   return {"error": dt["error"]}

    nodes    = onto["nodes"]
    services = dt.get("services", [])
    links    = onto["links"]
    cross_n  = sum(1 for l in links if l.get("dash"))

    # Build coverage set R from all maltg_ref values (string OR list)
    R: set = set()
    for s in services:
        ref = s.get("maltg_ref","")
        if isinstance(ref, list): R.update(r for r in ref if r)
        elif ref: R.add(ref)

    results = []
    for dim in DIMENSIONS:
        key, owl_types, dt_refs = dim["key"], dim["owl_types"], dim["dt_refs"]

        scored = [n for n in nodes if n["type"] in owl_types and safe_int(n["score"]) > 0]

        if key == "INTEROP":
            od  = [n for n in nodes if n["type"]=="opendata"  and safe_int(n["score"])>0]
            sec = [n for n in nodes if n["type"]=="security"  and safe_int(n["score"])>0]
            od_avg  = sum(safe_int(n["score"]) for n in od)  / max(1,len(od))
            sec_avg = sum(safe_int(n["score"]) for n in sec) / max(1,len(sec))
            onto_score = round(od_avg*0.60 + sec_avg*0.30 + min(10.0, cross_n*1.25), 1)
        else:
            onto_score = round(sum(safe_int(n["score"]) for n in scored)/max(1,len(scored)),1) if scored else 0.0

        coverage   = psi(R, dt_refs)
        dt_score   = round(onto_score * coverage, 1)
        gap        = round(onto_score - dt_score, 1)

        covered_subs = [r for r in dt_refs[1:] if r in R]
        missing_subs = [r for r in dt_refs[1:] if r not in R]

        results.append({
            "key":          key,
            "label":        dim["label"],
            "bar_color":    dim["bar_color"],
            "onto_score":   onto_score,
            "dt_score":     dt_score,
            "coverage_pct": round(coverage*100, 1),
            "gap":          gap,
            "root_covered": (dt_refs[0] if dt_refs else "") in R,
            "covered_subs": covered_subs,
            "missing_subs": missing_subs,
            "owl_nodes":    len(scored),
        })

    onto_vals    = [r["onto_score"] for r in results]
    dt_vals      = [r["dt_score"]   for r in results]
    overall_onto = round(sum(onto_vals)/max(1,len(onto_vals)), 1)
    overall_dt   = round(sum(dt_vals)/max(1,len(dt_vals)),     1)
    overall_gap  = round(overall_onto - overall_dt, 1)
    gap_pct      = round((overall_gap / max(1, overall_onto))*100, 1)
    top_gaps     = sorted(results, key=lambda r: r["gap"], reverse=True)[:3]

    return {
        "dimensions":     results,
        "overall_onto":   overall_onto,
        "overall_dt":     overall_dt,
        "overall_gap":    overall_gap,
        "gap_pct":        gap_pct,
        "top_gaps":       [{"label":r["label"],"gap":r["gap"],"key":r["key"]} for r in top_gaps],
        "total_services": len(services),
        "cross_links":    cross_n,
        "legaltech_dim":  next((r for r in results if r["key"]=="LEGALTECH"), None),
        "owl_hash":       onto["hash"],
        "dt_hash":        dt.get("hash",""),
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/ontology",    summary="MALTG_onto.owl → D3 graph", tags=["MALTG Data"])
def get_ontology(): return parse_owl()

@app.get("/api/dt-arch",     summary="dt_arch.json with hash",    tags=["MALTG Data"])
def get_dt_arch():  return parse_dt()

@app.get("/api/validation",  summary="9-dim conformance scores",  tags=["MALTG Data"])
def get_validation(): return compute_validation()

@app.get("/api/methodology", summary="5-phase validation methodology + formal model", tags=["MALTG Data"])
def get_methodology():
    """
    Returns the formal MALTG validation methodology:
    MALTG = ⟨Ω, Δ, Γ, Ψ, δ⟩
    5 phases: ORE → DTSM → HCS → LDCC → MDGA
    """
    return METHODOLOGY

@app.get("/api/maltg",       summary="1_MALTG.json (JSON-LD architecture)", tags=["MALTG Data"])
def get_maltg():
    """Serves the multidimensional LegalTech governance architecture (JSON-LD)."""
    if not MALTG_PATH.exists():
        return {"error": f"1_MALTG.json not found: {MALTG_PATH}"}
    try:
        data = json.loads(MALTG_PATH.read_text(encoding="utf-8-sig"))
        data["hash"] = file_hash(MALTG_PATH)
        return data
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}"}

@app.get("/api/workflow-files", summary="List BPMN workflow JSON files in /data", tags=["MALTG Data"])
def get_workflow_files():
    """Returns the selectable BPMN workflow JSON files found in /data."""
    return list_workflow_files()

def _grafo_node(g):
    """From IdGrafoFlujoEstructura '<flujo>-<nodeUUID>' return the node UUID, or None."""
    if not g or str(g).upper() in ("NULL", "0", ""):
        return None
    g = str(g)
    return g.split("-", 1)[1] if "-" in g else g

def _grafo_flujo(g):
    """From IdGrafoFlujoEstructura return the flow number prefix (e.g. '141')."""
    if not g or str(g).upper() in ("NULL", "0", ""):
        return ""
    g = str(g)
    return g.split("-", 1)[0] if "-" in g else ""

def _causa_flujo(d):
    for a in (d.get("actividades") or []):
        fl = _grafo_flujo(a.get("IdGrafoFlujoEstructura"))
        if fl:
            return fl
    return ""

def _causa_label(d, fallback):
    """Build 'Nroflujo - nroCausa - Tipo'  e.g.  141 - 07333202200763 - INQUILINATO."""
    cab = d.get("cabecera", {}) if isinstance(d, dict) else {}
    juicio = (d.get("juicio") if isinstance(d, dict) else "") or fallback
    flujo = _causa_flujo(d)
    tipo = cab.get("Materia") or cab.get("Tipo Accion") or cab.get("Delito") or ""
    parts = [p for p in (flujo, juicio, tipo) if p]
    return " - ".join(parts), juicio

@app.get("/api/expedientes", summary="List case (causa) JSON files in /data/LegalCase", tags=["MALTG Data"])
def get_expedientes():
    """Lists the decided-case JSON files (causas/juicios) available for overlay."""
    files = []
    if EXP_DIR.exists():
        for p in sorted(EXP_DIR.glob("*.json")):
            try:
                d = json.loads(p.read_text(encoding="utf-8-sig"))
                label, juicio = _causa_label(d, p.stem)
            except Exception:
                label, juicio = p.stem, p.stem
            files.append({"file": p.name, "label": label, "juicio": juicio})
    return {"files": files}

@app.get("/api/expediente", summary="A case (causa) with the flow nodes it traversed", tags=["MALTG Data"])
def get_expediente(file: str = ""):
    """
    Returns a decided case (causa/juicio) enriched for the interactive analysis:
      • ``pasos``    – activities ordered chronologically by FechaProvidencia, each
                       with a 1-based ``seq`` and the resolved ``nodeId``.
      • ``nodeRefs`` – unique BPMN node ids traversed (for highlighting).
    """
    name = Path(file).name
    cand = (EXP_DIR / name).resolve()
    if not name or cand.parent != EXP_DIR.resolve() or not cand.exists():
        return {"error": f"invalid or unknown case file: {file}"}
    try:
        data = json.loads(cand.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}"}

    acts = data.get("actividades") or []
    ordered = sorted(acts, key=lambda a: str(a.get("FechaProvidencia") or ""))
    pasos, refs, seen = [], [], set()
    for i, a in enumerate(ordered, 1):
        node = _grafo_node(a.get("IdGrafoFlujoEstructura"))
        paso = dict(a)
        paso["seq"] = i
        paso["nodeId"] = node
        pasos.append(paso)
        if node and node not in seen:
            seen.add(node); refs.append(node)

    label, juicio = _causa_label(data, name)
    data["pasos"]    = pasos
    data["nodeRefs"] = refs
    data["flujo"]    = _causa_flujo(data)
    data["label"]    = label
    data["file"]     = name
    return data

@app.get("/api/workflow",    summary="BPMN workflow JSON → procedural flow graph", tags=["MALTG Data"])
def get_workflow(file: str = "", row: int = 0):
    """
    Parses a COGEP BPMN diagram from /data/workflow (default = first/SUMARIO file,
    or ?file=NAME) and returns a normalised procedural flow graph. Files may hold
    several processes; ?row=N selects which one, and ``processes`` lists them all.
    """
    path = _resolve_wf_path(file)
    if path is None:
        return {"error": f"invalid or unknown workflow file: {file}"}
    return parse_workflow(path, row)

@app.get("/api/health",      summary="Health check",              tags=["System"])
def health():
    return {"status":"ok","version":"3.0.0",
            "owl_exists":OWL_PATH.exists(),"dt_exists":DT_PATH.exists(),
            "owl_hash":file_hash(OWL_PATH),"dt_hash":file_hash(DT_PATH),
            "cogep_kb_exists":KB_PATH.exists()}


# ═══════════════════════════════════════════════════════════════════
#  COGEP KNOWLEDGE BASE + RAZONADOR JURÍDICO SIMBÓLICO
#  "IA entrenada con el COGEP": razonamiento determinista y explicable
#  sobre la ontología procesal (data/cogep_kb.json).
# ═══════════════════════════════════════════════════════════════════
from datetime import datetime, timedelta, date

KB_PATH = DATA_DIR / "cogep_kb.json"

def load_kb():
    if not KB_PATH.exists():
        return {"error": f"cogep_kb.json not found: {KB_PATH}"}
    try:
        return json.loads(KB_PATH.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}"}

def _parse_dt_str(s):
    s = str(s or "").strip()
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try: return datetime.strptime(s[:26], fmt)
        except ValueError: continue
    return None

def business_days(d1: datetime, d2: datetime) -> int:
    """Días hábiles transcurridos (Art. 73 COGEP — excluye sáb/dom; no feriados)."""
    if not d1 or not d2 or d2 <= d1: return 0
    days, cur = 0, d1.date()
    while cur < d2.date():
        cur += timedelta(days=1)
        if cur.weekday() < 5: days += 1
    return days

def _match_acto(kb, nombre, tipo=""):
    txt = f"{nombre or ''} {tipo or ''}".upper()
    for acto in kb.get("actos", []):
        for kw in acto.get("keywords", []):
            if kw.upper() in txt:
                return acto
    return None

def _detect_procedimiento(kb, data):
    flujo = _causa_flujo(data)
    tipo  = str((data.get("cabecera") or {}).get("Tipo Accion") or "").upper()
    for p in kb.get("procedimientos", []):
        if flujo and p.get("flujo") == flujo: return p
    for p in kb.get("procedimientos", []):
        if p["id"] in tipo: return p
    return kb.get("procedimientos", [{}])[0]

def _verdict(dias, termino, umbrales):
    inc = umbrales.get("incumple_factor", 1.25)
    if dias <= termino:            return "CUMPLE"
    if dias <= termino * inc:      return "ALERTA"
    return "INCUMPLE"

def _dictamen_regla(regla, estado, dias, desde_fecha, hasta_fecha, juez=""):
    t   = regla["termino_dias"]
    exc = max(0, dias - t)
    quien = f" La actuación corresponde a {juez}." if juez else ""
    base = (f"Conforme al {regla['articulo']} COGEP — “{regla['texto_norma']}” — "
            f"el término es de {t} días hábiles. Entre el {desde_fecha:%d-%m-%Y} y el "
            f"{hasta_fecha:%d-%m-%Y} transcurrieron {dias} días hábiles.")
    if estado == "CUMPLE":
        return base + f" DICTAMEN: la actuación se realizó DENTRO del término legal.{quien}"
    if estado == "ALERTA":
        return base + (f" DICTAMEN: el término se excedió en {exc} día(s) hábil(es) — desviación leve "
                       f"que amerita observación de gestión.{quien}")
    return base + (f" DICTAMEN: INCUMPLIMIENTO del término legal por {exc} día(s) hábil(es). "
                   f"Art. 93 COGEP: el incumplimiento del término será sancionado conforme con la ley.{quien}")

def razonar_expediente(data):
    """Motor de reglas: evalúa cada término COGEP sobre las actividades reales."""
    kb = load_kb()
    if "error" in kb: return kb
    umbrales = kb.get("umbrales", {})
    proc = _detect_procedimiento(kb, data)

    acts = data.get("actividades") or []
    ordered = sorted(acts, key=lambda a: str(a.get("FechaProvidencia") or ""))

    # primera ocurrencia de cada acto procesal
    primera, pasos_eval = {}, []
    for a in ordered:
        acto = _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))
        fecha = _parse_dt_str(a.get("FechaProvidencia"))
        node  = _grafo_node(a.get("IdGrafoFlujoEstructura"))
        pasos_eval.append({"actividad": a.get("NombreProvidencia"), "fecha": str(a.get("FechaProvidencia") or ""),
                           "acto": acto["id"] if acto else None, "nodeId": node,
                           "juez": a.get("Login") or ""})
        if acto and fecha and acto["id"] not in primera:
            primera[acto["id"]] = {"fecha": fecha, "node": node, "juez": a.get("Login") or "",
                                   "actividad": a.get("NombreProvidencia")}
    # fallback: recepción = FechaIngreso de la cabecera
    fi = _parse_dt_str((data.get("cabecera") or {}).get("FechaIngreso"))
    if "act_recepcion" not in primera and fi:
        primera["act_recepcion"] = {"fecha": fi, "node": None, "juez": "", "actividad": "Ingreso de la causa"}

    resultados, node_alerts = [], {}
    for regla in kb.get("reglas", []):
        if proc.get("id") not in regla.get("procedimientos", []): continue
        d, h = primera.get(regla["acto_desde"]), primera.get(regla["acto_hasta"])
        if not d or not h or h["fecha"] <= d["fecha"]:
            resultados.append({"regla": regla["id"], "nombre": regla["nombre"], "articulo": regla["articulo"],
                               "estado": "NO_EVALUABLE", "termino_dias": regla["termino_dias"],
                               "dias": None, "exceso": 0, "indicador": regla.get("indicador", False),
                               "dictamen": "No constan en el expediente ambos actos procesales necesarios para evaluar este término."})
            continue
        dias   = business_days(d["fecha"], h["fecha"])
        estado = _verdict(dias, regla["termino_dias"], umbrales)
        res = {"regla": regla["id"], "nombre": regla["nombre"], "articulo": regla["articulo"],
               "estado": estado, "dias": dias, "termino_dias": regla["termino_dias"],
               "exceso": max(0, dias - regla["termino_dias"]),
               "indicador": regla.get("indicador", False),
               "acto_desde": regla["acto_desde"], "acto_hasta": regla["acto_hasta"],
               "desde_fecha": d["fecha"].strftime("%Y-%m-%d"), "hasta_fecha": h["fecha"].strftime("%Y-%m-%d"),
               "actividad": h["actividad"], "nodeId": h["node"], "juez": h["juez"],
               "dictamen": _dictamen_regla(regla, estado, dias, d["fecha"], h["fecha"], h["juez"])}
        resultados.append(res)
        if h["node"]:
            prev = node_alerts.get(h["node"])
            if not prev or ["CUMPLE","ALERTA","INCUMPLE"].index(estado) > ["CUMPLE","ALERTA","INCUMPLE"].index(prev["estado"]):
                node_alerts[h["node"]] = {"estado": estado, "exceso": res["exceso"],
                                          "regla": regla["id"], "articulo": regla["articulo"]}

    evaluadas = [r for r in resultados if r["estado"] != "NO_EVALUABLE"]
    pts = {"CUMPLE": 100, "ALERTA": 60, "INCUMPLE": 0}
    salud = round(sum(pts[r["estado"]] for r in evaluadas) / max(1, len(evaluadas)), 1) if evaluadas else None
    n_inc = sum(1 for r in evaluadas if r["estado"] == "INCUMPLE")
    n_ale = sum(1 for r in evaluadas if r["estado"] == "ALERTA")

    if salud is None:
        resumen = "El expediente no contiene actos procesales suficientes para un dictamen de términos."
    elif salud >= 90:
        resumen = (f"Salud procesal {salud}/100 — EXCELENTE. {len(evaluadas)} término(s) evaluado(s): "
                   f"la tramitación respeta los términos del COGEP.")
    elif salud >= 60:
        resumen = (f"Salud procesal {salud}/100 — ACEPTABLE CON OBSERVACIONES. "
                   f"{n_ale} alerta(s) y {n_inc} incumplimiento(s) sobre {len(evaluadas)} término(s) evaluado(s).")
    else:
        resumen = (f"Salud procesal {salud}/100 — DEFICIENTE. {n_inc} incumplimiento(s) de término legal "
                   f"sobre {len(evaluadas)} evaluado(s); amerita revisión disciplinaria de gestión (Art. 93 COGEP).")

    return {"juicio": data.get("juicio"), "label": data.get("label", ""),
            "procedimiento": {"id": proc.get("id"), "nombre": proc.get("nombre"), "articulos": proc.get("articulos")},
            "salud": salud, "resumen": resumen,
            "evaluadas": len(evaluadas), "cumple": sum(1 for r in evaluadas if r["estado"]=="CUMPLE"),
            "alertas": n_ale, "incumplimientos": n_inc,
            "resultados": resultados, "node_alerts": node_alerts,
            "motor": "Razonador simbólico COGEP v1.0 — determinista y explicable (cogep_kb.json)",
            "kb_hash": file_hash(KB_PATH)}


@app.get("/api/cogep/kb", summary="Base de conocimiento COGEP (cruda)", tags=["COGEP IA"])
def get_cogep_kb():
    return load_kb()

@app.get("/api/cogep/ontology", summary="Ontología COGEP → grafo D3", tags=["COGEP IA"])
def get_cogep_ontology():
    """Convierte cogep_kb.json en un grafo (procedimiento→etapa→acto→término→artículo)."""
    kb = load_kb()
    if "error" in kb: return kb
    nodes, links, seen = [], [], set()
    def add(nid, label, tipo, r=10, info=""):
        if nid in seen: return
        seen.add(nid); nodes.append({"id": nid, "label": label, "type": tipo, "r": r, "description": info})
    add("COGEP", "COGEP", "core", 26, "Código Orgánico General de Procesos — Ecuador")
    for s in kb.get("sujetos", []):
        add(s["id"], s["nombre"], "sujeto", 11, s.get("rol",""))
        links.append({"s": "COGEP", "t": s["id"], "type": "define", "w": 1.0, "dash": True})
    for pr in kb.get("principios", []):
        add(pr["id"], pr["nombre"], "principio", 9, pr.get("articulo",""))
        links.append({"s": "COGEP", "t": pr["id"], "type": "rige", "w": 1.0, "dash": True})
    actos = {a["id"]: a for a in kb.get("actos", [])}
    for p in kb.get("procedimientos", []):
        add(p["id"], p["nombre"], "procedimiento", 18, p.get("articulos",""))
        links.append({"s": "COGEP", "t": p["id"], "type": "subClassOf", "w": 1.4, "dash": False})
        for e in p.get("etapas", []):
            add(e["id"], e["nombre"], "etapa", 13, f"Etapa de {p['nombre']}")
            links.append({"s": p["id"], "t": e["id"], "type": "tieneEtapa", "w": 1.2, "dash": False})
            for aid in e.get("actos", []):
                a = actos.get(aid)
                if not a: continue
                add(aid, a["nombre"], "acto", 10, a.get("articulo",""))
                links.append({"s": e["id"], "t": aid, "type": "contieneActo", "w": 1.0, "dash": False})
                if a.get("sujeto"):
                    links.append({"s": aid, "t": a["sujeto"], "type": "ejecutadoPor", "w": 0.8, "dash": True})
    for r in kb.get("reglas", []):
        tid = "T_" + r["id"]
        add(tid, f"{r['termino_dias']} días — {r['articulo']}", "termino", 8, r["texto_norma"])
        links.append({"s": r["acto_hasta"], "t": tid, "type": "sujetoATermino", "w": 1.0, "dash": True})
        links.append({"s": tid, "t": r["acto_desde"], "type": "computaDesde", "w": 0.7, "dash": True})
    return {"nodes": nodes, "links": links, "node_count": len(nodes), "link_count": len(links),
            "hash": file_hash(KB_PATH), "meta": kb.get("meta", {})}

@app.get("/api/cogep/juicio", summary="Juicio de valor IA sobre un expediente", tags=["COGEP IA"])
def get_cogep_juicio(file: str = ""):
    name = Path(file).name
    cand = (EXP_DIR / name).resolve()
    if not name or cand.parent != EXP_DIR.resolve() or not cand.exists():
        return {"error": f"invalid or unknown case file: {file}"}
    try:
        data = json.loads(cand.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}"}
    label, _ = _causa_label(data, name)
    data["label"] = label
    return razonar_expediente(data)


# ─── Juicio de valor sobre PDF de una actuación ──────────────────────────────
_MESES = {"enero":1,"febrero":2,"marzo":3,"abril":4,"mayo":5,"junio":6,"julio":7,
          "agosto":8,"septiembre":9,"setiembre":9,"octubre":10,"noviembre":11,"diciembre":12}

def _extract_dates(text):
    import re
    out = []
    for m in re.finditer(r"(\d{4})-(\d{2})-(\d{2})", text):
        try: out.append(datetime(int(m[1]), int(m[2]), int(m[3])))
        except ValueError: pass
    for m in re.finditer(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", text):
        try: out.append(datetime(int(m[3]), int(m[2]), int(m[1])))
        except ValueError: pass
    for m in re.finditer(r"(\d{1,2})\s+de\s+([a-záéíóu]+)\s+(?:de(?:l)?\s+)?(\d{4})", text, re.I):
        mes = _MESES.get(m[2].lower())
        if mes:
            try: out.append(datetime(int(m[3]), mes, int(m[1])))
            except ValueError: pass
    return sorted({d for d in out if 2000 <= d.year <= 2035})

def _pdf_text_fallback(raw: bytes) -> str:
    """Extractor PDF de respaldo (sin dependencias): descomprime streams Flate y
    lee operadores de texto Tj/TJ. Cubre PDFs de texto simples; los PDF con
    fuentes CID/escaneados requieren pypdf u OCR."""
    import zlib, re
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        data = m.group(1)
        try:
            data = zlib.decompress(data)
        except Exception:
            pass
        try:
            txt = data.decode("latin-1", errors="ignore")
        except Exception:
            continue
        if "BT" not in txt and "Tj" not in txt and "TJ" not in txt:
            continue
        for tm in re.finditer(r"\((?:\\.|[^()\\])*\)\s*Tj|\[[^\[\]]*\]\s*TJ", txt):
            for ptxt in re.findall(r"\((?:\\.|[^()\\])*\)", tm.group(0)):
                t = ptxt[1:-1]
                t = re.sub(r"\\([()\\])", r"\1", t)
                t = re.sub(r"\\(\d{1,3})", lambda mm: chr(int(mm.group(1), 8)), t)
                out.append(t)
            out.append(" ")
        out.append("\n")
    return "".join(out)

def _doc_to_text(filename: str, raw: bytes) -> str:
    """PDF → texto: pypdf si está instalado; si no, extractor de respaldo. TXT directo."""
    if (filename or "").lower().endswith(".pdf") or raw[:4] == b"%PDF":
        try:
            from pypdf import PdfReader
            import io
            rd = PdfReader(io.BytesIO(raw))
            t = "\n".join((pg.extract_text() or "") for pg in rd.pages[:30])
            if t.strip():
                return t
        except Exception:
            pass
        return _pdf_text_fallback(raw)
    return raw.decode("utf-8", errors="ignore")

from fastapi import UploadFile, File as FFile

@app.post("/api/cogep/juicio-pdf", summary="Juicio de valor IA sobre el PDF de una actuación", tags=["COGEP IA"])
async def post_cogep_juicio_pdf(file: UploadFile = FFile(...)):
    """
    Recibe el PDF (o .txt) del contenido de una actividad procesal, identifica el acto,
    extrae las fechas y dictamina contra los términos del COGEP (razonador simbólico).
    """
    kb = load_kb()
    if "error" in kb: return kb
    raw = await file.read()
    text = _doc_to_text(file.filename or "", raw)
    if not text.strip():
        return {"error": "El documento no contiene texto extraíble (¿PDF escaneado sin OCR?). Para PDFs complejos instale pypdf y reconstruya la imagen."}

    up   = text.upper()
    acto = _match_acto(kb, up, "")
    fechas = _extract_dates(text)
    juez = ""
    import re as _re
    mj = _re.search(r"(?:JUEZA?|JUZGADORA?)[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,3})", text)
    if mj: juez = mj[1].strip()

    hallazgos = {"acto_detectado": acto["nombre"] if acto else None,
                 "acto_id": acto["id"] if acto else None,
                 "articulo_acto": acto.get("articulo") if acto else None,
                 "fechas_detectadas": [d.strftime("%Y-%m-%d") for d in fechas],
                 "juez_detectado": juez or None,
                 "caracteres_analizados": len(text)}

    if not acto:
        return {**hallazgos, "estado": "NO_EVALUABLE",
                "dictamen": ("El razonador no pudo asociar el documento a un acto procesal de la ontología COGEP. "
                             "Verifique que el PDF corresponda a una providencia (calificación, citación, contestación, "
                             "audiencia, sentencia, apelación, ejecución).")}

    reglas = [r for r in kb.get("reglas", []) if r["acto_hasta"] == acto["id"]]
    if not reglas or len(fechas) < 2:
        return {**hallazgos, "estado": "INFORMATIVO",
                "dictamen": (f"Acto identificado: {acto['nombre']} ({acto.get('articulo','')}). "
                             + ("No existe término COGEP parametrizado para este acto. " if not reglas else
                                "Se requieren al menos dos fechas en el documento (acto de referencia y actuación) para computar el término. ")
                             + "Dictamen de fondo no emitido.")}

    regla = reglas[0]
    d1, d2 = fechas[0], fechas[-1]
    dias = business_days(d1, d2)
    estado = _verdict(dias, regla["termino_dias"], kb.get("umbrales", {}))
    return {**hallazgos, "estado": estado, "regla": regla["id"], "articulo": regla["articulo"],
            "dias": dias, "termino_dias": regla["termino_dias"], "exceso": max(0, dias - regla["termino_dias"]),
            "dictamen": _dictamen_regla(regla, estado, dias, d1, d2, juez),
            "motor": "Razonador simbólico COGEP v1.0 — análisis documental"}


# ─── AGENTE DE ANÁLISIS DE ACTUACIONES: errores jurídicos en el documento ────
def _snippet(text, kws, width=90):
    """Devuelve un fragmento del documento alrededor de la primera keyword hallada."""
    nt = _norm_txt(text)
    for k in kws:
        i = nt.find(_norm_txt(k))
        if i >= 0:
            a, b = max(0, i - 20), min(len(text), i + width)
            return "…" + text[a:b].replace("\n", " ").strip() + "…"
    return ""

def analizar_actuacion(text: str, acto_id: str = "", expediente: str = ""):
    """
    Agente documental del razonador COGEP:
      1. identifica (o valida) el acto procesal del documento,
      2. verifica los requisitos legales del acto (ontología cogep_kb.json),
      3. controla elementos formales genéricos (fechas, juzgador, nro. de causa),
      4. evalúa el término legal si hay fechas computables,
      5. emite hallazgos tipificados (ERROR | ADVERTENCIA | CUMPLE) con artículo y evidencia.
    """
    kb = load_kb()
    if "error" in kb: return kb
    nt = _norm_txt(text)
    actos = {a["id"]: a for a in kb.get("actos", [])}

    detectado = _match_acto(kb, text.upper(), "")
    acto = actos.get(acto_id) or detectado
    hallazgos = []

    if not acto:
        return {"estado": "NO_EVALUABLE", "hallazgos": [],
                "dictamen": ("El agente no pudo asociar el documento a ningún acto procesal de la ontología COGEP. "
                             "Seleccione el acto manualmente o verifique que el PDF contenga texto extraíble.")}

    # 0) correspondencia acto seleccionado vs detectado
    if acto_id and detectado and detectado["id"] != acto_id:
        hallazgos.append({"tipo": "ADVERTENCIA", "articulo": detectado.get("articulo", ""),
                          "requisito": "Correspondencia del documento",
                          "detalle": f"Usted seleccionó «{acto['nombre']}», pero el texto sugiere «{detectado['nombre']}». El análisis se hace sobre el acto seleccionado.",
                          "evidencia": "", "recomendacion": "Confirme que el PDF corresponde a la actividad elegida."})

    # 1) elementos formales genéricos
    import re as _re
    fechas = _extract_dates(text)
    mj = _re.search(r"(?:JUEZA?|JUZGADORA?|DRA?\.)[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ]+){1,3})", text)
    juez = mj[1].strip() if mj else ""
    mc = _re.search(r"\b(\d{5}[-\s]?\d{4}[-\s]?\d{5}|\d{14,17})\b", text)
    causa_doc = (mc[1].replace("-", "").replace(" ", "") if mc else "")

    if fechas:
        hallazgos.append({"tipo": "CUMPLE", "articulo": "Art. 90.2", "requisito": "Fecha del pronunciamiento",
                          "detalle": f"Fecha(s) identificada(s): {', '.join(d.strftime('%d-%m-%Y') for d in fechas[:4])}.",
                          "evidencia": "", "recomendacion": ""})
    else:
        hallazgos.append({"tipo": "ERROR", "articulo": "Art. 90.2", "requisito": "Fecha del pronunciamiento",
                          "detalle": "No se identificó ninguna fecha en el documento; todo pronunciamiento escrito debe contener la fecha de expedición.",
                          "evidencia": "", "recomendacion": "Verifique que el documento esté completo y sea legible."})
    hallazgos.append({"tipo": "CUMPLE" if juez else "ADVERTENCIA", "articulo": "Art. 90.1 / 95.1",
                      "requisito": "Identificación del juzgador",
                      "detalle": (f"Juzgador identificado: {juez}." if juez else "No se identificó al juzgador responsable en el texto."),
                      "evidencia": "", "recomendacion": "" if juez else "El pronunciamiento debe identificar a quien lo expide."})
    if expediente:
        exp_num = "".join(ch for ch in Path(expediente).stem if ch.isdigit())
        if causa_doc and exp_num and causa_doc != exp_num:
            hallazgos.append({"tipo": "ERROR", "articulo": "—", "requisito": "Identidad de la causa",
                              "detalle": f"El documento refiere la causa {causa_doc}, pero la causa cargada es {exp_num}: posible documento de otro proceso.",
                              "evidencia": "", "recomendacion": "Verifique el expediente correcto."})
        elif causa_doc:
            hallazgos.append({"tipo": "CUMPLE", "articulo": "—", "requisito": "Identidad de la causa",
                              "detalle": f"Número de causa del documento coincide: {causa_doc}.", "evidencia": "", "recomendacion": ""})

    # 2) requisitos legales específicos del acto (ontología)
    for req in acto.get("requisitos", []):
        kws = req.get("evidencia_any", [])
        ok = any(_norm_txt(k) in nt for k in kws)
        hallazgos.append({
            "tipo": "CUMPLE" if ok else req.get("severidad", "ADVERTENCIA"),
            "articulo": req.get("articulo", ""),
            "requisito": req.get("descripcion", req.get("id")),
            "detalle": ("Se encontró evidencia del cumplimiento en el documento." if ok else
                        f"No se encontró evidencia de este requisito en el documento ({req.get('articulo','')})."),
            "evidencia": _snippet(text, kws) if ok else "",
            "recomendacion": "" if ok else req.get("recomendacion", ""),
        })

    # 3) término legal (si hay al menos dos fechas)
    termino = None
    reglas = [r for r in kb.get("reglas", []) if r["acto_hasta"] == acto["id"]]
    if reglas and len(fechas) >= 2:
        regla = reglas[0]
        dias = business_days(fechas[0], fechas[-1])
        estado_t = _verdict(dias, regla["termino_dias"], kb.get("umbrales", {}))
        termino = {"regla": regla["id"], "articulo": regla["articulo"], "dias": dias,
                   "termino_dias": regla["termino_dias"], "estado": estado_t,
                   "exceso": max(0, dias - regla["termino_dias"])}
        hallazgos.append({"tipo": "CUMPLE" if estado_t == "CUMPLE" else ("ADVERTENCIA" if estado_t == "ALERTA" else "ERROR"),
                          "articulo": regla["articulo"], "requisito": f"Término legal — {regla['nombre']}",
                          "detalle": _dictamen_regla(regla, estado_t, dias, fechas[0], fechas[-1], juez),
                          "evidencia": "", "recomendacion": ""})

    # 4) dictamen global
    errores = sum(1 for h in hallazgos if h["tipo"] == "ERROR")
    advert  = sum(1 for h in hallazgos if h["tipo"] == "ADVERTENCIA")
    cumple  = sum(1 for h in hallazgos if h["tipo"] == "CUMPLE")
    evaluables = errores + advert + cumple
    conformidad = round(100 * cumple / max(1, evaluables), 1)
    nulidad = any(h["tipo"] == "ERROR" and "89" in h["articulo"] for h in hallazgos)

    if errores == 0 and advert == 0:
        dictamen = (f"La actuación «{acto['nombre']}» satisface los {cumple} controles del razonador "
                    f"({acto.get('articulo','')} COGEP): no se identificaron errores jurídicos en el documento.")
    elif errores == 0:
        dictamen = (f"La actuación «{acto['nombre']}» es sustancialmente conforme ({conformidad}%), con {advert} "
                    f"observación(es) de forma que se recomienda subsanar.")
    else:
        dictamen = (f"La actuación «{acto['nombre']}» presenta {errores} posible(s) ERROR(es) jurídico(s) y {advert} "
                    f"advertencia(s) — conformidad {conformidad}%. "
                    + ("ATENCIÓN: la omisión de motivación acarrea NULIDAD (Art. 89 COGEP). " if nulidad else "")
                    + "Revise los hallazgos: cada uno cita el artículo del COGEP aplicable.")

    return {"estado": "ANALIZADO",
            "acto": {"id": acto["id"], "nombre": acto["nombre"], "articulo": acto.get("articulo", "")},
            "acto_detectado": detectado["nombre"] if detectado else None,
            "juez": juez or None, "causa_documento": causa_doc or None,
            "fechas": [d.strftime("%Y-%m-%d") for d in fechas],
            "termino": termino,
            "conformidad": conformidad, "errores": errores, "advertencias": advert, "cumplidos": cumple,
            "hallazgos": hallazgos, "dictamen": dictamen,
            "motor": "Agente documental COGEP v1.0 — razonador simbólico sobre ontología (sin caja negra)",
            "caracteres_analizados": len(text)}

from fastapi import Form

@app.post("/api/cogep/analisis", summary="Análisis IA de una actuación judicial (PDF/TXT): errores jurídicos", tags=["COGEP IA"])
async def post_cogep_analisis(file: UploadFile = FFile(...), acto: str = Form(""), expediente: str = Form("")):
    """
    Recibe el documento de una actividad procesal + el acto seleccionado por el usuario.
    El agente lee el PDF, valida los requisitos legales del acto contra la ontología
    COGEP y devuelve los hallazgos (errores/advertencias) con artículo y evidencia.
    """
    raw = await file.read()
    text = _doc_to_text(file.filename or "", raw)
    if not text.strip():
        return {"error": ("El documento no contiene texto extraíble. Si es un PDF escaneado se requiere OCR; "
                          "si es un PDF con fuentes especiales, instale pypdf (requirements.txt) y reconstruya la imagen.")}
    try:
        return analizar_actuacion(text, acto_id=acto, expediente=expediente)
    except Exception as e:
        return {"error": f"Error del agente de análisis: {e}"}


# ─── BLOCKCHAIN demo: ledger de integridad del expediente ────────────────────
def _sha(s): return hashlib.sha256(s.encode("utf-8")).hexdigest()

@app.get("/api/ledger", summary="Hash-chain (DLT demo) de las actuaciones de una causa", tags=["Tecnologías"])
def get_ledger(file: str = ""):
    """
    Materialización Blockchain: cada actuación se encadena con SHA-256
    (block_hash = H(idx ‖ fecha ‖ data_hash ‖ prev_hash)). Alterar una actuación
    rompe todos los bloques posteriores — no-repudio del expediente.
    """
    name = Path(file).name
    cand = (EXP_DIR / name).resolve()
    if not name or cand.parent != EXP_DIR.resolve() or not cand.exists():
        return {"error": f"invalid or unknown case file: {file}"}
    data = json.loads(cand.read_text(encoding="utf-8-sig"))
    acts = sorted(data.get("actividades") or [], key=lambda a: str(a.get("FechaProvidencia") or ""))
    chain, prev = [], "0"*64
    for i, a in enumerate(acts):
        payload = json.dumps(a, sort_keys=True, ensure_ascii=False)
        dh = _sha(payload)
        bh = _sha(f"{i}|{a.get('FechaProvidencia','')}|{dh}|{prev}")
        chain.append({"idx": i, "fecha": str(a.get("FechaProvidencia") or ""),
                      "actividad": a.get("NombreProvidencia") or "", "tipo": a.get("TipoProvidencia") or "",
                      "data_hash": dh, "prev_hash": prev, "block_hash": bh})
        prev = bh
    return {"juicio": data.get("juicio"), "bloques": chain, "longitud": len(chain),
            "root": prev, "algoritmo": "SHA-256 hash-chain (notarización DLT simulada)",
            "valido": True}


# ─── OPEN DATA demo: expediente como JSON-LD / CSV + DCAT ────────────────────
@app.get("/api/opendata", summary="Expediente como dato abierto (JSON-LD / CSV + DCAT)", tags=["Tecnologías"])
def get_opendata(file: str = "", format: str = "jsonld"):
    name = Path(file).name
    cand = (EXP_DIR / name).resolve()
    if not name or cand.parent != EXP_DIR.resolve() or not cand.exists():
        return {"error": f"invalid or unknown case file: {file}"}
    data = json.loads(cand.read_text(encoding="utf-8-sig"))
    cab  = data.get("cabecera", {})
    acts = sorted(data.get("actividades") or [], key=lambda a: str(a.get("FechaProvidencia") or ""))

    if format == "csv":
        from fastapi.responses import PlainTextResponse
        lines = ["secuencia,fecha,tipo_providencia,nombre_providencia,judicatura"]
        for a in acts:
            lines.append(",".join('"'+str(a.get(k) or "").replace('"',"'")+'"' for k in
                ("Secuencia","FechaProvidencia","TipoProvidencia","NombreProvidencia","IdJudicatura")))
        return PlainTextResponse("\n".join(lines), media_type="text/csv")

    jsonld = {
        "@context": {"@vocab": "http://maltg.arch/onto#", "schema": "http://schema.org/",
                     "dct": "http://purl.org/dc/terms/", "dcat": "http://www.w3.org/ns/dcat#"},
        "@id": f"http://maltg.arch/expediente/{data.get('juicio','')}",
        "@type": "ExpedienteJudicial",
        "schema:identifier": data.get("juicio", ""),
        "schema:about": cab.get("Materia", ""),
        "dct:title": f"Proceso {cab.get('Tipo Accion','')} — {cab.get('Materia','')} — {data.get('juicio','')}",
        "schema:provider": cab.get("NombreJudicatura", ""),
        "dct:created": cab.get("FechaIngreso", ""),
        "estadoProcesal": cab.get("EstadoProcesal", ""),
        "dcat:landingPage": "https://procesosjudiciales.funcionjudicial.gob.ec/",
        "dct:license": "https://creativecommons.org/licenses/by/4.0/",
        "dct:conformsTo": "COGEP — Código Orgánico General de Procesos",
        "actuaciones": [{
            "@type": "schema:Action", "schema:position": a.get("Secuencia"),
            "schema:name": a.get("NombreProvidencia"), "schema:startTime": a.get("FechaProvidencia"),
            "tipoProvidencia": a.get("TipoProvidencia") or "", "judicatura": a.get("IdJudicatura")
        } for a in acts],
        "dcat:dataset": {"@type": "dcat:Dataset",
            "dct:publisher": "Consejo de la Judicatura — Ecuador",
            "dcat:keyword": ["justicia abierta", "COGEP", "expediente", "open data judicial"],
            "dct:format": ["application/ld+json", "text/csv"]}
    }
    return jsonld

# ═══════════════════════════════════════════════════════════════════
#  CHAT COGEP — preguntas en lenguaje natural sobre una causa
#  Mismo motor simbólico (KB + razonador): respuestas deterministas
#  y explicables, siempre con cita de artículo cuando aplica.
# ═══════════════════════════════════════════════════════════════════
import unicodedata
from pydantic import BaseModel

def _norm_txt(s):
    s = unicodedata.normalize("NFD", str(s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")

_CHAT_ACTOS = {
    "act_sentencia":    ["sentencia", "fallo", "resolvio", "resolucion final"],
    "act_audiencia":    ["audiencia"],
    "act_citacion":     ["citacion", "citaron", "citar", "cito"],
    "act_contestacion": ["contestacion", "contesto", "contestar"],
    "act_calificacion": ["calificacion", "califico", "admision", "admitio", "demanda"],
    "act_apelacion":    ["apelacion", "apelo", "recurso"],
    "act_mandamiento":  ["mandamiento", "ejecucion"],
    "act_embargo":      ["embargo", "apremio"],
    "act_notificacion": ["notificacion", "notifico"],
}

_EST_ICON = {"CUMPLE": "✅", "ALERTA": "🟡", "INCUMPLE": "🔴", "NO_EVALUABLE": "⚪"}

def _chat_load(file):
    name = Path(file).name
    cand = (EXP_DIR / name).resolve()
    if not name or cand.parent != EXP_DIR.resolve() or not cand.exists():
        return None
    data = json.loads(cand.read_text(encoding="utf-8-sig"))
    label, _ = _causa_label(data, name)
    data["label"] = label
    return data

def _fmt_regla(r, largo=False):
    ic = _EST_ICON.get(r["estado"], "•")
    dias = "" if r["dias"] is None else f" — {r['dias']}/{r['termino_dias']} días hábiles" + (f" (+{r['exceso']})" if r["exceso"] else "")
    linea = f"{ic} {r['nombre']} ({r['articulo']}): {r['estado']}{dias}"
    return linea + ("\n   " + r["dictamen"] if largo else "")

def cogep_chat_answer(file, question):
    q = _norm_txt(question)
    sug = []
    if not file:
        return {"answer": "Primero selecciona una causa en el selector «Causa / Expediente» del diagrama y vuelve a preguntarme.",
                "intent": "sin_causa", "sugerencias": []}
    data = _chat_load(file)
    if data is None:
        return {"answer": f"No pude abrir el expediente «{file}».", "intent": "error", "sugerencias": []}

    kb = load_kb()
    j  = razonar_expediente(data)
    cab = data.get("cabecera", {})
    acts = sorted(data.get("actividades") or [], key=lambda a: str(a.get("FechaProvidencia") or ""))
    res  = j.get("resultados", [])
    evaluadas = [r for r in res if r["estado"] != "NO_EVALUABLE"]
    hdr = f"📁 {data.get('label','')}\n"

    def has(*kws): return any(k in q for k in kws)

    # 1) saludo / ayuda
    if has("hola", "buenas", "ayuda", "que puedes", "que sabes", "como funciona") or not q.strip():
        return {"answer": (f"Hola 👋 Soy el asistente COGEP. Razono sobre la ontología procesal (cogep_kb.json) "
                           f"y las {len(acts)} actuaciones reales de la causa seleccionada.\n{hdr}"
                           "Puedo responderte sobre: salud procesal, plazos e incumplimientos, cada acto "
                           "(sentencia, audiencia, citación…), el juez que tramitó, artículos del COGEP, "
                           "el historial de actuaciones y la integridad blockchain del expediente."),
                "intent": "ayuda",
                "sugerencias": ["¿Cómo está la salud del juicio?", "¿Qué plazos se incumplieron?", "¿Cuándo fue la sentencia?", "¿Quién tramitó la causa?"]}

    # 2) salud / estado general
    if has("salud", "estado general", "como va", "como esta", "diagnostico", "evaluacion general"):
        det = "\n".join(_fmt_regla(r) for r in evaluadas) or "Sin términos evaluables."
        return {"answer": (f"{hdr}⚖ {j.get('resumen','')}\n\nProcedimiento: {j['procedimiento']['nombre']} "
                           f"({j['procedimiento']['articulos']})\n\n{det}"),
                "intent": "salud",
                "sugerencias": ["¿Qué plazos se incumplieron?", "Detalle de la sentencia", "¿La cadena de integridad es válida?"]}

    # 3) incumplimientos / alertas
    if has("incumpl", "atraso", "retraso", "alerta", "vencid", "fuera de plazo", "demora", "mora"):
        bad = [r for r in evaluadas if r["estado"] in ("INCUMPLE", "ALERTA")]
        if not bad:
            return {"answer": hdr + "✅ No se detectaron incumplimientos ni alertas: todos los términos COGEP evaluados se cumplieron.",
                    "intent": "incumplimientos", "sugerencias": ["¿Cómo está la salud del juicio?", "Historial de actuaciones"]}
        det = "\n\n".join(_fmt_regla(r, largo=True) for r in bad)
        return {"answer": f"{hdr}Se detectaron {len(bad)} término(s) con problemas:\n\n{det}",
                "intent": "incumplimientos",
                "sugerencias": ["¿Quién tramitó la causa?", "¿Qué dice el Art. 93?", "¿Cómo está la salud del juicio?"]}

    # 4) plazos / términos (vista completa)
    if has("plazo", "termino", "cumple", "tiempos"):
        det = "\n".join(_fmt_regla(r) for r in res)
        return {"answer": (f"{hdr}Evaluación de términos COGEP ({j['procedimiento']['nombre']}):\n\n{det}\n\n"
                           "Nota: términos en días hábiles (Art. 73 COGEP). Pregúntame por un acto concreto para ver el dictamen completo."),
                "intent": "plazos", "sugerencias": ["Detalle de la audiencia", "Detalle de la sentencia", "¿Qué plazos se incumplieron?"]}

    # 5) acto procesal concreto
    for aid, kws in _CHAT_ACTOS.items():
        if has(*kws):
            acto = next((a for a in kb.get("actos", []) if a["id"] == aid), {})
            ocurr = [a for a in acts if _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))
                     and _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))["id"] == aid]
            lines = [f"{hdr}🧾 {acto.get('nombre', aid)} — base legal: {acto.get('articulo','')} COGEP"]
            if ocurr:
                lines.append(f"\nOcurrencias en el expediente ({len(ocurr)}):")
                for a in ocurr[:5]:
                    lines.append(f"• {str(a.get('FechaProvidencia',''))[:10]} — {a.get('NombreProvidencia','')} ({a.get('TipoProvidencia') or 's/t'}) · responsable: {a.get('Login','—')}")
            else:
                lines.append("\nEste acto aún no consta en el expediente.")
            dict_r = [r for r in res if r.get("acto_hasta") == aid or r.get("acto_desde") == aid]
            for r in dict_r:
                lines.append("\n⚖ " + _fmt_regla(r, largo=True))
            return {"answer": "\n".join(lines), "intent": "acto:" + aid,
                    "sugerencias": ["¿Qué plazos se incumplieron?", "¿Cómo está la salud del juicio?", "Historial de actuaciones"]}

    # 6) juez / responsables
    if has("juez", "jueza", "juzgador", "quien tramito", "quien tramita", "secretario", "responsable", "judicatura"):
        users = []
        for a in acts:
            u = a.get("Login") or ""
            if u and u not in users: users.append(u)
        return {"answer": (f"{hdr}🏛 Judicatura: {cab.get('NombreJudicatura','—')}\n"
                           f"Usuarios que tramitaron actuaciones ({len(users)}): {', '.join(users) or '—'}\n\n"
                           "El dictamen de cada término indica el login responsable de la actuación evaluada."),
                "intent": "juez", "sugerencias": ["¿Qué plazos se incumplieron?", "Detalle de la sentencia"]}

    # 7) artículo N del COGEP
    import re as _re
    m = _re.search(r"art\w*\.?\s*(\d+)", q)
    if m:
        num = m[1]
        hits = []
        for r in kb.get("reglas", []):
            if num in r["articulo"]:
                hits.append(f"📖 {r['articulo']} — {r['nombre']} (término: {r['termino_dias']} días hábiles)\n“{r['texto_norma']}”")
        for a in kb.get("actos", []):
            if num in str(a.get("articulo","")) and not any(num in h for h in hits):
                hits.append(f"📖 {a['articulo']} — {a['nombre']}")
        if hits:
            return {"answer": hdr + "\n\n".join(hits), "intent": "articulo",
                    "sugerencias": ["¿Qué plazos se incumplieron?", "¿Cómo está la salud del juicio?"]}
        return {"answer": f"El Art. {num} no está parametrizado en la base de conocimiento COGEP (cogep_kb.json). "
                          "Puedes agregarlo editando ese archivo: el razonador y este chat lo usarán automáticamente.",
                "intent": "articulo", "sugerencias": ["¿Qué dice el Art. 146?", "¿Qué dice el Art. 333?"]}

    # 8) procedimiento / vía procesal
    if has("procedimiento", "via", "tramite", "sumario", "ordinario", "etapas"):
        proc = j["procedimiento"]
        pk = next((p for p in kb.get("procedimientos", []) if p["id"] == proc["id"]), {})
        etapas = " → ".join(e["nombre"] for e in pk.get("etapas", []))
        return {"answer": (f"{hdr}La causa se tramita en {proc['nombre']} ({proc['articulos']} COGEP).\n"
                           f"Materia: {cab.get('Materia','—')} · Acción: {cab.get('Tipo Accion','—')}\n"
                           f"Etapas del flujo: {etapas}"),
                "intent": "procedimiento", "sugerencias": ["¿Cómo está la salud del juicio?", "Historial de actuaciones"]}

    # 9) historial / actuaciones
    if has("historial", "actuacion", "actividades", "providencia", "cuantas", "ultima", "movimientos", "pasos"):
        last = acts[-3:][::-1]
        det = "\n".join(f"• {str(a.get('FechaProvidencia',''))[:10]} — {a.get('NombreProvidencia','')}" for a in last)
        return {"answer": (f"{hdr}El expediente registra {len(acts)} actuaciones.\nÚltimas:\n{det}\n\n"
                           "Activa «▶ Recorrido» en el diagrama para verlas animadas en orden cronológico."),
                "intent": "historial", "sugerencias": ["¿Cuándo inició la causa?", "¿Cómo está la salud del juicio?"]}

    # 10) blockchain / integridad
    if has("blockchain", "integridad", "ledger", "hash", "alterado", "cadena"):
        l = get_ledger(file)
        return {"answer": (f"{hdr}⛓ Ledger de integridad: {l.get('longitud')} bloques SHA-256 encadenados.\n"
                           f"Root: {str(l.get('root',''))[:32]}…\n"
                           "Cada actuación es un bloque (hash = SHA-256(idx | fecha | data | hash_prev)): alterar una rompe la cadena. "
                           "Puedes verificarlo en vivo con el botón «✔ Verificar cadena» de la tarjeta Blockchain."),
                "intent": "blockchain", "sugerencias": ["¿Cómo está la salud del juicio?", "Historial de actuaciones"]}

    # 11) inicio / duración / fechas
    if has("inicio", "ingreso", "empezo", "duracion", "cuanto lleva", "cuando", "fecha"):
        fi = str(cab.get("FechaIngreso",""))[:10]
        fu = str(acts[-1].get("FechaProvidencia",""))[:10] if acts else "—"
        d1, d2 = _parse_dt_str(cab.get("FechaIngreso")), _parse_dt_str(acts[-1].get("FechaProvidencia")) if acts else None
        dur = business_days(d1, d2) if d1 and d2 else None
        return {"answer": (f"{hdr}📅 Ingreso de la causa: {fi}\nÚltima actuación: {fu}"
                           + (f"\nDuración tramitada: {dur} días hábiles." if dur is not None else "")
                           + f"\nEstado procesal actual: {cab.get('EstadoProcesal','—')}"),
                "intent": "fechas", "sugerencias": ["Historial de actuaciones", "¿Qué plazos se incumplieron?"]}

    # 12) materia / sobre qué trata
    if has("materia", "delito", "trata", "sobre que", "tipo de juicio", "asunto"):
        return {"answer": (f"{hdr}La causa versa sobre: {cab.get('Delito') or cab.get('Materia','—')}\n"
                           f"Materia: {cab.get('Materia','—')} · Acción: {cab.get('Tipo Accion','—')} · "
                           f"Estado: {cab.get('EstadoProcesal','—')}\nJudicatura: {cab.get('NombreJudicatura','—')}"),
                "intent": "materia", "sugerencias": ["¿En qué procedimiento se tramita?", "¿Cómo está la salud del juicio?"]}

    # fallback
    return {"answer": ("No encontré esa información en la ontología COGEP ni en el expediente. "
                       "Prueba preguntarme por: salud del juicio, plazos/incumplimientos, un acto concreto "
                       "(sentencia, audiencia, citación, contestación…), el juez, un artículo del COGEP, "
                       "el historial o la integridad blockchain."),
            "intent": "fallback",
            "sugerencias": ["¿Cómo está la salud del juicio?", "¿Qué plazos se incumplieron?", "¿Cuándo fue la sentencia?"]}

class ChatReq(BaseModel):
    file: str = ""
    question: str = ""

@app.post("/api/cogep/chat", summary="Chat IA sobre la causa (razonador COGEP)", tags=["COGEP IA"])
def post_cogep_chat(req: ChatReq):
    try:
        return cogep_chat_answer(req.file, req.question)
    except Exception as e:
        return {"answer": f"Error del razonador: {e}", "intent": "error", "sugerencias": []}


if FRONT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONT_DIR), html=True), name="static")
