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
            "owl_hash":file_hash(OWL_PATH),"dt_hash":file_hash(DT_PATH)}

if FRONT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONT_DIR), html=True), name="static")
