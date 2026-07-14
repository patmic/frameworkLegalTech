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
SDT_CJ_PATH = SDT_DIR / "SDT_CJ.json"              # Modelo Digital Estructural (SDT) del Consejo de la Judicatura (JSON-LD)
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
PESOS_AHP_PATH = DATA_DIR / "pesos_ahp.json"
_PSI_OVERRIDE = {"w": None}   # usado por /api/sensibilidad para perturbar sin persistir

def _psi_weights():
    """Pesos de Ψ: AHP / panel de supuestos (pesos_ahp.json) o default 0.40/0.60."""
    if _PSI_OVERRIDE["w"]: return _PSI_OVERRIDE["w"]
    try:
        d = json.loads(PESOS_AHP_PATH.read_text(encoding="utf-8-sig"))
        r = min(0.9, max(0.1, float((d.get("psi") or {}).get("root", 0.40))))
        return (round(r, 4), round(1.0 - r, 4))
    except Exception:
        return (0.40, 0.60)

def psi(svc_refs_set: set, dt_refs: list) -> float:
    """
    Ψ(d) = w_root·𝟙[root_d ∈ R] + w_subs·(|sub_d ∩ R| / |sub_d|)
    w_root/w_subs configurables (AHP o panel de supuestos); default 0.40/0.60.
    """
    if not dt_refs: return 0.0
    W_ROOT, W_SUBS = _psi_weights()
    root, subs = dt_refs[0], dt_refs[1:]
    root_ok    = W_ROOT if root in svc_refs_set else 0.0
    sub_score  = W_SUBS * (sum(1 for r in subs if r in svc_refs_set) / max(1, len(subs))) if subs \
                 else (W_SUBS if root in svc_refs_set else 0.0)
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

    # ── Cierre del ciclo adaptativo (MAPE-K · Execute) ────────────────
    # Para el gemelo del CJ, la dimensión LEGALTECH mezcla el score declarado
    # con el índice empírico de /api/cogep/salud-global (expedientes reales).
    adaptativo = None
    if dt.get("_file") == "SDT_CJ.json":
        try:
            cache = json.loads(SALUD_CACHE.read_text(encoding="utf-8")) if SALUD_CACHE.exists() else None
            if cache and cache.get("indice_global") is not None:
                w  = float(load_adapt_cfg().get("peso_empirico_radar", 0.5))
                lt = next((r for r in results if r["key"] == "LEGALTECH"), None)
                if lt:
                    emp_score = round(float(cache["indice_global"]), 1)  # escala 0–100 del radar
                    lt["dt_score_declarado"] = lt["dt_score"]
                    lt["dt_score"] = round((1 - w) * lt["dt_score"] + w * emp_score, 1)
                    lt["empirico"] = {"indice": cache["indice_global"], "score": emp_score,
                                      "peso": w, "n_causas": cache.get("n_causas"),
                                      "ts": (cache.get("contexto_adaptacion") or {}).get("timestamp")}
                    adaptativo = {"aplicado": True, "dimension": "LEGALTECH", **lt["empirico"]}
        except Exception:
            pass

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
        "adaptativo":     adaptativo,
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

@app.get("/api/dt-arch",     summary="Gemelo digital (.json en data/sdt) with hash", tags=["MALTG Data"])
def get_dt_arch(file: str = ""):  return parse_dt(_resolve_sdt_path(file))

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

# ── Feriados judiciales configurables (Art. 77 COGEP) — editable desde la UI ──
FERIADOS_PATH = DATA_DIR / "feriados_judiciales.json"
_FERIADOS_CACHE = {"mtime": None, "dias": set()}

def load_feriados_doc():
    if not FERIADOS_PATH.exists():
        return {"meta": {}, "feriados": [], "suspensiones": []}
    try:
        return json.loads(FERIADOS_PATH.read_text(encoding="utf-8-sig"))
    except Exception as e:
        return {"meta": {"error": str(e)}, "feriados": [], "suspensiones": []}

def _feriados_set():
    """Set de fechas no computables (feriados + rangos de suspensión), cacheado por mtime."""
    if not FERIADOS_PATH.exists(): return set()
    m = FERIADOS_PATH.stat().st_mtime
    if _FERIADOS_CACHE["mtime"] == m: return _FERIADOS_CACHE["dias"]
    dias = set()
    doc = load_feriados_doc()
    for f in doc.get("feriados", []):
        try: dias.add(datetime.strptime(str(f.get("fecha", ""))[:10], "%Y-%m-%d").date())
        except ValueError: pass
    for s in doc.get("suspensiones", []):
        try:
            a = datetime.strptime(str(s.get("desde", ""))[:10], "%Y-%m-%d").date()
            b = datetime.strptime(str(s.get("hasta", ""))[:10], "%Y-%m-%d").date()
            cur = a
            while cur <= b:
                dias.add(cur); cur += timedelta(days=1)
        except ValueError: pass
    _FERIADOS_CACHE.update(mtime=m, dias=dias)
    return dias

def business_days(d1: datetime, d2: datetime) -> int:
    """Días hábiles transcurridos (Arts. 73 y 77 COGEP — excluye sáb/dom,
    feriados y suspensiones de término de /data/feriados_judiciales.json)."""
    if not d1 or not d2 or d2 <= d1: return 0
    fer = _feriados_set()
    days, cur = 0, d1.date()
    while cur < d2.date():
        cur += timedelta(days=1)
        if cur.weekday() < 5 and cur not in fer: days += 1
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
    umbrales = dict(kb.get("umbrales", {}))
    try:   # override del usuario-experto (panel de supuestos, con límites min-max)
        umbrales.update({k: v for k, v in (load_adapt_cfg().get("umbrales_razonador") or {}).items() if v is not None})
    except Exception: pass
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
        regla  = _regla_efectiva(regla, h["fecha"])   # M3: versión de la regla vigente a la fecha del acto
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
#  SDT_CJ — Modelo Digital Estructural (SDT) del Consejo de la Judicatura (CJ)
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
            "title":"SDT_CJ — Modelo Digital Estructural (SDT) del Ecosistema Tecnologico del Consejo de la Judicatura del Ecuador",
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
def post_sdt_cj_scrape(base: str = ""):
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
    # Persistir copia JSON-LD en /data/sdt/LegalTech_<dominio>_<fecha>.json
    # (dominio de la URL objetivo del tab Simulación: funcionjudicial, corteconstitucional, ...)
    try:
        import copy as _copy
        from urllib.parse import urlparse
        host = (urlparse(base).hostname or "") if base else ""
        host = (host or "funcionjudicial.gob.ec").lower()
        if host.startswith("www."):
            host = host[4:]
        dom = re.sub(r"[^a-z0-9]", "", host.split(".")[0]) or "sitio"
        base_url = base or "https://www.funcionjudicial.gob.ec/"

        # El archivo por dominio hereda el análisis pero con metadatos coherentes
        # con el sitio realmente auditado (no siempre el CJ).
        sdt_doc = _copy.deepcopy(doc)
        for k in ("_written", "_write_error", "_saved_sdt", "_sdt_save_error"):
            sdt_doc.pop(k, None)
        DOMAIN_LABELS = {
            "funcionjudicial":    "Consejo de la Judicatura del Ecuador",
            "corteconstitucional":"Corte Constitucional del Ecuador",
            "procesosjudiciales": "SATJE — Procesos Judiciales (Función Judicial)",
        }
        ent = DOMAIN_LABELS.get(dom, host)
        sdt_doc["@id"] = f"sdt:SDT_{dom}"
        m = sdt_doc.setdefault("meta", {})
        m["title"] = f"SDT_{dom} — Modelo Digital Estructural (SDT) del Ecosistema Tecnologico de {ent}"
        m["subject"] = f"{ent} ({host})"
        m["primary_source"] = base_url
        m["domain"] = dom
        m["scraping_target"] = base_url

        fecha = utcnow_iso()[:10].replace("-", "")
        sdt_dir = DATA_DIR / "sdt"
        sdt_dir.mkdir(parents=True, exist_ok=True)
        out = sdt_dir / f"LegalTech_{dom}_{fecha}.json"
        raw = json.dumps(sdt_doc, ensure_ascii=False, indent=2)
        sdt_doc["meta"]["self_hash"] = "sha256:" + hashlib.sha256(raw.encode()).hexdigest()[:16]
        out.write_text(json.dumps(sdt_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        # Devolver el doc con metadatos del dominio para que el tab Simulación
        # muestre las secciones coherentes con el sitio auditado.
        doc = sdt_doc
        doc["_saved_sdt"] = f"/data/sdt/{out.name}"
    except Exception as e:
        doc["_sdt_save_error"] = str(e)
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


# ═══════════════════════════════════════════════════════════════════
#  CAPA ADAPTATIVA (MAPE-K) — Monitor→Analyze→Plan→Execute sobre las
#  ontologías (Knowledge). Ver PLAN_ADAPTATIVIDAD.md.
#  M1 Variabilidad fáctica (IVF) · M2 Process Drift (IDP) ·
#  M5 Trazabilidad (contexto_adaptacion + bitácora) · M6 Alertas.
# ═══════════════════════════════════════════════════════════════════
ADAPT_CFG_PATH = DATA_DIR / "adaptativo_config.json"
SALUD_CACHE    = DATA_DIR / "salud_global_cache.json"
RAZONADOR_VERSION = "v3-adaptativo"

DEFAULT_ADAPT_CFG = {
    "version": 1,
    "pesos_ranking": {"salud": 0.50, "variabilidad": 0.25, "drift": 0.25},
    "peso_empirico_radar": 0.50,
    "puntos_drift": {"loop": 20, "pingpong": 15, "estancamiento_legal": 25,
                     "estancamiento_ref": 10, "retroceso": 20},
    "umbrales": {"loop_k": 3, "gap_referencial_dias": 60},
    "f1_min": 0.85,
    "umbrales_razonador": {"incumple_factor": 1.25},
    "actualizado": None, "actor": "sistema",
}

DISCLAIMER = ("Indicador de apoyo generado por razonamiento simbólico sobre la ontología COGEP — "
              "no constituye asesoría jurídica ni prejuzga la conducta procesal de los intervinientes.")

def load_adapt_cfg():
    cfg = json.loads(json.dumps(DEFAULT_ADAPT_CFG))  # deep copy
    if ADAPT_CFG_PATH.exists():
        try:
            user = json.loads(ADAPT_CFG_PATH.read_text(encoding="utf-8-sig"))
            for k, v in user.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict): cfg[k].update(v)
                else: cfg[k] = v
        except Exception: pass
    return cfg

def _contexto_adaptacion(trigger, extra=None):
    """M5 — metadatos de contexto: con qué conocimiento/configuración se produjo la salida."""
    ctx = {"kb_hash": file_hash(KB_PATH), "feriados_hash": file_hash(FERIADOS_PATH),
           "config_hash": file_hash(ADAPT_CFG_PATH), "ontologia_hash": file_hash(OWL_PATH),
           "razonador_version": RAZONADOR_VERSION, "timestamp": utcnow_iso(), "trigger": trigger}
    if extra: ctx.update(extra)
    return ctx

def _norm_prov(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())

def _iter_causas():
    if not EXP_DIR.exists(): return
    for p in sorted(EXP_DIR.glob("*.json")):
        try: d = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception: continue
        label, juicio = _causa_label(d, p.stem)
        yield p.name, label, juicio, d

# ── M1 · Variabilidad del Contexto Fáctico (IVF) ─────────────────────
def variabilidad_causa(kb, data):
    """IVF = 100·(actos_no_canónicos + actos_faltantes)/(canónicos + no_canónicos).
    'No canónico' = actividad que no resuelve a ningún acto de la ontología
    (fuera de frontera de vocabulario — guardrail M4)."""
    proc = _detect_procedimiento(kb, data)
    canon = []
    for e in proc.get("etapas", []):
        for a in e.get("actos", []):
            if a not in canon: canon.append(a)
    matched, extra = set(), {}
    for a in (data.get("actividades") or []):
        acto = _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))
        if acto: matched.add(acto["id"])
        else:
            k = _norm_prov(a.get("NombreProvidencia"))
            if k: extra[k] = extra.get(k, 0) + 1
    faltantes = [c for c in canon if c not in matched]
    ivf = round(min(100.0, 100.0 * (len(extra) + len(faltantes)) / max(1, len(canon) + len(extra))), 1)
    return {"procedimiento": proc.get("id"), "actos_canonicos": len(canon),
            "actos_presentes": sorted(matched), "actos_faltantes": faltantes,
            "fuera_de_frontera": [{"actividad": k, "veces": v} for k, v in sorted(extra.items())],
            "ivf": ivf}

# ── M2 · Deriva del Proceso (IDP) ────────────────────────────────────
_DRIFT_EXCLUDE_RETRO = {"act_notificacion"}

def drift_causa(kb, data, cfg, razon=None):
    """Detectores de dilación: loops, ping-pong, estancamiento (criterio legal COGEP
    primero; umbral referencial solo sin término aplicable) y retroceso de etapa."""
    umb, pts = cfg.get("umbrales", {}), cfg.get("puntos_drift", {})
    proc = _detect_procedimiento(kb, data)
    acts = sorted((data.get("actividades") or []), key=lambda a: str(a.get("FechaProvidencia") or ""))
    findings = []

    # 1) Loops — misma providencia repetida ≥ k veces
    loop_k = safe_int(umb.get("loop_k", 3), 3)
    counts = {}
    for a in acts:
        k = _norm_prov(a.get("NombreProvidencia"))
        if k: counts[k] = counts.get(k, 0) + 1
    for k, n in counts.items():
        if n >= loop_k:
            findings.append({"tipo": "loop", "severidad": "alta", "puntos": pts.get("loop", 20),
                             "detalle": f"'{k[:80]}' se repite {n} veces (umbral configurado: {loop_k}). Posible patrón dilatorio."})

    # 2) Ping-pong — alternancia A→B→A→B de actos ontológicos
    seq = []
    for a in acts:
        m = _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))
        seq.append(m["id"] if m else None)
    i = 0
    while i + 3 < len(seq):
        a1, b1, a2, b2 = seq[i:i+4]
        if a1 and b1 and a1 != b1 and a1 == a2 and b1 == b2:
            findings.append({"tipo": "pingpong", "severidad": "alta", "puntos": pts.get("pingpong", 15),
                             "detalle": f"Alternancia {a1} ↔ {b1} desde la actuación #{i+1}."})
            i += 4
        else:
            i += 1

    # 3) Estancamiento — criterio primario: término legal COGEP incumplido (razonador)
    razon = razon or razonar_expediente(data)
    reglas_eval = razon.get("resultados", []) if isinstance(razon, dict) else []
    actos_con_regla = set()
    for r in reglas_eval:
        if r.get("estado") == "NO_EVALUABLE": continue
        actos_con_regla.update([r.get("acto_desde"), r.get("acto_hasta")])
        if r.get("estado") == "INCUMPLE":
            findings.append({"tipo": "estancamiento_legal", "severidad": "critica",
                             "puntos": pts.get("estancamiento_legal", 25), "articulo": r.get("articulo"),
                             "detalle": (f"{r.get('nombre')}: {r.get('dias')} días hábiles frente a un término de "
                                         f"{r.get('termino_dias')} ({r.get('articulo')} COGEP).")})
    # criterio de respaldo (sin fundamento normativo — solo referencial)
    gap_ref = safe_int(umb.get("gap_referencial_dias", 60), 60)
    prev_f, prev_n = None, ""
    for a in acts:
        f = _parse_dt_str(a.get("FechaProvidencia"))
        if not f: continue
        if prev_f:
            gap = business_days(prev_f, f)
            m = _match_acto(kb, a.get("NombreProvidencia"), a.get("TipoProvidencia"))
            if gap > gap_ref and (not m or m["id"] not in actos_con_regla):
                findings.append({"tipo": "estancamiento_ref", "severidad": "media",
                                 "puntos": pts.get("estancamiento_ref", 10),
                                 "detalle": (f"{gap} días hábiles sin término COGEP aplicable entre '{prev_n[:50]}' y "
                                             f"'{_norm_prov(a.get('NombreProvidencia'))[:50]}' "
                                             f"(umbral referencial configurado: {gap_ref}; sin fundamento normativo).")})
        prev_f, prev_n = f, _norm_prov(a.get("NombreProvidencia"))

    # 4) Retroceso de etapa
    etapa_idx = {}
    for i_e, e in enumerate(proc.get("etapas", [])):
        for aid in e.get("actos", []):
            etapa_idx.setdefault(aid, i_e)
    max_idx, retros = -1, 0
    for s in seq:
        if not s or s in _DRIFT_EXCLUDE_RETRO or s not in etapa_idx: continue
        idx = etapa_idx[s]
        if idx < max_idx and retros < 3:
            retros += 1
            findings.append({"tipo": "retroceso", "severidad": "alta", "puntos": pts.get("retroceso", 20),
                             "detalle": f"Acto '{s}' (etapa {idx+1}) posterior a actos de la etapa {max_idx+1}."})
        max_idx = max(max_idx, idx)

    idp = min(100, sum(f.get("puntos", 0) for f in findings))
    return {"procedimiento": proc.get("id"), "idp": idp, "n_findings": len(findings),
            "findings": findings, "disclaimer": DISCLAIMER}

# ── Analyze: corrida batch sobre todo /data/LegalCase ────────────────
def compute_salud_global():
    kb, cfg = load_kb(), load_adapt_cfg()
    if "error" in kb: return kb
    causas, por_proc = [], {}
    tot_eval, tot_cumple = 0, 0
    for name, label, juicio, d in _iter_causas():
        r = razonar_expediente(d)
        if not isinstance(r, dict) or "error" in r: continue
        v  = variabilidad_causa(kb, d)
        dr = drift_causa(kb, d, cfg, r)
        pid = r.get("procedimiento", {}).get("id") or "?"
        row = {"file": name, "juicio": juicio, "label": label, "procedimiento": pid,
               "salud": r.get("salud"), "evaluadas": r.get("evaluadas", 0),
               "cumple": r.get("cumple", 0), "alertas": r.get("alertas", 0),
               "incumplimientos": r.get("incumplimientos", 0),
               "ivf": v["ivf"], "idp": dr["idp"], "drift_findings": dr["n_findings"],
               "fuera_de_frontera": len(v["fuera_de_frontera"])}
        causas.append(row)
        tot_eval += row["evaluadas"]; tot_cumple += row["cumple"]
        pp = por_proc.setdefault(pid, {"procedimiento": pid, "n_causas": 0, "evaluadas": 0,
                                       "cumple": 0, "incumplimientos": 0, "salud_sum": 0.0, "salud_n": 0})
        pp["n_causas"] += 1; pp["evaluadas"] += row["evaluadas"]; pp["cumple"] += row["cumple"]
        pp["incumplimientos"] += row["incumplimientos"]
        if row["salud"] is not None: pp["salud_sum"] += row["salud"]; pp["salud_n"] += 1
    for pp in por_proc.values():
        pp["indice"] = round(100.0 * pp["cumple"] / max(1, pp["evaluadas"]), 1)
        pp["salud_media"] = round(pp["salud_sum"] / pp["salud_n"], 1) if pp["salud_n"] else None
        pp.pop("salud_sum"); pp.pop("salud_n")
    con_salud = [c["salud"] for c in causas if c["salud"] is not None]
    indice = round(100.0 * tot_cumple / max(1, tot_eval), 1)
    out = {"indice_global": indice,
           "salud_media": round(sum(con_salud) / len(con_salud), 1) if con_salud else None,
           "actos_en_plazo": tot_cumple, "actos_evaluables": tot_eval,
           "n_causas": len(causas), "por_procedimiento": sorted(por_proc.values(), key=lambda x: -x["n_causas"]),
           "causas": causas, "disclaimer": DISCLAIMER,
           "contexto_adaptacion": _contexto_adaptacion("salud_global", {"n_causas": len(causas)})}
    # Execute + M5: persistir y asentar en bitácora solo si el índice cambió
    try:
        prev = json.loads(SALUD_CACHE.read_text(encoding="utf-8")) if SALUD_CACHE.exists() else {}
        if prev.get("indice_global") != indice:
            bitacora_log("sistema-adaptativo", "recalculo_salud_global",
                         f"Índice empírico {prev.get('indice_global', '—')} → {indice} "
                         f"({tot_cumple}/{tot_eval} actos en plazo, {len(causas)} causas). "
                         f"kb={out['contexto_adaptacion']['kb_hash'][:8]} feriados={out['contexto_adaptacion']['feriados_hash'][:8]}",
                         refs=["/api/cogep/salud-global"], tipo="adaptacion")
        SALUD_CACHE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception: pass
    return out

# ── Endpoints ────────────────────────────────────────────────────────
@app.get("/api/cogep/salud-global", summary="Índice empírico procesal (batch sobre /data/LegalCase)", tags=["Adaptativo (MAPE-K)"])
def get_salud_global():
    return compute_salud_global()

@app.get("/api/adaptativo/config", summary="Configuración de métricas del usuario (pesos/umbrales)", tags=["Adaptativo (MAPE-K)"])
def get_adapt_config():
    return load_adapt_cfg()

@app.post("/api/adaptativo/config", summary="Guardar configuración (normaliza pesos, asienta en bitácora)", tags=["Adaptativo (MAPE-K)"])
def post_adapt_config(payload: dict = Body(...)):
    cfg = load_adapt_cfg()
    for k in ("pesos_ranking", "puntos_drift", "umbrales"):
        if isinstance(payload.get(k), dict): cfg[k].update(payload[k])
    if "peso_empirico_radar" in payload:
        try: cfg["peso_empirico_radar"] = min(1.0, max(0.0, float(payload["peso_empirico_radar"])))
        except (TypeError, ValueError): pass
    tot = sum(max(0.0, float(v or 0)) for v in cfg["pesos_ranking"].values()) or 1.0
    cfg["pesos_ranking"] = {k: round(max(0.0, float(v or 0)) / tot, 4) for k, v in cfg["pesos_ranking"].items()}
    cfg["actualizado"] = utcnow_iso()
    cfg["actor"] = str(payload.get("actor", "usuario"))[:80]
    ADAPT_CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    bitacora_log(cfg["actor"], "config_metricas_adaptativas",
                 f"pesos_ranking={cfg['pesos_ranking']} peso_empirico_radar={cfg['peso_empirico_radar']} "
                 f"umbrales={cfg['umbrales']}", refs=["/api/adaptativo/config"], tipo="adaptacion")
    return {"ok": True, "config": cfg}

@app.get("/api/adaptativo/feriados", summary="Feriados y suspensiones de término (editable)", tags=["Adaptativo (MAPE-K)"])
def get_feriados():
    return load_feriados_doc()

@app.post("/api/adaptativo/feriados", summary="Guardar feriados/suspensiones (valida fechas, asienta en bitácora)", tags=["Adaptativo (MAPE-K)"])
def post_feriados(payload: dict = Body(...)):
    doc = load_feriados_doc()
    def _valid_date(s):
        try: datetime.strptime(str(s)[:10], "%Y-%m-%d"); return True
        except ValueError: return False
    if isinstance(payload.get("feriados"), list):
        fer = [f for f in payload["feriados"] if isinstance(f, dict) and _valid_date(f.get("fecha"))]
        doc["feriados"] = sorted(({"fecha": str(f["fecha"])[:10], "motivo": str(f.get("motivo", ""))[:120],
                                   "ambito": str(f.get("ambito", "nacional"))[:40],
                                   "fuente": str(f.get("fuente", "usuario"))[:120]} for f in fer),
                                 key=lambda x: x["fecha"])
    if isinstance(payload.get("suspensiones"), list):
        doc["suspensiones"] = [{"desde": str(s["desde"])[:10], "hasta": str(s["hasta"])[:10],
                                "motivo": str(s.get("motivo", ""))[:160]}
                               for s in payload["suspensiones"]
                               if isinstance(s, dict) and _valid_date(s.get("desde")) and _valid_date(s.get("hasta"))]
    meta = doc.setdefault("meta", {})
    meta["actualizado"] = utcnow_iso(); meta["actor"] = str(payload.get("actor", "usuario"))[:80]
    FERIADOS_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    bitacora_log(meta["actor"], "edicion_feriados_judiciales",
                 f"{len(doc.get('feriados', []))} feriados, {len(doc.get('suspensiones', []))} suspensiones. "
                 "Afecta el cómputo de días hábiles (Art. 77 COGEP) de todos los dictámenes.",
                 refs=["/api/adaptativo/feriados"], tipo="adaptacion")
    return {"ok": True, "feriados": len(doc.get("feriados", [])), "suspensiones": len(doc.get("suspensiones", []))}

@app.get("/api/adaptativo/variabilidad", summary="M1 · IVF de una causa (contexto fáctico vs flujo canónico)", tags=["Adaptativo (MAPE-K)"])
def get_variabilidad(file: str = ""):
    kb = load_kb()
    if "error" in kb: return kb
    d = get_expediente(file)
    if "error" in d: return d
    out = variabilidad_causa(kb, d)
    out["juicio"] = d.get("juicio"); out["contexto_adaptacion"] = _contexto_adaptacion("variabilidad")
    return out

@app.get("/api/adaptativo/drift", summary="M2 · Deriva procesal de una causa (loops, ping-pong, estancamiento, retroceso)", tags=["Adaptativo (MAPE-K)"])
def get_drift(file: str = ""):
    kb, cfg = load_kb(), load_adapt_cfg()
    if "error" in kb: return kb
    d = get_expediente(file)
    if "error" in d: return d
    out = drift_causa(kb, d, cfg)
    out["juicio"] = d.get("juicio"); out["contexto_adaptacion"] = _contexto_adaptacion("drift")
    return out

@app.get("/api/adaptativo/ranking", summary="Ranking de juicios por proceso según métricas del usuario", tags=["Adaptativo (MAPE-K)"])
def get_ranking(proc: str = ""):
    """Score de riesgo = w_salud·(100−salud) + w_var·IVF + w_drift·IDP, con pesos
    fijados por el usuario en /api/adaptativo/config. Peor score = primero."""
    cfg = load_adapt_cfg()
    sg  = compute_salud_global()
    if "error" in sg: return sg
    w = cfg["pesos_ranking"]
    rows = []
    for c in sg["causas"]:
        if proc and c["procedimiento"] != proc: continue
        salud = c["salud"] if c["salud"] is not None else 50.0
        riesgo = round(w.get("salud", .5) * (100 - salud) + w.get("variabilidad", .25) * c["ivf"]
                       + w.get("drift", .25) * c["idp"], 1)
        rows.append({**c, "riesgo": riesgo})
    rows.sort(key=lambda r: -r["riesgo"])
    for i, r in enumerate(rows, 1): r["rank"] = i
    procs = sorted({c["procedimiento"] for c in sg["causas"]})
    return {"proc": proc or "TODOS", "procedimientos": procs, "pesos": w,
            "n": len(rows), "ranking": rows, "indice_global": sg["indice_global"],
            "por_procedimiento": sg["por_procedimiento"],
            "contexto_adaptacion": sg["contexto_adaptacion"], "disclaimer": DISCLAIMER}

@app.get("/api/adaptativo/alertas", summary="M6 · Seguridad cognitiva: alertas de aspectos fuera de ley", tags=["Adaptativo (MAPE-K)"])
def get_alertas(file: str = ""):
    kb, cfg = load_kb(), load_adapt_cfg()
    if "error" in kb: return kb
    alertas = []
    for name, label, juicio, d in _iter_causas():
        if file and name != file: continue
        r = razonar_expediente(d)
        if not isinstance(r, dict) or "error" in r: continue
        for res in r.get("resultados", []):
            if res.get("estado") == "INCUMPLE":
                alertas.append({"nivel": "critica", "tipo": "termino_vencido", "juicio": juicio, "file": name,
                                "articulo": res.get("articulo"), "titulo": f"Término legal vencido — {res.get('nombre')}",
                                "hecho": f"{res.get('dias')} días hábiles (término: {res.get('termino_dias')}) "
                                         f"entre {res.get('desde_fecha')} y {res.get('hasta_fecha')}.",
                                "fundamento": f"{res.get('articulo')} COGEP · Art. 93 COGEP (sanción por incumplimiento)"})
        dr = drift_causa(kb, d, cfg, r)
        for f in dr["findings"]:
            if f["tipo"] in ("loop", "pingpong", "retroceso"):
                alertas.append({"nivel": "alta", "tipo": f"drift_{f['tipo']}", "juicio": juicio, "file": name,
                                "titulo": "Patrón de tramitación con posible dilación",
                                "hecho": f["detalle"], "fundamento": "Detector M2 (process drift) — patrón, no conducta"})
        v = variabilidad_causa(kb, d)
        for x in v["fuera_de_frontera"]:
            alertas.append({"nivel": "media", "tipo": "fuera_de_frontera", "juicio": juicio, "file": name,
                            "titulo": "Actuación fuera de la frontera ontológica (guardrail M4)",
                            "hecho": f"'{x['actividad'][:90]}' ({x['veces']}×) no resuelve a ningún acto de la ontología COGEP.",
                            "fundamento": "Derivada a criterio humano — el sistema no clasifica fuera de su vocabulario"})
    orden = {"critica": 0, "alta": 1, "media": 2}
    alertas.sort(key=lambda a: (orden.get(a["nivel"], 3), a["juicio"]))
    return {"n": len(alertas),
            "por_nivel": {k: sum(1 for a in alertas if a["nivel"] == k) for k in ("critica", "alta", "media")},
            "alertas": alertas, "disclaimer": DISCLAIMER,
            "contexto_adaptacion": _contexto_adaptacion("alertas")}


# ═══════════════════════════════════════════════════════════════════
#  VALIDACIÓN ADAPTATIVA (PLAN_VALIDACION_ADAPTATIVA.md)
#  A1 gold standard + eval del razonador · A2 cambio normativo ·
#  A3 rúbrica + AHP + sensibilidad · A4 OWL + CQs · A5 muestra ·
#  Panel de supuestos del experto con límites min-max.
# ═══════════════════════════════════════════════════════════════════
GOLD_DIR       = DATA_DIR / "gold"
GOLD_PATH      = GOLD_DIR / "gold_standard.json"
EVAL_REPORT    = GOLD_DIR / "eval_report.json"
RUBRICA_PATH   = DATA_DIR / "rubrica_dimensiones.json"
EVID_DIM_PATH  = DATA_DIR / "evidencia_dimensiones.json"
KB_CHANGELOG   = DATA_DIR / "kb_changelog.json"
CQ_PATH        = DATA_DIR / "competency_questions.json"
COGEP_OWL_PATH = DATA_DIR / "COGEP_ontology.owl"

def _jload(p, default):
    try: return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception: return default

def _jsave(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

# ── M3 · versión de regla vigente a la fecha del acto ───────────────
def _regla_efectiva(regla, fecha):
    hist = regla.get("historial") or []
    if not hist or not fecha: return regla
    fd = fecha.strftime("%Y-%m-%d") if hasattr(fecha, "strftime") else str(fecha)[:10]
    best = None
    for h in hist:
        vd = str(h.get("vigencia_desde", ""))[:10]
        vh = str(h.get("vigencia_hasta") or "9999-12-31")[:10]
        if vd and vd <= fd <= vh and (best is None or vd >= str(best.get("vigencia_desde", ""))[:10]):
            best = h
    if not best: return regla
    r = dict(regla)
    r.update({k: v for k, v in best.items() if k in ("termino_dias", "texto_norma", "articulo")})
    r["_version_vigente_desde"] = best.get("vigencia_desde")
    return r

# ── Panel de Supuestos del experto (todo valor asumido, con min-max) ─
SUPUESTOS_DEF = [
    {"clave": "pesos_ranking.salud",        "grupo": "Ranking", "nombre": "Peso: salud procesal",      "min": 0,   "max": 1,   "paso": 0.05, "descripcion": "Peso de (100−salud) en el score de riesgo. Se normaliza con los otros dos."},
    {"clave": "pesos_ranking.variabilidad", "grupo": "Ranking", "nombre": "Peso: variabilidad (IVF)",  "min": 0,   "max": 1,   "paso": 0.05, "descripcion": "Peso del Índice de Variabilidad Fáctica en el riesgo."},
    {"clave": "pesos_ranking.drift",        "grupo": "Ranking", "nombre": "Peso: deriva (IDP)",        "min": 0,   "max": 1,   "paso": 0.05, "descripcion": "Peso del Índice de Deriva Procesal en el riesgo."},
    {"clave": "peso_empirico_radar",        "grupo": "Radar",   "nombre": "Peso empírico en el radar", "min": 0,   "max": 1,   "paso": 0.05, "descripcion": "Mezcla del índice empírico con el score declarado en la dimensión LegalTech."},
    {"clave": "psi.root",                   "grupo": "Radar",   "nombre": "Ψ: peso del concepto raíz", "min": 0.1, "max": 0.9, "paso": 0.05, "descripcion": "w_root en Ψ(d); subs = 1 − root. Justificable vía AHP (tab Validación)."},
    {"clave": "puntos_drift.loop",          "grupo": "Drift",   "nombre": "Puntos: loop",              "min": 0,   "max": 50,  "paso": 1,    "descripcion": "Puntos de IDP por providencia repetida ≥ k veces."},
    {"clave": "puntos_drift.pingpong",      "grupo": "Drift",   "nombre": "Puntos: ping-pong",         "min": 0,   "max": 50,  "paso": 1,    "descripcion": "Puntos de IDP por alternancia A→B→A→B."},
    {"clave": "puntos_drift.estancamiento_legal", "grupo": "Drift", "nombre": "Puntos: estancamiento legal", "min": 0, "max": 50, "paso": 1, "descripcion": "Puntos por término COGEP incumplido (criterio normativo)."},
    {"clave": "puntos_drift.estancamiento_ref",   "grupo": "Drift", "nombre": "Puntos: estancamiento referencial", "min": 0, "max": 50, "paso": 1, "descripcion": "Puntos por gap sin término aplicable (criterio referencial, no normativo)."},
    {"clave": "puntos_drift.retroceso",     "grupo": "Drift",   "nombre": "Puntos: retroceso de etapa","min": 0,   "max": 50,  "paso": 1,    "descripcion": "Puntos por acto de etapa anterior tras etapa posterior."},
    {"clave": "umbrales.loop_k",            "grupo": "Drift",   "nombre": "Umbral: repeticiones (k)",  "min": 2,   "max": 10,  "paso": 1,    "descripcion": "Repeticiones mínimas de una providencia para marcar loop."},
    {"clave": "umbrales.gap_referencial_dias", "grupo": "Drift","nombre": "Umbral: gap referencial",   "min": 5,   "max": 365, "paso": 5,    "descripcion": "Días hábiles sin término aplicable para marcar estancamiento referencial."},
    {"clave": "umbrales_razonador.incumple_factor", "grupo": "Razonador", "nombre": "Factor ALERTA→INCUMPLE", "min": 1.0, "max": 2.0, "paso": 0.05, "descripcion": "días ≤ término ⇒ CUMPLE · ≤ término×factor ⇒ ALERTA · mayor ⇒ INCUMPLE."},
    {"clave": "f1_min",                     "grupo": "Validez IA", "nombre": "Umbral de aceptación F1", "min": 0.5, "max": 1.0, "paso": 0.01, "descripcion": "F1 mínimo del mapeo providencia→acto para considerar el razonador apto como indicador agregado."},
]

def _cfg_get(cfg, dotted):
    cur = cfg
    for k in dotted.split("."):
        if not isinstance(cur, dict) or k not in cur: return None
        cur = cur[k]
    return cur

def _cfg_set(cfg, dotted, v):
    ks = dotted.split(".")
    cur = cfg
    for k in ks[:-1]: cur = cur.setdefault(k, {})
    cur[ks[-1]] = v

@app.get("/api/adaptativo/supuestos", summary="Supuestos del experimento (valor, min, max, procedencia)", tags=["Adaptativo (MAPE-K)"])
def get_supuestos():
    cfg = load_adapt_cfg()
    w_root, _ = _psi_weights()
    ahp = _jload(PESOS_AHP_PATH, {})
    out = []
    for s in SUPUESTOS_DEF:
        if s["clave"] == "psi.root":
            val, proc = w_root, ahp.get("procedencia", "default 0.40/0.60 (sin AHP)")
        else:
            val, proc = _cfg_get(cfg, s["clave"]), ("configurado por " + str(cfg.get("actor", "sistema"))) if cfg.get("actualizado") else "default del sistema"
        out.append({**s, "valor": val, "procedencia": proc})
    return {"supuestos": out, "actualizado": cfg.get("actualizado"), "actor": cfg.get("actor"),
            "nota": "Todo valor asumido de la simulación es configurable aquí dentro de sus límites; cada cambio queda en bitácora."}

@app.post("/api/adaptativo/supuestos", summary="Fijar supuestos (valida min-max, asienta en bitácora)", tags=["Adaptativo (MAPE-K)"])
def post_supuestos(payload: dict = Body(...)):
    valores = payload.get("valores") or {}
    actor = str(payload.get("actor", "usuario-experto"))[:80]
    cfg = load_adapt_cfg()
    aplicados, rechazados = {}, {}
    for s in SUPUESTOS_DEF:
        k = s["clave"]
        if k not in valores: continue
        try: v = float(valores[k])
        except (TypeError, ValueError):
            rechazados[k] = "no numérico"; continue
        if v < s["min"] or v > s["max"]:
            rechazados[k] = f"fuera de rango [{s['min']}, {s['max']}]"; continue
        if s["paso"] == 1: v = int(round(v))
        if k == "psi.root":
            ahp = _jload(PESOS_AHP_PATH, {})
            ahp["psi"] = {"root": round(v, 4), "subs": round(1 - v, 4)}
            ahp["procedencia"] = f"panel de supuestos ({actor})"
            _jsave(PESOS_AHP_PATH, ahp)
        else:
            _cfg_set(cfg, k, v)
        aplicados[k] = v
    if aplicados:
        tot = sum(max(0.0, float(v or 0)) for v in cfg["pesos_ranking"].values()) or 1.0
        cfg["pesos_ranking"] = {k: round(max(0.0, float(v or 0)) / tot, 4) for k, v in cfg["pesos_ranking"].items()}
        cfg["actualizado"] = utcnow_iso(); cfg["actor"] = actor
        ADAPT_CFG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        bitacora_log(actor, "supuestos_experimento", f"aplicados={aplicados} rechazados={rechazados}",
                     refs=["/api/adaptativo/supuestos"], tipo="adaptacion")
    return {"ok": True, "aplicados": aplicados, "rechazados": rechazados}

# ── A1 · Gold standard + evaluación del razonador ────────────────────
@app.get("/api/eval/gold", summary="A1 · Anotaciones gold standard + progreso", tags=["Validez IA"])
def get_gold():
    g = _jload(GOLD_PATH, {"anotaciones": []})
    an = g.get("anotaciones", [])
    por_proc, anotadores = {}, {}
    kbp = load_kb()
    for a in an:
        por_proc[a.get("procedimiento", "?")] = por_proc.get(a.get("procedimiento", "?"), 0) + 1
        anotadores[a.get("anotador", "?")] = anotadores.get(a.get("anotador", "?"), 0) + 1
    actos = [{"id": x["id"], "nombre": x["nombre"], "articulo": x.get("articulo", "")} for x in kbp.get("actos", [])] if "error" not in kbp else []
    return {"n": len(an), "por_procedimiento": por_proc, "anotadores": anotadores,
            "anotaciones": an, "actos_catalogo": actos,
            "veredictos": ["CUMPLE", "ALERTA", "INCUMPLE", "NO_EVALUABLE"]}

@app.get("/api/eval/causa", summary="A1 · Actuaciones de una causa para anotar (con predicción actual)", tags=["Validez IA"])
def get_eval_causa(file: str = ""):
    kb = load_kb()
    if "error" in kb: return kb
    d = get_expediente(file)
    if "error" in d: return d
    proc = _detect_procedimiento(kb, d)
    g = _jload(GOLD_PATH, {"anotaciones": []})
    previas = {(a.get("seq")): a for a in g.get("anotaciones", []) if a.get("file") == Path(file).name}
    filas = []
    for p in d.get("pasos", []):
        m = _match_acto(kb, p.get("NombreProvidencia"), p.get("TipoProvidencia"))
        filas.append({"seq": p["seq"], "actividad": p.get("NombreProvidencia"), "tipo": p.get("TipoProvidencia"),
                      "fecha": str(p.get("FechaProvidencia") or "")[:10],
                      "acto_predicho": m["id"] if m else "ninguno",
                      "anotacion": previas.get(p["seq"])})
    return {"file": Path(file).name, "juicio": d.get("juicio"), "procedimiento": proc.get("id"), "filas": filas}

@app.post("/api/eval/gold", summary="A1 · Guardar anotaciones del abogado (upsert)", tags=["Validez IA"])
def post_gold(payload: dict = Body(...)):
    nuevas = payload.get("anotaciones") or []
    anotador = str(payload.get("anotador", "")).strip()
    if not anotador: return {"error": "se requiere 'anotador'"}
    g = _jload(GOLD_PATH, {"anotaciones": []})
    idx = {(a.get("file"), a.get("seq"), a.get("anotador")): i for i, a in enumerate(g["anotaciones"])}
    n_up = 0
    for a in nuevas:
        if not a.get("file") or a.get("seq") is None or not a.get("acto_correcto"): continue
        e = {"file": str(a["file"]), "seq": int(a["seq"]), "actividad": str(a.get("actividad", ""))[:160],
             "procedimiento": str(a.get("procedimiento", ""))[:20],
             "acto_correcto": str(a["acto_correcto"])[:40],
             "veredicto_correcto": str(a.get("veredicto_correcto", ""))[:14] or None,
             "anotador": anotador[:80], "fecha": utcnow_iso(), "notas": str(a.get("notas", ""))[:300]}
        key = (e["file"], e["seq"], anotador)
        if key in idx: g["anotaciones"][idx[key]] = e
        else: idx[key] = len(g["anotaciones"]); g["anotaciones"].append(e)
        n_up += 1
    _jsave(GOLD_PATH, g)
    bitacora_log(anotador, "anotacion_gold_standard", f"{n_up} actuaciones anotadas/actualizadas (total {len(g['anotaciones'])}).",
                 refs=["/api/eval/gold"], tipo="adaptacion")
    return {"ok": True, "guardadas": n_up, "total": len(g["anotaciones"])}

def _prf(conf, labels):
    """precision/recall/F1 macro desde una matriz de confusión dict[gold][pred]."""
    per = {}
    for c in labels:
        tp = conf.get(c, {}).get(c, 0)
        fp = sum(conf.get(g, {}).get(c, 0) for g in labels if g != c)
        fn = sum(conf.get(c, {}).get(p, 0) for p in labels if p != c)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec  = tp / (tp + fn) if (tp + fn) else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per[c] = {"precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3), "n": tp + fn}
    usados = [c for c in labels if per[c]["n"] > 0]
    macro = {k: round(sum(per[c][k] for c in usados) / max(1, len(usados)), 3) for k in ("precision", "recall", "f1")}
    return per, macro

@app.post("/api/eval/run", summary="A1 · Evaluar el razonador contra el gold standard (F1, matriz, kappa)", tags=["Validez IA"])
def post_eval_run(payload: dict = Body(default={})):
    kb = load_kb()
    if "error" in kb: return kb
    g = _jload(GOLD_PATH, {"anotaciones": []})
    an = g.get("anotaciones", [])
    if not an: return {"error": "no hay anotaciones gold; anote actuaciones primero"}
    causas_cache, razon_cache = {}, {}
    conf, errores, aciertos, total = {}, [], 0, 0
    v_conf, v_tot, v_ok = {}, 0, 0
    for a in an:
        f = a["file"]
        if f not in causas_cache:
            causas_cache[f] = get_expediente(f)
        d = causas_cache[f]
        if "error" in d: continue
        paso = next((p for p in d.get("pasos", []) if p["seq"] == a["seq"]), None)
        if not paso: continue
        m = _match_acto(kb, paso.get("NombreProvidencia"), paso.get("TipoProvidencia"))
        pred, gold = (m["id"] if m else "ninguno"), a["acto_correcto"]
        conf.setdefault(gold, {}); conf[gold][pred] = conf[gold].get(pred, 0) + 1
        total += 1
        if pred == gold: aciertos += 1
        else: errores.append({"file": f, "seq": a["seq"], "actividad": a.get("actividad", ""),
                              "gold": gold, "prediccion": pred, "anotador": a.get("anotador")})
        # veredicto: comparar estado de la regla cuyo acto_hasta = acto anotado
        if a.get("veredicto_correcto"):
            if f not in razon_cache: razon_cache[f] = razonar_expediente(d)
            r = razon_cache[f]
            res = next((x for x in r.get("resultados", []) if x.get("acto_hasta") == gold), None)
            estado = res.get("estado") if res else "NO_EVALUABLE"
            v_conf.setdefault(a["veredicto_correcto"], {})
            v_conf[a["veredicto_correcto"]][estado] = v_conf[a["veredicto_correcto"]].get(estado, 0) + 1
            v_tot += 1
            if estado == a["veredicto_correcto"]: v_ok += 1
    labels = sorted({l for l in list(conf.keys()) + [p for v in conf.values() for p in v]})
    per_clase, macro = _prf(conf, labels)
    # kappa de Cohen si hay 2 anotadores con ítems comunes
    kappa = None
    por_anot = {}
    for a in an: por_anot.setdefault(a["anotador"], {})[(a["file"], a["seq"])] = a["acto_correcto"]
    if len(por_anot) >= 2:
        (a1, m1), (a2, m2) = list(por_anot.items())[:2]
        comunes = set(m1) & set(m2)
        if len(comunes) >= 10:
            po = sum(1 for k in comunes if m1[k] == m2[k]) / len(comunes)
            cats = {m1[k] for k in comunes} | {m2[k] for k in comunes}
            pe = sum((sum(1 for k in comunes if m1[k] == c) / len(comunes)) *
                     (sum(1 for k in comunes if m2[k] == c) / len(comunes)) for c in cats)
            kappa = round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0
            kappa = {"valor": kappa, "anotadores": [a1, a2], "n_comunes": len(comunes)}
    cfg = load_adapt_cfg()
    report = {"n_anotaciones": total, "exactitud_mapeo": round(aciertos / max(1, total), 3),
              "macro": macro, "por_clase": per_clase, "matriz_confusion": conf, "labels": labels,
              "veredicto": {"n": v_tot, "exactitud": round(v_ok / max(1, v_tot), 3) if v_tot else None,
                            "matriz": v_conf},
              "errores": errores[:60], "kappa": kappa,
              "f1_min_aceptado": cfg.get("f1_min", 0.85),
              "apto": macro["f1"] >= float(cfg.get("f1_min", 0.85)),
              "contexto_adaptacion": _contexto_adaptacion("eval_razonador", {"n_gold": total})}
    _jsave(EVAL_REPORT, report)
    bitacora_log("evaluador", "evaluacion_razonador",
                 f"N={total} · exactitud={report['exactitud_mapeo']} · F1_macro={macro['f1']} · "
                 f"apto={'SÍ' if report['apto'] else 'NO'} (umbral {report['f1_min_aceptado']})",
                 refs=["/api/eval/run"], tipo="adaptacion")
    return report

@app.get("/api/eval/report", summary="A1 · Último reporte de evaluación (chip de validez)", tags=["Validez IA"])
def get_eval_report():
    r = _jload(EVAL_REPORT, None)
    if not r: return {"disponible": False, "chip": "sin validez medida"}
    return {"disponible": True, "chip": f"F1 {r['macro']['f1']} · N={r['n_anotaciones']}",
            "apto": r.get("apto"), **r}

# ── A2 · Cambio normativo / jurisprudencial ──────────────────────────
@app.get("/api/adaptativo/kb-changelog", summary="A2 · Historial de cambios normativos de la KB", tags=["Adaptativo (MAPE-K)"])
def get_kb_changelog():
    kb = load_kb()
    return {"version": (kb.get("meta") or {}).get("version", "1.0"),
            "cambios": _jload(KB_CHANGELOG, []),
            "reglas": [{"id": r["id"], "nombre": r["nombre"], "articulo": r["articulo"],
                        "termino_dias": r["termino_dias"], "procedimientos": r.get("procedimientos", []),
                        "versiones": len(r.get("historial", [])) or 1} for r in kb.get("reglas", [])]}

@app.post("/api/adaptativo/kb-cambio", summary="A2 · Registrar reforma/jurisprudencia sobre una regla (validado)", tags=["Adaptativo (MAPE-K)"])
def post_kb_cambio(payload: dict = Body(...)):
    kb = load_kb()
    if "error" in kb: return kb
    rid = str(payload.get("regla_id", ""))
    regla = next((r for r in kb.get("reglas", []) if r["id"] == rid), None)
    if not regla: return {"error": f"regla desconocida (guardrail ontológico): {rid}"}
    try:
        nuevo = int(payload.get("termino_dias_nuevo"))
        assert 1 <= nuevo <= 365
    except Exception:
        return {"error": "termino_dias_nuevo debe ser un entero entre 1 y 365"}
    vd = str(payload.get("vigencia_desde", ""))[:10]
    try: datetime.strptime(vd, "%Y-%m-%d")
    except ValueError: return {"error": "vigencia_desde inválida (YYYY-MM-DD)"}
    fuente = {"tipo": str(payload.get("fuente_tipo", "reforma"))[:30],
              "ref": str(payload.get("fuente_ref", ""))[:160], "url": str(payload.get("fuente_url", ""))[:300]}
    if not fuente["ref"]: return {"error": "se requiere la referencia de la fuente (Registro Oficial / sentencia)"}
    actor = str(payload.get("actor", "usuario-experto"))[:80]
    antes = regla["termino_dias"]
    if not regla.get("historial"):
        regla["historial"] = [{"termino_dias": antes, "vigencia_desde": "2016-05-22",
                               "fuente": {"tipo": "original", "ref": regla["articulo"] + " COGEP (RO-S 506)"}}]
    regla["historial"].append({"termino_dias": nuevo, "vigencia_desde": vd, "fuente": fuente})
    regla["termino_dias"] = nuevo
    meta = kb.setdefault("meta", {})
    try: meta["version"] = str(round(float(meta.get("version", "1.0")) + 0.1, 1))
    except Exception: meta["version"] = "1.1"
    KB_PATH.write_text(json.dumps(kb, ensure_ascii=False, indent=2), encoding="utf-8")
    log = _jload(KB_CHANGELOG, [])
    cambio = {"id": len(log) + 1, "ts": utcnow_iso(), "regla_id": rid, "campo": "termino_dias",
              "antes": antes, "despues": nuevo, "vigencia_desde": vd, "fuente": fuente,
              "actor": actor, "motivo": str(payload.get("motivo", ""))[:300], "kb_version": meta["version"]}
    log.append(cambio); _jsave(KB_CHANGELOG, log)
    bitacora_log(actor, "cambio_normativo",
                 f"Regla {rid}: término {antes}→{nuevo} días desde {vd} ({fuente['tipo']}: {fuente['ref']}). KB v{meta['version']}.",
                 refs=["/api/adaptativo/kb-cambio"], tipo="adaptacion")
    return {"ok": True, "cambio": cambio, "kb_version": meta["version"]}

@app.get("/api/adaptativo/impacto", summary="A2 · Delta de dictámenes de un cambio normativo sobre el corpus", tags=["Adaptativo (MAPE-K)"])
def get_impacto(cambio: int = 0):
    log = _jload(KB_CHANGELOG, [])
    if not log: return {"error": "no hay cambios normativos registrados"}
    c = next((x for x in log if x["id"] == cambio), log[-1])
    kb = load_kb()
    umb = dict(kb.get("umbrales", {}))
    umb.update(load_adapt_cfg().get("umbrales_razonador") or {})
    deltas, n_eval = [], 0
    for name, label, juicio, d in _iter_causas():
        r = razonar_expediente(d)
        if not isinstance(r, dict) or "error" in r: continue
        res = next((x for x in r.get("resultados", []) if x.get("regla") == c["regla_id"]
                    and x.get("estado") != "NO_EVALUABLE"), None)
        if not res: continue
        n_eval += 1
        e_antes  = _verdict(res["dias"], c["antes"], umb)
        e_despues = _verdict(res["dias"], c["despues"], umb)
        if e_antes != e_despues:
            deltas.append({"juicio": juicio, "file": name, "dias": res["dias"],
                           "antes": e_antes, "despues": e_despues})
    return {"cambio": c, "causas_evaluadas": n_eval, "causas_afectadas": len(deltas), "deltas": deltas,
            "contexto_adaptacion": _contexto_adaptacion("impacto_normativo", {"cambio_id": c["id"]}),
            "disclaimer": DISCLAIMER}

# ── A3 · Rúbrica + evidencia por dimensión + AHP + sensibilidad ──────
@app.get("/api/rubrica", summary="A3 · Rúbrica 0-100 por dimensión + evidencias registradas", tags=["Validez IA"])
def get_rubrica():
    return {"rubrica": _jload(RUBRICA_PATH, {}), "evidencias": _jload(EVID_DIM_PATH, {})}

@app.post("/api/rubrica/evidencia", summary="A3 · Registrar evidencia documental de una dimensión", tags=["Validez IA"])
def post_evidencia_dim(payload: dict = Body(...)):
    dim = str(payload.get("dimension", "")).upper()
    if dim not in {d["key"] for d in DIMENSIONS}: return {"error": f"dimensión desconocida: {dim}"}
    e = {"url": str(payload.get("url", ""))[:400], "snapshot_ref": str(payload.get("snapshot_ref", ""))[:160],
         "extracto": str(payload.get("extracto", ""))[:400], "criterio_rubrica": str(payload.get("criterio", ""))[:200],
         "actor": str(payload.get("actor", "usuario-experto"))[:80], "fecha": utcnow_iso()}
    if not e["url"] and not e["snapshot_ref"]: return {"error": "se requiere url o snapshot_ref"}
    ev = _jload(EVID_DIM_PATH, {})
    ev.setdefault(dim, []).append(e)
    _jsave(EVID_DIM_PATH, ev)
    bitacora_log(e["actor"], "evidencia_dimension", f"{dim}: {e['url'] or e['snapshot_ref']}",
                 refs=["/api/rubrica/evidencia"], tipo="adaptacion")
    return {"ok": True, "dimension": dim, "n": len(ev[dim])}

def _ahp_eigen(M):
    n = len(M)
    w = [1.0 / n] * n
    for _ in range(100):
        nw = [sum(M[i][j] * w[j] for j in range(n)) for i in range(n)]
        s = sum(nw) or 1.0
        w = [x / s for x in nw]
    lam = sum(sum(M[i][j] * w[j] for j in range(n)) / w[i] for i in range(n)) / n
    RI = {1: 0, 2: 0, 3: .58, 4: .9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45}.get(n, 1.49)
    CI = (lam - n) / (n - 1) if n > 1 else 0.0
    return [round(x, 4) for x in w], round(lam, 3), (round(CI / RI, 4) if RI else 0.0)

@app.get("/api/ahp", summary="A3 · Pesos Ψ vigentes y juicios de expertos", tags=["Validez IA"])
def get_ahp():
    d = _jload(PESOS_AHP_PATH, {})
    w_root, w_subs = _psi_weights()
    return {"psi": {"root": w_root, "subs": w_subs}, "procedencia": d.get("procedencia", "default 0.40/0.60 (sin AHP)"),
            "expertos": d.get("expertos_psi", []),
            "escala_saaty": [{"v": 1, "t": "igual importancia"}, {"v": 3, "t": "moderadamente más importante"},
                             {"v": 5, "t": "fuertemente más importante"}, {"v": 7, "t": "muy fuertemente"},
                             {"v": 9, "t": "extremadamente más importante"}]}

@app.post("/api/ahp", summary="A3 · Registrar juicio AHP de un experto (raíz vs subconceptos)", tags=["Validez IA"])
def post_ahp(payload: dict = Body(...)):
    experto = str(payload.get("experto", "")).strip()[:80]
    if not experto: return {"error": "se requiere 'experto'"}
    try:
        a = float(payload.get("saaty"))
        assert 1/9 <= a <= 9
    except Exception:
        return {"error": "saaty debe estar entre 1/9 y 9 (use valores negativos de UI como recíprocos)"}
    w, lam, cr = _ahp_eigen([[1, a], [1 / a, 1]])
    d = _jload(PESOS_AHP_PATH, {})
    exps = [e for e in d.get("expertos_psi", []) if e.get("experto") != experto]
    exps.append({"experto": experto, "saaty": a, "root": w[0], "subs": w[1], "cr": cr, "ts": utcnow_iso()})
    d["expertos_psi"] = exps
    root_m = round(sum(e["root"] for e in exps) / len(exps), 4)
    d["psi"] = {"root": root_m, "subs": round(1 - root_m, 4)}
    d["procedencia"] = f"AHP ({len(exps)} experto(s), media aritmética; CR=0 en matriz 2×2)"
    _jsave(PESOS_AHP_PATH, d)
    bitacora_log(experto, "juicio_ahp_psi", f"saaty={a} → root={w[0]} · agregado root={root_m} ({len(exps)} expertos)",
                 refs=["/api/ahp"], tipo="adaptacion")
    return {"ok": True, "experto": {"root": w[0], "subs": w[1]}, "agregado": d["psi"], "n_expertos": len(exps)}

@app.get("/api/sensibilidad", summary="A3 · Sensibilidad ±10/20% de pesos Ψ y del ranking (tornado)", tags=["Validez IA"])
def get_sensibilidad():
    base_root, _ = _psi_weights()
    tornado = []
    try:
        for f in (-0.20, -0.10, 0.0, 0.10, 0.20):
            r = min(0.9, max(0.1, base_root * (1 + f)))
            _PSI_OVERRIDE["w"] = (r, round(1 - r, 4))
            v = compute_validation("SDT_CJ.json")
            tornado.append({"delta_pct": int(f * 100), "root": round(r, 3),
                            "overall_dt": v.get("overall_dt"), "legaltech": (v.get("legaltech_dim") or {}).get("dt_score")})
    finally:
        _PSI_OVERRIDE["w"] = None
    base_dt = next((t["overall_dt"] for t in tornado if t["delta_pct"] == 0), None)
    max_dev = max((abs((t["overall_dt"] or 0) - (base_dt or 0)) for t in tornado), default=0)
    # estabilidad del top-1 del ranking ante ±20% en cada peso
    cfg = load_adapt_cfg(); w0 = cfg["pesos_ranking"]
    sg = _jload(SALUD_CACHE, None) or compute_salud_global()
    def top1(w):
        best, bj = -1, None
        for c in sg.get("causas", []):
            salud = c["salud"] if c["salud"] is not None else 50.0
            riesgo = w["salud"] * (100 - salud) + w["variabilidad"] * c["ivf"] + w["drift"] * c["idp"]
            if riesgo > best: best, bj = riesgo, c["juicio"]
        return bj
    base_top = top1(w0); estable_rk = True; pruebas = []
    for k in w0:
        for f in (-0.2, 0.2):
            w = dict(w0); w[k] = max(0.0, w[k] * (1 + f))
            tot = sum(w.values()) or 1.0
            w = {kk: vv / tot for kk, vv in w.items()}
            t = top1(w); pruebas.append({"peso": k, "delta_pct": int(f * 100), "top1": t})
            if t != base_top: estable_rk = False
    return {"psi_base_root": base_root, "tornado": tornado, "max_desviacion_overall": round(max_dev, 2),
            "radar_estable_10pct": max((abs((t["overall_dt"] or 0) - (base_dt or 0))
                                        for t in tornado if abs(t["delta_pct"]) <= 10), default=0) < 5,
            "ranking": {"top1_base": base_top, "estable_20pct": estable_rk, "pruebas": pruebas},
            "contexto_adaptacion": _contexto_adaptacion("sensibilidad")}

# ── A4 · COGEP → OWL + verificación estructural + competency questions ─
def kb_to_owl(kb):
    NS = "http://maltg.arch/onto/cogep#"
    def esc(s): return str(s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    L = ['<?xml version="1.0"?>',
         f'<rdf:RDF xmlns:rdf="{RDF_NS}" xmlns:rdfs="{RDFS_NS}" xmlns:owl="{OWL_NS}" xmlns="{NS}" xml:base="{NS[:-1]}">',
         f'  <owl:Ontology rdf:about="{NS[:-1]}"><rdfs:comment>Ontología COGEP generada desde cogep_kb.json v{esc((kb.get("meta") or {}).get("version","1.0"))}</rdfs:comment></owl:Ontology>']
    for c in ("Procedimiento", "Etapa", "ActoProcesal", "TerminoProcesal", "SujetoProcesal"):
        L.append(f'  <owl:Class rdf:about="{NS}{c}"/>')
    for p, dom, rng in (("tieneEtapa", "Procedimiento", "Etapa"), ("contieneActo", "Etapa", "ActoProcesal"),
                        ("actoDesde", "TerminoProcesal", "ActoProcesal"), ("actoHasta", "TerminoProcesal", "ActoProcesal"),
                        ("sujetoObligado", "TerminoProcesal", "SujetoProcesal"), ("aplicaA", "TerminoProcesal", "Procedimiento"),
                        ("ejecutadoPor", "ActoProcesal", "SujetoProcesal")):
        L.append(f'  <owl:ObjectProperty rdf:about="{NS}{p}"><rdfs:domain rdf:resource="{NS}{dom}"/><rdfs:range rdf:resource="{NS}{rng}"/></owl:ObjectProperty>')
    for s in kb.get("sujetos", []):
        L.append(f'  <owl:NamedIndividual rdf:about="{NS}{esc(s["id"])}"><rdf:type rdf:resource="{NS}SujetoProcesal"/><rdfs:label>{esc(s.get("nombre"))}</rdfs:label></owl:NamedIndividual>')
    for a in kb.get("actos", []):
        suj = f'<ejecutadoPor rdf:resource="{NS}{esc(a["sujeto"])}"/>' if a.get("sujeto") else ""
        L.append(f'  <owl:NamedIndividual rdf:about="{NS}{esc(a["id"])}"><rdf:type rdf:resource="{NS}ActoProcesal"/><rdfs:label>{esc(a.get("nombre"))}</rdfs:label><rdfs:comment>{esc(a.get("articulo"))}</rdfs:comment>{suj}</owl:NamedIndividual>')
    for p in kb.get("procedimientos", []):
        ets = "".join(f'<tieneEtapa rdf:resource="{NS}{esc(e["id"])}"/>' for e in p.get("etapas", []))
        L.append(f'  <owl:NamedIndividual rdf:about="{NS}{esc(p["id"])}"><rdf:type rdf:resource="{NS}Procedimiento"/><rdfs:label>{esc(p.get("nombre"))}</rdfs:label><rdfs:comment>{esc(p.get("articulos"))}</rdfs:comment>{ets}</owl:NamedIndividual>')
        for e in p.get("etapas", []):
            acts = "".join(f'<contieneActo rdf:resource="{NS}{esc(x)}"/>' for x in e.get("actos", []))
            L.append(f'  <owl:NamedIndividual rdf:about="{NS}{esc(e["id"])}"><rdf:type rdf:resource="{NS}Etapa"/><rdfs:label>{esc(e.get("nombre"))}</rdfs:label>{acts}</owl:NamedIndividual>')
    for r in kb.get("reglas", []):
        procs = "".join(f'<aplicaA rdf:resource="{NS}{esc(x)}"/>' for x in r.get("procedimientos", []))
        suj = f'<sujetoObligado rdf:resource="{NS}{esc(r["sujeto_obligado"])}"/>' if r.get("sujeto_obligado") else ""
        L.append(f'  <owl:NamedIndividual rdf:about="{NS}{esc(r["id"])}"><rdf:type rdf:resource="{NS}TerminoProcesal"/>'
                 f'<rdfs:label>{esc(r.get("nombre"))}</rdfs:label><rdfs:comment>{esc(r.get("articulo"))} · {r.get("termino_dias")} días hábiles</rdfs:comment>'
                 f'<actoDesde rdf:resource="{NS}{esc(r["acto_desde"])}"/><actoHasta rdf:resource="{NS}{esc(r["acto_hasta"])}"/>{suj}{procs}</owl:NamedIndividual>')
    L.append('</rdf:RDF>')
    return "\n".join(L)

@app.post("/api/cogep/owl/generar", summary="A4 · Generar COGEP_ontology.owl desde la KB", tags=["Validez IA"])
def post_owl_generar():
    kb = load_kb()
    if "error" in kb: return kb
    xml = kb_to_owl(kb)
    COGEP_OWL_PATH.write_text(xml, encoding="utf-8")
    h = file_hash(COGEP_OWL_PATH)
    bitacora_log("sistema", "generacion_owl_cogep", f"COGEP_ontology.owl regenerado (sha {h[:10]}) desde KB v{(kb.get('meta') or {}).get('version','1.0')}.",
                 refs=["/api/cogep/owl/generar"], tipo="adaptacion")
    return {"ok": True, "path": "/data/COGEP_ontology.owl", "hash": h,
            "individuos": {"actos": len(kb.get("actos", [])), "reglas": len(kb.get("reglas", [])),
                           "procedimientos": len(kb.get("procedimientos", [])), "sujetos": len(kb.get("sujetos", []))}}

@app.get("/api/cogep/owl/verificacion", summary="A4 · Verificación estructural de la ontología COGEP", tags=["Validez IA"])
def get_owl_verificacion():
    kb = load_kb()
    if "error" in kb: return kb
    actos = {a["id"] for a in kb.get("actos", [])}
    sujetos = {s["id"] for s in kb.get("sujetos", [])}
    procs = {p["id"] for p in kb.get("procedimientos", [])}
    checks = []
    def chk(cid, desc, fallos):
        checks.append({"id": cid, "descripcion": desc, "ok": not fallos, "detalles": fallos[:15]})
    chk("C1", "Todo acto referenciado en etapas existe en el catálogo de actos",
        [f"{p['id']}/{e['id']}: {x}" for p in kb.get("procedimientos", []) for e in p.get("etapas", []) for x in e.get("actos", []) if x not in actos])
    chk("C2", "Toda regla referencia actos existentes (acto_desde/acto_hasta)",
        [f"{r['id']}: {x}" for r in kb.get("reglas", []) for x in (r.get("acto_desde"), r.get("acto_hasta")) if x not in actos])
    chk("C3", "Toda regla aplica a procedimientos existentes",
        [f"{r['id']}: {x}" for r in kb.get("reglas", []) for x in r.get("procedimientos", []) if x not in procs])
    chk("C4", "Todo sujeto referenciado existe",
        [f"{r['id']}: {r.get('sujeto_obligado')}" for r in kb.get("reglas", []) if r.get("sujeto_obligado") and r["sujeto_obligado"] not in sujetos] +
        [f"{a['id']}: {a.get('sujeto')}" for a in kb.get("actos", []) if a.get("sujeto") and a["sujeto"] not in sujetos])
    chk("C5", "Términos con valor positivo y artículo citado",
        [r["id"] for r in kb.get("reglas", []) if not (isinstance(r.get("termino_dias"), int) and r["termino_dias"] > 0 and r.get("articulo"))])
    chk("C6", "Actos con keywords para el matching (frontera de vocabulario)",
        [a["id"] for a in kb.get("actos", []) if not a.get("keywords")])
    en_etapas = {x for p in kb.get("procedimientos", []) for e in p.get("etapas", []) for x in e.get("actos", [])}
    chk("C7", "Sin actos huérfanos (advertencia: acto fuera de todas las etapas)",
        sorted(actos - en_etapas))
    consistente = all(c["ok"] for c in checks if c["id"] != "C7")
    return {"consistente": consistente, "checks": checks,
            "owl_hash": file_hash(COGEP_OWL_PATH) if COGEP_OWL_PATH.exists() else None,
            "nota": ("Verificación estructural automatizada sobre la KB/OWL. La verificación con razonador DL "
                     "(HermiT/Pellet en Protégé) y el escaneo OOPS! se ejecutan externamente y se registran en bitácora."),
            "contexto_adaptacion": _contexto_adaptacion("verificacion_ontologica")}

def _cq_resolver(kb, tipo, params):
    p = params or {}
    if tipo == "actos_por_procedimiento":
        proc = next((x for x in kb["procedimientos"] if x["id"] == p.get("proc")), None)
        if not proc: return None
        return [{"etapa": e["nombre"], "actos": e.get("actos", [])} for e in proc.get("etapas", [])]
    if tipo == "reglas_por_procedimiento":
        return [{"regla": r["id"], "nombre": r["nombre"], "articulo": r["articulo"], "termino_dias": r["termino_dias"]}
                for r in kb["reglas"] if p.get("proc") in r.get("procedimientos", [])]
    if tipo == "termino_de_acto":
        return [{"regla": r["id"], "articulo": r["articulo"], "termino_dias": r["termino_dias"],
                 "procedimientos": r.get("procedimientos", [])} for r in kb["reglas"] if r.get("acto_hasta") == p.get("acto")]
    if tipo == "sujeto_obligado":
        r = next((x for x in kb["reglas"] if x["id"] == p.get("regla")), None)
        if not r: return None
        s = next((x for x in kb["sujetos"] if x["id"] == r.get("sujeto_obligado")), None)
        return {"regla": r["id"], "sujeto": (s or {}).get("nombre", r.get("sujeto_obligado")), "articulo": r["articulo"]}
    if tipo == "actos_sin_termino":
        con = {r.get("acto_hasta") for r in kb["reglas"]}
        return sorted(a["id"] for a in kb["actos"] if a["id"] not in con)
    if tipo == "actos_de_sujeto":
        return sorted(a["id"] for a in kb["actos"] if a.get("sujeto") == p.get("sujeto"))
    if tipo == "procedimientos_de_flujo":
        return [x["id"] for x in kb["procedimientos"] if p.get("flujo") in (x.get("flujos") or [x.get("flujo")])]
    return None

@app.get("/api/cogep/cq", summary="A4 · Ejecutar las competency questions sobre la ontología", tags=["Validez IA"])
def get_cq():
    kb = load_kb()
    if "error" in kb: return kb
    cqs = _jload(CQ_PATH, [])
    out = []
    for c in cqs:
        try: resp = _cq_resolver(kb, c.get("tipo"), c.get("params"))
        except Exception as e: resp = None
        out.append({**c, "respuesta": resp, "responde": resp is not None and resp != []})
    return {"n": len(out), "responden": sum(1 for c in out if c["responde"]), "cqs": out,
            "contexto_adaptacion": _contexto_adaptacion("competency_questions")}

@app.post("/api/cogep/cq", summary="A4 · Añadir una competency question (tipos predefinidos)", tags=["Validez IA"])
def post_cq(payload: dict = Body(...)):
    tipos = ("actos_por_procedimiento", "reglas_por_procedimiento", "termino_de_acto",
             "sujeto_obligado", "actos_sin_termino", "actos_de_sujeto", "procedimientos_de_flujo")
    tipo = str(payload.get("tipo", ""))
    if tipo not in tipos: return {"error": f"tipo debe ser uno de {tipos}"}
    pregunta = str(payload.get("pregunta", "")).strip()[:300]
    if not pregunta: return {"error": "se requiere 'pregunta'"}
    cqs = _jload(CQ_PATH, [])
    cq = {"id": f"CQ{len(cqs)+1:02d}", "pregunta": pregunta, "tipo": tipo,
          "params": payload.get("params") or {}, "sparql": str(payload.get("sparql", ""))[:600],
          "autor": str(payload.get("actor", "usuario-experto"))[:80]}
    cqs.append(cq); _jsave(CQ_PATH, cqs)
    bitacora_log(cq["autor"], "nueva_competency_question", f"{cq['id']}: {pregunta}", refs=["/api/cogep/cq"], tipo="adaptacion")
    return {"ok": True, "cq": cq}

# ── A5 · Caracterización de la muestra ───────────────────────────────
@app.get("/api/adaptativo/muestra", summary="A5 · Caracterización de la muestra de expedientes", tags=["Adaptativo (MAPE-K)"])
def get_muestra():
    kb = load_kb()
    filas = []
    for name, label, juicio, d in _iter_causas():
        proc = _detect_procedimiento(kb, d) if "error" not in kb else {}
        cab = d.get("cabecera") or {}
        j = str(juicio or "")
        filas.append({"juicio": j, "procedimiento": proc.get("id", "?"),
                      "provincia": j[:2] if len(j) >= 2 else "?",
                      "anio": j[5:9] if len(j) >= 9 and j[5:9].isdigit() else "?",
                      "materia": cab.get("Materia") or cab.get("Tipo Accion") or "?",
                      "n_actividades": len(d.get("actividades") or [])})
    def agg(key):
        c = {}
        for f in filas: c[f[key]] = c.get(f[key], 0) + 1
        return dict(sorted(c.items(), key=lambda x: -x[1]))
    return {"n": len(filas), "por_procedimiento": agg("procedimiento"), "por_provincia": agg("provincia"),
            "por_anio": agg("anio"), "por_materia": agg("materia"), "causas": filas,
            "declaracion": ("Muestreo intencional (no probabilístico) estratificado por procedimiento y provincia, "
                            "sobre causas COGEP consultables en el portal público SATJE. Permite generalización "
                            "analítica del método (detección de incumplimientos); NO habilita inferencia estadística "
                            "poblacional. El índice empírico global es un indicador sobre la muestra estudiada.")}


if FRONT_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONT_DIR), html=True), name="static")
# MALTG v3 — capa adaptativa MAPE-K activa
