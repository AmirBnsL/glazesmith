#!/usr/bin/env python3
"""Carefully clean materials.json: normalize oxides, merge duplicates, keep all useful entries."""
import json, re
from pathlib import Path

OXIDE_MAP = {
    "SIO2": "SiO2", "AL2O3": "Al2O3", "TIO2": "TiO2", "B2O3": "B2O3",
    "LI2O": "Li2O", "NA2O": "Na2O", "K2O": "K2O",
    "MGO": "MgO", "CAO": "CaO", "SRO": "SrO", "BAO": "BaO",
    "ZNO": "ZnO", "PBO": "PbO",
    "FE2O3": "Fe2O3", "FEO": "FeO",
    "P2O5": "P2O5", "ZRO2": "ZrO2",
    "COO": "CoO", "CUO": "CuO", "CU2O": "Cu2O",
    "MNO2": "MnO2", "MNO": "MnO",
    "CR2O3": "Cr2O3", "SNO2": "SnO2",
    "NIO": "NiO", "CDO": "CdO",
}
INVALID_OXIDES = {"CO2", "H2O", "F", "SO3", "KNAO", "H2O-", "H2O+", "NA2O-", "H2O-0", "CL"}

# Old entries to keep (by original key)
KEEP_OLD = {
    "silica", "whiting", "ep kaolin", "bentonite", "custer feldspar",
    "potash feldspar", "g200 hp", "grolleg kaolin", "kaolin",
    "nepheline syenite", "wollastonite", "dolomite", "talc",
    "zinc oxide", "red iron oxide", "titanium dioxide", "rutile",
    "tin oxide", "cobalt carbonate", "ferro frit 3124",
}

# Rename rules for display/filename consistency
RENAME = {
    "cc_china_clay": "china_clay",
    "tennessee__10_ball_clay": "tennessee_10_ball_clay",
    "49_er_ball_clay": "49er_ball_clay",
    "no._50_china_clay": "china_clay_50",
    "sodium_feldspar_1005": "soda_feldspar_1005",
    "glaze_a_ball_clay": "glaze_ball_clay_a",
    "no. 44 kaolin": "kaolin_44",
    "no. 17 kaolin": "kaolin_17",
}

data = json.load(open("data/materials.json"))
all_mats = data["materials"]

def normalize_oxides(mat):
    """Normalize oxide names in-place."""
    analysis = mat.get("analysis", {})
    cleaned = {}
    loi = 0.0
    for ox, val in analysis.items():
        ox_u = ox.upper().replace("(", "").replace(")", "").replace("-", "").replace(".", "")
        if ox_u in INVALID_OXIDES:
            continue
        if ox_u == "LOI":
            loi = val
            continue
        normalized = OXIDE_MAP.get(ox_u, ox)
        cleaned[normalized] = round(val, 2)
    mat["analysis"] = cleaned
    if loi > 0:
        mat["loi"] = loi
    return mat

# Step 1: Normalize all entries
for key in list(all_mats.keys()):
    all_mats[key] = normalize_oxides(all_mats[key])

# Step 2: Build output — keep old entries first, then add new ones that don't overlap
out = {"materials": {}}

# Helper: check if a new entry overlaps with an existing one
def normalize_key(k):
    return k.lower().replace(" ", "_").replace("#", "_").replace(".", "_").replace("-", "_")

existing_keys = set()
for old_key in KEEP_OLD:
    if old_key in all_mats:
        out["materials"][old_key] = all_mats[old_key]
        existing_keys.add(normalize_key(old_key))

# Add new entries that don't overlap
added_new = 0
for key, mat in sorted(all_mats.items()):
    if key in out["materials"]:
        continue
    nk = normalize_key(key)
    # Check if this material is already covered by an old entry
    overlap = False
    for ek in existing_keys:
        # If keys share significant word overlap, skip
        k_words = set(nk.split("_"))
        e_words = set(ek.split("_"))
        common = k_words & e_words
        if len(common) >= 2 and ("feldspar" in common or "kaolin" in common or "clay" in common or "ball" in common or "oxide" in common):
            overlap = True
            break
        # Specific known overlaps
        if ek == "potash_feldspar" and "feldspar" in k_words and "potash" not in k_words:
            continue  # don't overlap potash with other feldspars
        if "kaolin" in common and len(k_words) == 1 and len(e_words) == 1:
            overlap = True
            break
    
    if not overlap:
        out["materials"][key] = mat
        added_new += 1

# Apply renames
for old_name, new_name in RENAME.items():
    if old_name in out["materials"]:
        out["materials"][new_name] = out["materials"].pop(old_name)

# Ensure all entries have a "name" field
for key, mat in out["materials"].items():
    if "name" not in mat:
        mat["name"] = key.replace("_", " ").title()

with open("data/materials.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"Final: {len(out['materials'])} materials")
for k, v in sorted(out["materials"].items()):
    ox = v.get("analysis", {})
    print(f"  {k:40s} → {len(ox):2d} oxides: {sorted(ox.keys())}")
