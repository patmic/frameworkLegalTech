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

from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import xml.etree.ElementTree as ET
import json, hashlib
import re, ssl, urllib.request, datetime, time
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
SDT_DIR    = DATA_DIR / "sdt"                         # gemelos digitales estructurales (.json) — selector del tab Validación
OWL_PATH   = DATA_DIR / "MALTG_ontology.owl"
ONTO_JSON  = DATA_DIR / "MALTG_ontology.json"       # estructura (estrella) del grafo de ontología (tab 03)
ONTO_INFO  = DATA_DIR / "MALTG_ontologyInfo.json"   # detalles informativos por nodo (descripción, norma…)
DT_PATH    = SDT_DIR / "SDT_Synthetic.json"          # gemelo digital sintético (antes dt_arch.json)
WF_DIR     = DATA_DIR / "workflow"        # directory holding BPMN workflow JSON files
EXP_DIR    = DATA_DIR / "LegalCase"        # decided cases (causas/juicios) JSON files
MALTG_PATH = DATA_DIR / "MALTG_architecture.json"  # JSON-LD multidimensional architecture
SDT_CJ_PATH = SDT_DIR / "SDT_CJ.json"              # Gemelo Digital Estructural del Consejo de la Judicatura (JSON-LD)
FRONT_DIR  = Path("/frontend")

OWL_NS   = "http://www.w3.org/2002/07/owl#"
RDF_NS   = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
RDFS_NS  = "http://www.w3.org/2000/01/rdf-schema#"
MALTG_NS = "http://maltg.arch/onto#"

# ═══════════════════════════════════════════════════════════════════
#  10 VALIDATION DIMENSIONS
#  Foundation (TOGAF, COBIT, ITIL, NIST) + Technology (AI, BC, OpenData, Security)
#  + Interop + LegalTech domain — alineadas con MALTG_architecture.json
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
        "key": "ITIL", "label": "Gestión de Servicios ITIL",
        "bar_color": "linear-gradient(90deg,#22d3ee,#0ea5e9)",
        "owl_types": ["itil"],
        "dt_refs": ["ITIL","Service_Operation","Incident_Management","Change_Enablement",
                    "Service_Level_Management","Configuration_Management"],
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
                "definition": "Directed graph G(V, E) representing the microservice architecture. SDT_Synthetic.json (data/sdt) is the canonical Δ.",
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
            "description": "Parse the selected SDT (data/sdt/*.json) and construct the directed service graph Δ. Build the coverage set R by collecting all maltg_ref values (string or array) across all services.",
            "inputs":  ["data/sdt/SDT_Synthetic.json"],
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


def parse_ontology():
    """
    Fuente del grafo de ontología (tab 03) y de los onto_scores de la validación.
    Prefiere MALTG_ontology.json (con descripción conceptual por nodo); si no
    existe o es inválido, recae en MALTG_ontology.owl. Devuelve el mismo esquema
    {nodes, links, node_count, link_count, hash, meta?}.
    """
    if ONTO_JSON.exists():
        try:
            data = json.loads(ONTO_JSON.read_text(encoding="utf-8-sig"))
            nodes = data.get("nodes", [])
            links = data.get("links", [])
            data["node_count"] = len(nodes)
            data["link_count"] = len(links)
            data["hash"] = file_hash(ONTO_JSON)
            return data
        except json.JSONDecodeError as e:
            return {"error": f"JSON error en MALTG_ontology.json: {e}",
                    "nodes": [], "links": []}
    return parse_owl()


# ─── DT Parser ────────────────────────────────────────────────────────────────
def _resolve_sdt_path(file: str = ""):
    """Resuelve de forma segura un .json dentro de /data/sdt (sin path traversal)."""
    if not file:
        return DT_PATH
    name = Path(file).name                       # descarta cualquier ruta
    if not name.endswith(".json"):
        name += ".json"
    p = (SDT_DIR / name).resolve()
    try:
        p.relative_to(SDT_DIR.resolve())         # debe quedar dentro de /data/sdt
    except ValueError:
        return DT_PATH
    return p

def parse_dt(path=None):
    p = path or DT_PATH
    if not p.exists():
        return {"error": f"SDT no encontrado: {p}"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data["hash"] = file_hash(p)
        data["_file"] = p.name
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
def compute_validation(dt_file: str = ""):
    onto = parse_ontology()
    dt   = parse_dt(_resolve_sdt_path(dt_file))
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
        "dt_file":        dt.get("_file",""),
        "dt_title":       (dt.get("meta") or {}).get("title",""),
    }


# ─── Endpoints ────────────────────────────────────────────────────────────────
@app.get("/api/ontology",    summary="MALTG_ontology.json (estructura) → D3 graph", tags=["MALTG Data"])
def get_ontology(): return parse_ontology()

@app.get("/api/ontology-info", summary="MALTG_ontologyInfo.json → detalle por nodo", tags=["MALTG Data"])
def get_ontology_info():
    """Detalles informativos de cada nodo (descripción conceptual, norma, score)."""
    if not ONTO_INFO.exists():
        return {"info": {}}
    try:
        return json.loads(ONTO_INFO.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        return {"error": f"JSON error: {e}", "info": {}}

@app.post("/api/ontology/score", summary="Actualizar el score de un nodo (persistente)", tags=["MALTG Data"])
def set_ontology_score(payload: dict = Body(...)):
    """
    Persiste el nuevo score (0-100) de un nodo de la ontología en
    MALTG_ontology.json (estructura — alimenta barras y radar) y en
    MALTG_ontologyInfo.json (detalle). Lo usa el slider de cada leyenda.
    """
    node = (payload or {}).get("id")
    if not node:
        return {"error": "falta 'id'"}
    try:
        score = max(0, min(100, int(round(float(payload.get("score"))))))
    except (TypeError, ValueError):
        return {"error": "score inválido"}

    updated = []
    # 1) estructura (drive del gráfico y del radar)
    if ONTO_JSON.exists():
        try:
            d = json.loads(ONTO_JSON.read_text(encoding="utf-8-sig"))
            hit = False
            for n in d.get("nodes", []):
                if n.get("id") == node:
                    n["score"] = str(score); hit = True
            if hit:
                ONTO_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
                updated.append("MALTG_ontology.json")
        except Exception as e:
            return {"error": f"no se pudo escribir MALTG_ontology.json: {e}"}
    # 2) info (detalle por nodo)
    if ONTO_INFO.exists():
        try:
            d2 = json.loads(ONTO_INFO.read_text(encoding="utf-8-sig"))
            info = d2.get("info", {})
            if node in info:
                info[node]["score"] = str(score)
                ONTO_INFO.write_text(json.dumps(d2, ensure_ascii=False, indent=2), encoding="utf-8")
                updated.append("MALTG_ontologyInfo.json")
        except Exception as e:
            return {"error": f"no se pudo escribir MALTG_ontologyInfo.json: {e}"}

    if not updated:
        return {"error": f"nodo no encontrado: {node}"}
    return {"ok": True, "id": node, "score": score, "updated": updated}

@app.get("/api/dt-arch",     summary="SDT_Synthetic.json (data/sdt) with hash", tags=["MALTG Data"])
def get_dt_arch():  return parse_dt()

@app.get("/api/validation",  summary="9-dim conformance scores",  tags=["MALTG Data"])
def get_validation(file: str = ""): return compute_validation(file)

@app.get("/api/sdt-files", summary="Lista los gemelos digitales (.json) en /data/sdt", tags=["MALTG Data"])
def get_sdt_files():
    files = []
    if SDT_DIR.exists():
        for p in sorted(SDT_DIR.glob("*.json")):
            title = ""
            try:
                j = json.loads(p.read_text(encoding="utf-8"))
                title = (j.get("meta") or {}).get("title", "")
            except Exception:
                pass
            files.append({"file": p.name, "title": title,
                          "default": (p.name == DT_PATH.name)})
    return {"dir": "/data/sdt", "files": files, "default": DT_PATH.name}

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
    # 1) por código de flujo (acepta 'flujo' único o lista 'flujos')
    for p in kb.get("procedimientos", []):
        if flujo and (p.get("flujo") == flujo or flujo in (p.get("flujos") or [])):
            return p
    # 2) por nombre del tipo de acción
    for p in kb.get("procedimientos", []):
        if p["id"] in tipo:
            return p
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


# ═══════════════════════════════════════════════════════════════════
#  SDT_CJ — Gemelo Digital Estructural del Consejo de la Judicatura (CJ)
#  Web scraping del portal funcionjudicial.gob.ec + análisis de madurez
#  LegalTech contra MALTG_ontology.owl → /data/SDT_CJ.json (JSON-LD)
# ═══════════════════════════════════════════════════════════════════
CJ_TARGETS = {
    "portal":      "https://www.funcionjudicial.gob.ec/",
    "satje_spa":   "https://procesosjudiciales.funcionjudicial.gob.ec/busqueda",
    "esatje":      "https://www.funcionjudicial.gob.ec/satje/",
    "estadistica": "https://fsweb.funcionjudicial.gob.ec/estadisticas/datoscj/portalestadistica.html",
    "iso37001":    "https://www.funcionjudicial.gob.ec/sistema-de-gestion-antisoborno-de-acuerdo-a-la-norma-iso-37001/",
}

# Protocolo reproducible (ver /data/evidence/PROTOCOLO.md)
SCRAPER_UA = "MALTG-SDT-Auditor/1.0 (+legaltech-governance-scraper; protocolo v1)"

def utcnow_iso():
    # Nota: en este módulo `datetime` es la CLASE (from datetime import datetime, línea superior)
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def _http_get(url, timeout=8):
    """GET con stdlib (sin dependencias). Devuelve (status, html, headers)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": SCRAPER_UA,
        "Accept": "text/html,application/xhtml+xml",
    })
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
        raw = r.read(400_000)
        enc = r.headers.get_content_charset() or "utf-8"
        return r.status, raw.decode(enc, "replace"), dict(r.headers)

def scrape_cj():
    """Scraping en vivo del ecosistema CJ → fingerprints tecnológicos y evidencias."""
    rep = {"scanned_at": utcnow_iso(),
           "targets": {}, "signals": {}, "online": False, "errors": []}
    portal_html = ""
    for key, url in CJ_TARGETS.items():
        t0 = time.time()
        try:
            status, html, headers = _http_get(url)
            if key == "portal":
                portal_html = html
            rep["targets"][key] = {
                "url": url, "status": status, "ok": 200 <= status < 400,
                "bytes": len(html), "ms": int((time.time() - t0) * 1000),
                "generator": headers.get("X-Generator") or headers.get("generator") or "",
            }
            rep["online"] = True
        except Exception as e:
            rep["targets"][key] = {"url": url, "ok": False, "error": str(e)[:160]}
            rep["errors"].append(f"{key}: {e}")
    pl = portal_html.lower()
    sig = rep["signals"]
    sig["wordpress_elementor"] = ("elementor" in pl) or ("wp-content" in pl)
    sig["jsf_legacy_links"]    = len(re.findall(r'\.jsf', portal_html, re.I))
    sig["php_legacy_links"]    = len(re.findall(r'\.php', portal_html, re.I))
    sig["satje_spa_modern"]    = "procesosjudiciales" in pl
    sig["open_data_ref"]       = ("datosabiertos" in pl) or ("justicia-abierta" in pl) or ("estadistica" in pl)
    sig["iso37001_ref"]        = ("37001" in pl) or ("antisoborno" in pl)
    sig["disciplinary_ref"]    = "disciplinari" in pl
    sig["json_ld_semantic"]    = ('application/ld+json' in pl) or ('"@context"' in portal_html)
    sig["public_api_spec"]     = bool(re.search(r'swagger|openapi|/api/v\d', portal_html, re.I))
    return rep

def _cj_model():
    """Modelo experto del SDT del CJ (componentes, capas y dimensiones de madurez)."""
    colorTypes = {"external":"#ff9a3c","modern":"#10e98c","legacy":"#ff4d6d","service":"#a855f7",
                  "data":"#00e5ff","semantic":"#b060ff","compliance":"#60a5fa","strategic":"#ffc947"}
    layers = [
        {"id":"l_ext","label":"CIUDADANIA / EXTERNAL","x":8,"y":8,"width":120,"height":690,"fill":"#0a1020"},
        {"id":"l_front","label":"PRESENTACION / FRONTEND","x":136,"y":8,"width":152,"height":690,"fill":"#0a1018"},
        {"id":"l_leg","label":"INTEGRACION LEGACY","x":296,"y":8,"width":152,"height":690,"fill":"#160a12"},
        {"id":"l_svc","label":"APLICACIONES / SERVICIOS","x":456,"y":8,"width":152,"height":690,"fill":"#100a1a"},
        {"id":"l_data","label":"DATOS & WEB SEMANTICA","x":616,"y":8,"width":164,"height":690,"fill":"#081820"},
        {"id":"l_gov","label":"GOBERNANZA & COMPLIANCE","x":788,"y":8,"width":172,"height":690,"fill":"#081020"},
        {"id":"l_str","label":"ESTRATEGIA / INNOVACION","x":968,"y":8,"width":160,"height":690,"fill":"#1a1608"},
    ]
    def s(i,l,sub,ct,x,y,st,m,d,ev="",dim=""):
        return {"id":i,"label":l,"subtitle":sub,"colorType":ct,"x":x,"y":y,"width":140,"height":46,
                "status":st,"maltg_ref":m,"description":d,"evidence":ev,"dimension":dim}
    services = [
        s("ciudadano","Ciudadano","Usuario final","external",16,150,"active",["LegalTech_Domain"],"Ciudadano que consulta causas y tramites via portal y SATJE."),
        s("abogado","Abogado","Firma electronica","external",16,260,"active",["Digital_Signature","eIDAS_Compliance"],"Profesional que opera e-SATJE con firma electronica."),
        s("interop_ent","Entidades","TCE / Fiscalia","external",16,370,"partial",["Court_System_Integration","Interoperability"],"Otras entidades de la Funcion Judicial; codigo fuente SATJE entregado al TCE (2024).","TCE recibe codigo SATJE (2024)","D2"),
        s("portal_wp","Portal CJ","WordPress+Elementor","legacy",144,70,"legacy",["Technology_Architecture"],"Portal publico sobre WordPress + Elementor (PHP/jQuery, CMS acoplado).","meta-generator Elementor","D2"),
        s("satje_spa","SATJE v4","SPA desacoplada","modern",144,160,"active",["APIs","Technology_Architecture"],"Consulta de Procesos SATJE v4.0.1: SPA moderna desacoplada.","SPA v4.0.1","D2"),
        s("esatje","e-SATJE OGJE","Gestion 24/7","modern",144,250,"active",["Case_Management","Workflows","Digital_Signature"],"Oficina de Gestion Judicial Electronica (e-SATJE 2020), 24/7.","e-SATJE 2020","D2"),
        s("supa","SUPA","Pensiones aliment.","service",144,340,"active",["Case_Management"],"Sistema Unico de Pensiones Alimenticias."),
        s("serv_linea","Servicios en Linea","Hub de servicios","service",144,430,"partial",["Service_Catalog"],"Hub que enlaza aplicaciones heredadas y modernas."),
        s("jsf_remates","Remates JSF","PrimeFaces/.jsf","legacy",304,80,"legacy",["Technology_Architecture"],"Remates Judiciales sobre JavaServer Faces (portal.jsf).","remates portal.jsf","D2"),
        s("jsf_dir","Directorio JSF",".jsf heredado","legacy",304,170,"legacy",["Technology_Architecture"],"Directorio telefonico sobre JSF (directorio.jsf).","directorio.jsf","D2"),
        s("php_siscadep","SISCADEP","Guia .php","legacy",304,260,"legacy",["Technology_Architecture"],"Guia de Servicios sobre PHP heredado (frmConsultaExterna.php).","siscadep .php","D2"),
        s("citaciones","Citaciones","Consulta","service",304,350,"active",["Notarization"],"Consulta de Citaciones Judiciales."),
        s("biometrico","Biometrico","Control interno","legacy",304,440,"legacy",["IAM","Access_Control"],"Sistema biometrico institucional."),
        s("gestion_doc","Gestion Documental","Interno","service",464,80,"partial",["Case_Management","Audit_Trail"],"Sistema de gestion documental institucional."),
        s("concursos","Concursos","Seleccion jueces","service",464,170,"active",["Workflows"],"Sistema de Concursos para meritocracia judicial."),
        s("mediacion","Mediacion","CNM","service",464,260,"active",["Smart_Legal_Contracts"],"Centro Nacional de Mediacion."),
        s("exp_disc","Expedientes Disc.","Disciplinario","compliance",464,350,"partial",["Compliance","Audit","Regulatory_Compliance_Engine"],"Expedientes/resoluciones disciplinarias (COFJ); automatizacion parcial.","Portal expedientes disc.","D4"),
        s("escuela","Escuela FJ","Formacion","service",464,440,"active",["Legal_Knowledge_Base"],"Escuela de la Funcion Judicial."),
        s("estadistica","Portal Estadistica","HTML estatico","data",624,70,"partial",["Data_Portal","Strategic_KPIs"],"Portal de Estadisticas Judiciales (HTML/descargas), no Linked Data.","portalestadistica.html","D1"),
        s("datos_abiertos","Datos Abiertos","CKAN nacional","data",624,160,"partial",["OpenData_Layer","DCAT_Catalog","Open_Standards"],"Participacion en datosabiertos.gob.ec (CKAN/DCAT), sin JSON-LD judicial propio.","datosabiertos.gob.ec/cj","D1"),
        s("justicia_abierta","Justicia Abierta","En construccion","data",624,250,"planned",["OpenData_Layer","Data_Portal"],"Portal unico de datos abiertos 'Justicia Abierta', en construccion.","Portal Justicia Abierta","D1"),
        s("bdd_jur","Repositorio Jurisd.","BDD operativa","data",624,340,"active",["Data_Lakes","Provenance"],"Repositorio que integra datos jurisdiccionales/operativos diarios.","","D1"),
        s("semantic_layer","Capa Semantica","Ontologias/JSON-LD","semantic",624,430,"absent",["JSON_LD","FAIR_Principles","Open_API_Spec","Interoperability"],"AUSENTE: sin ontologias/Linked Data/JSON-LD/FAIR judicial. Oportunidad MALTG.","Sin Web Semantica publica","D1"),
        s("dt_judicial","Gemelos Digitales","DT judicial","semantic",624,520,"absent",["Process_Mining","Predictive_Analytics","Symbolic_Reasoner"],"AUSENTE: sin facilidades para Gemelos Digitales Judiciales.","Sin Digital Twins","D1"),
        s("iso37001","ISO 37001 SGAS","Antisoborno","compliance",796,70,"active",["Compliance","MEA03_Compliance","Ethics","Risk_Assessment"],"Sistema de Gestion Antisoborno ISO 37001 (Resol. CJ-DG-2025-049).","CJ-DG-2025-049","D4"),
        s("compliance_jud","Compliance Judicial","Modelo gestion","compliance",796,160,"partial",["Regulatory_Compliance_Engine","Governance_Compliance_Layer"],"Modelo de Gestion para el Compliance Judicial (documento).","Modelo Compliance Judicial","D4"),
        s("sist_disc","Sistema Disciplinario","Modernizacion","compliance",796,250,"planned",["Audit_Trail","Continuous_Monitoring","DSS05_Security_Services"],"Modernizacion del sistema disciplinario con plataforma de ultima generacion.","Modernizacion disciplinario","D4"),
        s("denuncias","Denuncias Corrupcion","Canal digital","compliance",796,340,"active",["Detect_Function"],"Canales de Denuncias de Actos de Corrupcion.","","D4"),
        s("plan_integridad","Plan Integridad","2024-2028","compliance",796,430,"active",["Govern_Function","Regulation"],"Adhesion al Plan Nacional de Integridad Publica 2024-2028.","Plan Integridad 2024-2028","D4"),
        s("lotaip","LOTAIP","Transparencia","compliance",796,520,"active",["Audit","Regulation","Metrics"],"Portal de transparencia LOTAIP y rendicion de cuentas."),
        s("plan_estr","Plan Estrategico","2026-2031","strategic",976,120,"active",["Strategic_Layer","Strategic_KPIs","Planning"],"Plan Estrategico 2026-2031 aprobado por el Pleno.","Pleno aprueba PE 2026-2031","D3"),
        s("eje_digital","Eje Transf. Digital","Innovacion tecno.","strategic",976,230,"partial",["Architecture_Vision","Roadmap","Migration_Planning"],"Eje 'Transformacion digital e innovacion tecnologica' del PE.","Eje transf. digital","D3"),
        s("plan_inv","Plan Inversion","2026-2029","strategic",976,340,"active",["Investment_Governance","Value_Realization"],"Plan Anual y Plurianual de Inversion 2026-2029.","Plan Inversion 2026-2029","D3"),
        s("infra_obsoleta","Infra Obsoleta","Riesgo 90%","legacy",976,450,"legacy",["Technology_Architecture","APO12_Risk"],"Brecha critica: ~90% de la infraestructura tecnologica obsoleta.","90% infra obsoleta","D3"),
    ]
    connections = [
        ("ciudadano","portal_wp","solid"),("ciudadano","satje_spa","solid"),("abogado","satje_spa","solid"),
        ("abogado","esatje","solid"),("interop_ent","satje_spa","dashed"),("portal_wp","serv_linea","solid"),
        ("satje_spa","esatje","solid"),("satje_spa","bdd_jur","solid"),("esatje","gestion_doc","solid"),
        ("serv_linea","jsf_remates","solid"),("serv_linea","php_siscadep","solid"),("serv_linea","citaciones","solid"),
        ("serv_linea","jsf_dir","dashed"),("supa","bdd_jur","solid"),("concursos","bdd_jur","solid"),
        ("gestion_doc","bdd_jur","solid"),("exp_disc","sist_disc","solid"),("bdd_jur","estadistica","solid"),
        ("bdd_jur","datos_abiertos","solid"),("datos_abiertos","justicia_abierta","dashed"),
        ("bdd_jur","semantic_layer","dashed"),("semantic_layer","dt_judicial","dashed"),
        ("datos_abiertos","semantic_layer","dashed"),("sist_disc","iso37001","solid"),
        ("denuncias","iso37001","solid"),("iso37001","compliance_jud","solid"),
        ("plan_integridad","compliance_jud","solid"),("lotaip","compliance_jud","dashed"),
        ("plan_estr","eje_digital","solid"),("eje_digital","plan_inv","solid"),
        ("eje_digital","satje_spa","dashed"),("plan_inv","infra_obsoleta","solid"),
    ]
    connections = [{"from":a,"to":b,"style":c} for a,b,c in connections]
    scale = [
        {"level":1,"name":"Inicial","range":"0-20","desc":"Procesos manuales / ad-hoc, sin estructura digital."},
        {"level":2,"name":"En Transicion","range":"21-40","desc":"Islas digitales, datos en silos, sin interoperabilidad."},
        {"level":3,"name":"Definido","range":"41-60","desc":"Procesos definidos y portales modernos emergentes; brechas de ejecucion."},
        {"level":4,"name":"Gestionado","range":"61-80","desc":"Servicios medidos, APIs e integracion semantica parcial."},
        {"level":5,"name":"Optimizado / Semantico","range":"81-100","desc":"Datos enlazados, gemelos digitales, automatizacion gobernada."},
    ]
    dimensions = [
        {"id":"D1","key":"datos_interop_semantica","label":"Capa de Datos e Interoperabilidad Semantica",
         "maltg_layer":"Technology_Integration_Layer / OpenData_Layer",
         "maltg_refs":["JSON_LD","DCAT_Catalog","OpenData_Layer","FAIR_Principles","Open_Standards","Interoperability","Data_Portal"],
         "score":28,"weight":0.25,
         "findings":["Estadistica judicial via Portal de Estadisticas (HTML) y participacion en el CKAN nacional datosabiertos.gob.ec (DCAT).",
                     "Repositorio que integra datos jurisdiccionales/operativos diarios; portal 'Justicia Abierta' en construccion."],
         "gaps":["Sin evidencia de ontologias, Web Semantica, JSON-LD ni Linked Data judicial.",
                 "Sin facilidades para Gemelos Digitales Judiciales ni API abierta documentada.",
                 "Datos como descargas/HTML (silos), no recursos FAIR interoperables."]},
        {"id":"D2","key":"arquitectura_integracion","label":"Arquitectura de Integracion (APIs y Frontend)",
         "maltg_layer":"Technology_Integration_Layer / Foundation (TOGAF Tech)",
         "maltg_refs":["APIs","Open_API_Spec","Technology_Architecture","Orchestration","Service_Catalog"],
         "score":42,"weight":0.25,
         "findings":["SATJE 'Consulta de Procesos' migro a una SPA moderna y desacoplada (v4.0.1).",
                     "e-SATJE (OGJE) ofrece gestion judicial electronica 24/7."],
         "gaps":["El portal publico depende de WordPress + Elementor (PHP/jQuery, acoplado).",
                 "Persisten aplicaciones heredadas JSF/PrimeFaces (.jsf) y PHP (remates, directorio, SISCADEP).",
                 "Sin API REST publica documentada (OpenAPI) ni API gateway de integracion."]},
        {"id":"D3","key":"transformacion_innovacion","label":"Transformacion e Innovacion Declarada",
         "maltg_layer":"Strategic_Layer",
         "maltg_refs":["Strategic_Layer","Architecture_Vision","Roadmap","Strategic_KPIs","Investment_Governance","Migration_Planning"],
         "score":55,"weight":0.25,
         "findings":["Plan Estrategico 2026-2031 con eje explicito 'Transformacion digital e innovacion tecnologica'.",
                     "Plan de Inversion 2026-2029 prioriza la transformacion del sistema digital."],
         "gaps":["Brecha de ejecucion: el CJ reconoce ~90% de infraestructura tecnologica obsoleta.",
                 "Alta intencion declarada con baja materializacion real en la arquitectura desplegada."]},
        {"id":"D4","key":"compliance_automatizacion","label":"Cumplimiento Regulatorio y Automatizacion (Compliance)",
         "maltg_layer":"Governance_Compliance_Layer",
         "maltg_refs":["Compliance","MEA03_Compliance","Regulatory_Compliance_Engine","Audit_Trail","Ethics","Govern_Function","Risk_Assessment"],
         "score":58,"weight":0.25,
         "findings":["Sistema de Gestion Antisoborno ISO 37001 (Resol. CJ-DG-2025-049; Politica Antisoborno 2025).",
                     "Modelo de Compliance Judicial, canales de denuncia y Plan Nacional de Integridad 2024-2028.",
                     "Modernizacion del sistema disciplinario con plataforma de ultima generacion."],
         "gaps":["Compliance sustentado mayormente en politicas/PDF, no en motores regulatorios automatizados.",
                 "Automatizacion de procesos disciplinarios en transicion (anunciada, no consolidada)."]},
    ]
    # slug = referencia estable al snapshot /data/evidence/<run>/<slug>.html (trazabilidad campo→fuente)
    sources = [
        {"slug":"portal_cj","label":"Portal CJ","url":"https://www.funcionjudicial.gob.ec/","dimensiones":["D2"]},
        {"slug":"satje_spa","label":"SATJE Consulta de Procesos (SPA v4.0.1)","url":"https://procesosjudiciales.funcionjudicial.gob.ec/busqueda","dimensiones":["D2"]},
        {"slug":"esatje_ogje","label":"e-SATJE 2020 (OGJE)","url":"https://www.funcionjudicial.gob.ec/satje/","dimensiones":["D2"]},
        {"slug":"plan_estrategico_2026_2031","label":"Plan Estrategico 2026-2031","url":"https://www.funcionjudicial.gob.ec/el-pleno-aprueba-el-plan-estrategico-2026-2031-para-transformar-la-funcion-judicial/","dimensiones":["D3"]},
        {"slug":"inversion_transf_digital","label":"Inversion en transformacion digital / infra obsoleta","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-prioriza-inversion-en-la-transformacion-digital-repotenciacion-de-la-infraestructura-y-combate-a-la-impunidad/","dimensiones":["D3"]},
        {"slug":"iso37001_sgas","label":"ISO 37001 Antisoborno (SGAS)","url":"https://www.funcionjudicial.gob.ec/sistema-de-gestion-antisoborno-de-acuerdo-a-la-norma-iso-37001/","dimensiones":["D4"]},
        {"slug":"modernizacion_disciplinario","label":"Modernizacion del sistema disciplinario","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-modernizara-su-sistema-disciplinario-con-plataforma-de-ultima-generacion-y-controles-de-seguridad/","dimensiones":["D4"]},
        {"slug":"plan_integridad_2024_2028","label":"Plan Nacional de Integridad Publica 2024-2028","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-se-adhiere-al-plan-nacional-de-integridad-publica-y-lucha-contra-la-corrupcion-2024-2028/","dimensiones":["D4"]},
        {"slug":"justicia_abierta","label":"Justicia Abierta — datos abiertos judiciales","url":"https://www.funcionjudicial.gob.ec/consejo-de-la-judicatura-trabaja-en-el-portal-unico-de-datos-abiertos-y-estadistica-judicial-justicia-abierta-transparentando-la-informacion-para-combatir-la-corrupcion/","dimensiones":["D1"]},
        {"slug":"ckan_datosabiertos_cj","label":"Datos Abiertos Ecuador (CKAN) — organizacion CJ","url":"https://datosabiertos.gob.ec/dataset/?organization=cj","dimensiones":["D1"]},
        {"slug":"portal_estadisticas","label":"Portal de Estadisticas Judiciales","url":"https://fsweb.funcionjudicial.gob.ec/estadisticas/datoscj/portalestadistica.html","dimensiones":["D1"]},
    ]
    return colorTypes, layers, services, connections, scale, dimensions, sources

def _level_for(score, scale):
    for it in scale:
        lo, hi = [int(x) for x in it["range"].split("-")]
        if lo <= score <= hi:
            return f'Nivel {it["level"]} · {it["name"]}'
    return "n/d"

def build_sdt_cj(scrape_report=None, evidence_run=None):
    """Construye el SDT_CJ JSON-LD; integra señales del scraping si están disponibles.
    `evidence_run` = id de la corrida de snapshots en /data/evidence (trazabilidad)."""
    colorTypes, layers, services, connections, scale, dimensions, sources = _cj_model()

    # Verificación en vivo: las señales del scraping confirman/ajustan la evidencia.
    verification = {}
    if scrape_report:
        sig = scrape_report.get("signals", {})
        verification = {
            "scanned_at": scrape_report.get("scanned_at"),
            "online": scrape_report.get("online", False),
            "wordpress_elementor_confirmado": bool(sig.get("wordpress_elementor")),
            "enlaces_legacy_jsf": sig.get("jsf_legacy_links", 0),
            "enlaces_legacy_php": sig.get("php_legacy_links", 0),
            "satje_spa_confirmado": bool(sig.get("satje_spa_modern")),
            "referencia_datos_abiertos": bool(sig.get("open_data_ref")),
            "referencia_iso37001": bool(sig.get("iso37001_ref")),
            "web_semantica_jsonld_detectada": bool(sig.get("json_ld_semantic")),
            "api_publica_detectada": bool(sig.get("public_api_spec")),
            "targets": scrape_report.get("targets", {}),
        }

    for d in dimensions:
        d["level"] = _level_for(d["score"], scale)
    overall = round(sum(d["score"] * d["weight"] for d in dimensions))

    now = utcnow_iso()
    doc = {
        "@context": {
            "maltg":"http://maltg.arch/onto#","sdt":"http://maltg.arch/sdt#",
            "schema":"http://schema.org/","dcterms":"http://purl.org/dc/terms/",
            "skos":"http://www.w3.org/2004/02/skos/core#",
            "label":"skos:prefLabel","title":"dcterms:title","description":"dcterms:description",
            "score":"maltg:maturityScore","level":"maltg:maturityLevel",
            "evidence":"sdt:evidence","findings":"sdt:findings","gaps":"sdt:gaps",
            "maltg_ref":{"@id":"maltg:mapsTo","@type":"@id"},
            "maltg_refs":{"@id":"maltg:mapsTo","@type":"@id"},
            "services":"sdt:hasComponent","connections":"sdt:hasFlow","dimensions":"sdt:hasDimension",
            "from":{"@id":"sdt:source","@type":"@id"},"to":{"@id":"sdt:target","@type":"@id"},
        },
        "@id":"sdt:SDT_CJ_Ecuador","@type":"sdt:StructuralDigitalTwin",
        "meta":{
            "title":"SDT_CJ — Gemelo Digital Estructural del Ecosistema Tecnologico del Consejo de la Judicatura del Ecuador",
            "version":"1.0.0",
            "description":"Gemelo digital estructural (SDT) del ecosistema digital del CJ, evaluado contra la ontologia MALTG para determinar su Nivel de Madurez LegalTech.",
            "subject":"Consejo de la Judicatura del Ecuador (funcionjudicial.gob.ec)",
            "auditor":"Auditor Principal de Arquitectura de Software / Consultor Senior LegalTech Governance",
            "method":"Web scraping + analisis multidimensional contra MALTG_ontology.owl",
            "generated":now,"maltg_compliance":"MALTG v4.1 · TOGAF · COBIT · NIST CSF · ISO 37001 · GDPR/eIDAS",
            "ontology_source":"/data/MALTG_ontology.owl","primary_source":"https://www.funcionjudicial.gob.ec/",
            "protocol":{
                "instrumento":"Analisis documental sistematico de fuentes oficiales (web scraping con snapshots verificables)",
                "documento":"/data/evidence/PROTOCOLO.md",
                "semillas":"/data/evidence/sources_semilla.json",
                "user_agent":SCRAPER_UA,
                "evidence_run":evidence_run,
                "fases":["identificacion","captura (snapshot + SHA-256)","verificacion de integridad","codificacion contra rubrica"],
            },
        },
        "maturity":{
            "overall_score":overall,"overall_level":_level_for(overall, scale),"scale":scale,
            "dimensions_summary":[{"id":d["id"],"label":d["label"],"score":d["score"],"level":d["level"]} for d in dimensions],
        },
        "scrape_report": verification,
        "canvas":{"width":1136,"height":706},
        "colorTypes":colorTypes,"layers":layers,"services":services,"connections":connections,
        "dimensions":dimensions,"sources":sources,
    }
    raw = json.dumps(doc, ensure_ascii=False, indent=2)
    doc["meta"]["self_hash"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]
    return doc

@app.post("/api/sdt-cj/scrape", summary="Scraping del portal CJ → genera SDT_CJ.json (JSON-LD)", tags=["SDT_CJ"])
def post_sdt_cj_scrape():
    """Ejecuta scraping en vivo del ecosistema CJ, recalcula la madurez y persiste /data/SDT_CJ.json.

    Blindado: nunca propaga una excepción (siempre devuelve JSON válido), de modo que el
    frontend no reciba un 'Internal Server Error' en texto plano.
    """
    import traceback
    rep = None
    try:
        rep = scrape_cj()
    except Exception as e:
        rep = {"scanned_at": utcnow_iso(),
               "online": False, "signals": {}, "targets": {},
               "errors": [f"scrape_cj: {e}"]}
    # Protocolo reproducible: snapshots verificables de TODAS las fuentes semilla
    evidence_run = None
    try:
        manifest = capture_evidence()
        evidence_run = manifest.get("run_id")
    except Exception as e:
        rep.setdefault("errors", []).append(f"capture_evidence: {e}")
    try:
        doc = build_sdt_cj(rep, evidence_run=evidence_run)
    except Exception as e:
        return {"error": f"build_sdt_cj fallo: {e}", "trace": traceback.format_exc()[-600:],
                "scrape_report": rep}
    try:
        SDT_CJ_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        doc["_written"] = str(SDT_CJ_PATH)
        bitacora_log("sistema/scraper", "regeneracion_sdt_cj",
                     f"SDT_CJ.json regenerado (madurez {doc['maturity']['overall_score']}/100); evidencia: {evidence_run or 'sin snapshots'}",
                     refs=[r for r in [evidence_run, "SDT_CJ.json"] if r])
    except Exception as e:
        doc["_write_error"] = str(e)
    return doc

@app.get("/api/sdt-cj", summary="Lee /data/SDT_CJ.json (gemelo digital estructural del CJ)", tags=["SDT_CJ"])
def get_sdt_cj():
    if SDT_CJ_PATH.exists():
        try:
            doc = json.loads(SDT_CJ_PATH.read_text(encoding="utf-8"))
            doc.setdefault("meta", {})["file_hash"] = file_hash(SDT_CJ_PATH)
            return doc
        except Exception as e:
            return {"error": f"SDT_CJ.json invalido: {e}"}
    # Si aún no existe, devolver el modelo experto (sin verificación en vivo)
    return build_sdt_cj(None)


# ═══════════════════════════════════════════════════════════════════
#  EVIDENCIA REPRODUCIBLE & BITÁCORA — Protocolo de recolección (Fallo 2)
#  Snapshots con SHA-256 en /data/evidence/<run>/ + manifest.json
#  Bitácora append-only encadenada por hash en /data/bitacora.json
# ═══════════════════════════════════════════════════════════════════
EV_DIR        = DATA_DIR / "evidence"
SEED_PATH     = EV_DIR / "sources_semilla.json"
PROTOCOL_PATH = EV_DIR / "PROTOCOLO.md"
BITACORA_PATH = DATA_DIR / "bitacora.json"

def load_seeds():
    """Fuentes semilla del protocolo. Si no existe el archivo, lo crea desde el modelo experto."""
    if SEED_PATH.exists():
        try:
            return json.loads(SEED_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    _, _, _, _, _, _, sources = _cj_model()
    seeds = [{"slug": s["slug"], "label": s["label"], "url": s["url"],
              "dimensiones": s.get("dimensiones", []), "incluida": True,
              "criterio": "Fuente oficial (*.funcionjudicial.gob.ec / *.gob.ec)"} for s in sources]
    EV_DIR.mkdir(parents=True, exist_ok=True)
    SEED_PATH.write_text(json.dumps(seeds, ensure_ascii=False, indent=2), encoding="utf-8")
    return seeds

# ── Bitácora append-only (cadena de hashes, mismo principio que el ledger) ──
def bitacora_read():
    if BITACORA_PATH.exists():
        try:
            return json.loads(BITACORA_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def bitacora_log(actor, accion, detalle="", refs=None, tipo="sistema"):
    entries = bitacora_read()
    prev = entries[-1]["hash"] if entries else "GENESIS"
    e = {"id": len(entries) + 1, "ts": utcnow_iso(), "tipo": tipo,
         "actor": actor, "accion": accion, "detalle": detalle,
         "refs": refs or [], "prev_hash": prev}
    e["hash"] = hashlib.sha256(json.dumps(e, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    entries.append(e)
    BITACORA_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    return e

def bitacora_verify(entries):
    """Verifica la cadena de hashes de la bitácora. Devuelve (ok, primer_id_roto|None)."""
    prev = "GENESIS"
    for e in entries:
        body = {k: e[k] for k in ("id","ts","tipo","actor","accion","detalle","refs","prev_hash") if k in e}
        if e.get("prev_hash") != prev:
            return False, e.get("id")
        if hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16] != e.get("hash"):
            return False, e.get("id")
        prev = e["hash"]
    return True, None

# ── Captura de snapshots verificables ────────────────────────────────
def capture_evidence(fecha_corte=None):
    """Descarga cada fuente semilla, guarda el HTML como snapshot y escribe manifest.json
    con URL, timestamp, bytes y SHA-256. La corrida queda en /data/evidence/<run_id>/."""
    seeds = load_seeds()
    stamp = datetime.utcnow()
    run_id = (fecha_corte or stamp.strftime("%Y-%m-%d")) + "_" + stamp.strftime("%H%M%S")
    n = 1
    while (EV_DIR / run_id).exists():
        n += 1
        run_id = run_id.split("-v")[0] + f"-v{n}"
    run_dir = EV_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for s in seeds:
        if not s.get("incluida", True):
            entries.append({"slug": s["slug"], "url": s["url"], "ok": False, "excluida": True,
                            "criterio": s.get("criterio", "")})
            continue
        t0 = time.time()
        try:
            status, html, headers = _http_get(s["url"], timeout=10)
            fname = s["slug"] + ".html"
            (run_dir / fname).write_text(html, encoding="utf-8")
            entries.append({
                "slug": s["slug"], "label": s["label"], "url": s["url"],
                "ok": 200 <= status < 400, "status": status,
                "bytes": len(html.encode("utf-8")),
                "sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "file": f"{run_id}/{fname}", "ms": int((time.time() - t0) * 1000),
                "captured_at": utcnow_iso(),
                "dimensiones": s.get("dimensiones", []),
            })
        except Exception as e:
            entries.append({"slug": s["slug"], "label": s.get("label",""), "url": s["url"],
                            "ok": False, "error": str(e)[:160]})
    n_ok = sum(1 for e in entries if e.get("ok"))
    manifest = {
        "run_id": run_id, "captured_at": utcnow_iso(),
        "user_agent": SCRAPER_UA,
        "seed_file": "/data/evidence/sources_semilla.json",
        "protocol": "/data/evidence/PROTOCOLO.md",
        "n_total": len(entries), "n_ok": n_ok,
        "entries": entries,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    bitacora_log("sistema/scraper", "captura_evidencia",
                 f"Corrida {run_id}: {n_ok}/{len(entries)} fuentes capturadas con snapshot + SHA-256.",
                 refs=[run_id])
    return manifest

def _resolve_run(run: str = ""):
    """Resuelve un run_id de forma segura dentro de /data/evidence (sin traversal)."""
    if run:
        name = Path(run).name
        d = (EV_DIR / name).resolve()
        if d.parent == EV_DIR.resolve() and d.is_dir() and (d / "manifest.json").exists():
            return d
        return None
    runs = sorted([d for d in EV_DIR.iterdir() if d.is_dir() and (d / "manifest.json").exists()]) if EV_DIR.exists() else []
    return runs[-1] if runs else None

# ── Endpoints de evidencia ───────────────────────────────────────────
@app.get("/api/evidence/runs", summary="Corridas de captura de evidencia", tags=["Evidencia & Bitácora"])
def get_evidence_runs():
    out = []
    if EV_DIR.exists():
        for d in sorted(EV_DIR.iterdir()):
            mf = d / "manifest.json"
            if d.is_dir() and mf.exists():
                try:
                    m = json.loads(mf.read_text(encoding="utf-8"))
                    out.append({"run_id": m.get("run_id", d.name), "captured_at": m.get("captured_at"),
                                "n_total": m.get("n_total"), "n_ok": m.get("n_ok")})
                except Exception:
                    out.append({"run_id": d.name, "error": "manifest ilegible"})
    return {"runs": out, "count": len(out)}

@app.get("/api/evidence/manifest", summary="Manifest de una corrida (última por defecto)", tags=["Evidencia & Bitácora"])
def get_evidence_manifest(run: str = ""):
    d = _resolve_run(run)
    if not d:
        return {"error": "no hay corridas de evidencia", "runs": 0}
    try:
        return json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"manifest ilegible: {e}"}

@app.get("/api/evidence/verify", summary="Verifica SHA-256 de los snapshots vs manifest", tags=["Evidencia & Bitácora"])
def get_evidence_verify(run: str = ""):
    d = _resolve_run(run)
    if not d:
        return {"error": "no hay corridas de evidencia"}
    try:
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    except Exception as e:
        return {"error": f"manifest ilegible: {e}"}
    results, ok_all = [], True
    for e in m.get("entries", []):
        if not e.get("ok"):
            results.append({"slug": e.get("slug"), "estado": "SIN_SNAPSHOT"})
            continue
        f = EV_DIR / e["file"]
        if not f.exists():
            results.append({"slug": e["slug"], "estado": "FALTANTE"}); ok_all = False; continue
        sha = hashlib.sha256(f.read_text(encoding="utf-8").encode("utf-8")).hexdigest()
        intact = sha == e.get("sha256")
        ok_all = ok_all and intact
        results.append({"slug": e["slug"], "estado": "INTEGRO" if intact else "ALTERADO",
                        "sha256_manifest": e.get("sha256", "")[:16], "sha256_actual": sha[:16]})
    verdict = "INTEGRA" if ok_all else "COMPROMETIDA"
    bitacora_log("sistema/verificador", "verificacion_integridad",
                 f"Corrida {m.get('run_id')}: evidencia {verdict}.", refs=[m.get("run_id")])
    return {"run_id": m.get("run_id"), "integra": ok_all, "resultados": results}

@app.get("/api/evidence/snapshot", summary="Vista previa de un snapshot capturado", tags=["Evidencia & Bitácora"])
def get_evidence_snapshot(run: str = "", slug: str = "", chars: int = 4000):
    d = _resolve_run(run)
    if not d:
        return {"error": "no hay corridas de evidencia"}
    name = Path(slug).name + ".html"
    f = (d / name).resolve()
    if f.parent != d.resolve() or not f.exists():
        return {"error": f"snapshot no encontrado: {slug}"}
    txt = f.read_text(encoding="utf-8")
    return {"run_id": d.name, "slug": slug, "bytes": len(txt.encode('utf-8')),
            "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest(),
            "preview": txt[:max(200, min(chars, 20000))]}

@app.post("/api/evidence/capture", summary="Ejecuta una captura de evidencia (snapshots + manifest)", tags=["Evidencia & Bitácora"])
def post_evidence_capture():
    try:
        return capture_evidence()
    except Exception as e:
        return {"error": f"capture_evidence: {e}"}

@app.get("/api/evidence/protocolo", summary="Texto del protocolo de recolección", tags=["Evidencia & Bitácora"])
def get_evidence_protocolo():
    if PROTOCOL_PATH.exists():
        return {"path": "/data/evidence/PROTOCOLO.md", "text": PROTOCOL_PATH.read_text(encoding="utf-8")}
    return {"error": "PROTOCOLO.md no encontrado en /data/evidence"}

@app.get("/api/evidence/seeds", summary="Fuentes semilla del protocolo", tags=["Evidencia & Bitácora"])
def get_evidence_seeds():
    return {"seeds": load_seeds(), "path": "/data/evidence/sources_semilla.json"}

# ── Endpoints de bitácora ────────────────────────────────────────────
@app.get("/api/bitacora", summary="Bitácora del proyecto (append-only, hash-encadenada)", tags=["Evidencia & Bitácora"])
def get_bitacora():
    entries = bitacora_read()
    ok, broken = bitacora_verify(entries)
    return {"entries": entries, "count": len(entries),
            "cadena_integra": ok, "primer_registro_roto": broken}

@app.post("/api/bitacora", summary="Añadir entrada manual a la bitácora", tags=["Evidencia & Bitácora"])
def post_bitacora(payload: dict = Body(...)):
    actor   = str(payload.get("actor", "")).strip() or "investigador"
    accion  = str(payload.get("accion", "")).strip()
    detalle = str(payload.get("detalle", "")).strip()
    if not accion and not detalle:
        return {"error": "se requiere 'accion' o 'detalle'"}
    e = bitacora_log(actor[:80], (accion or "nota")[:120], detalle[:2000],
                     refs=payload.get("refs") or [], tipo="manual")
    return {"ok": True, "entry": e}


if FRONT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONT_DIR), html=True), name="static")
