#!/usr/bin/env python3
"""
Digitalfire Scraper — extracts oxide analyses for the most common
ceramic materials used in GlazyBench, then writes them into
data/materials.json.
"""

import json, os, re, time, sys
from pathlib import Path
from urllib.parse import quote

try:
    import httpx
except ImportError:
    print("httpx not found — installing…");
    import subprocess; subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MATERIALS_PATH = DATA_DIR / "materials.json"
BASE_URL = "https://digitalfire.com"
# Be polite — insert a small delay between requests
DELAY = 0.3

# ---- 1. Fetch all Digitalfire material list pages → name→ID map ----

def fetch_text(url: str, client: httpx.Client) -> str:
    r = client.get(url, timeout=30, follow_redirects=True)
    r.raise_for_status()
    return r.text

def scrape_all_material_ids(client: httpx.Client) -> dict[str, int]:
    """Return {lowercase_name: numeric_id} for every material on Digitalfire."""
    LETTERS = [str(i) for i in range(1, 10)] + \
              [chr(ord("A") + i) for i in range(26)] + ["Frits"]
    name_id: dict[str, int] = {}
    list_pat = re.compile(
        r'href="https://digitalfire\.com/material/(\d+)"[^>]*>([^<]+)</a>'
    )
    for letter in LETTERS:
        url = f"{BASE_URL}/material/list/{letter}"
        try:
            html = fetch_text(url, client)
            for m in list_pat.finditer(html):
                name = m.group(2).strip().lower()
                id_ = int(m.group(1))
                # Prefer keeping the first occurrence (generic over branded)
                if name not in name_id:
                    name_id[name] = id_
        except Exception as exc:
            print(f"  ⚠  {letter}: {exc}")
        time.sleep(DELAY)
    return name_id


# ---- 2. Parse oxide table from a material page ----

def parse_oxide_table(html: str) -> tuple[dict[str, float], float | None]:
    """Return (oxides: {name: wt_pct}, formula_weight or None)."""
    oxides: dict[str, float] = {}
    fw: float | None = None
    # Locate the analysis table
    # Pattern: <tr><td class="label"><a href="/oxide/...">SiO2</a></td>
    #          <td class="text-right">65.00%</td>
    row_pat = re.compile(
        r"<tr[^>]*>"
        r"\s*<td[^>]*>\s*<a\s+href=\"[^\"]*/oxide/[^\"]*\"[^>]*>([^<]+)</a>\s*</td>"
        r"\s*<td[^>]*>([^<]*%?)</td>"
    )
    for m in row_pat.finditer(html):
        ox = m.group(1).strip().upper()
        val_str = m.group(2).strip().replace("%", "").replace(",", ".")
        if val_str and val_str != "n/a":
            try:
                v = float(val_str)
                oxides[ox] = v
            except ValueError:
                pass
    # Formula weight
    fw_pat = re.compile(
        r"Formula\s*Weight</a>\s*</td>\s*<td[^>]*>\s*([\d,.]+)"
    )
    fwm = fw_pat.search(html, re.IGNORECASE)
    if fwm:
        try:
            fw = float(fwm.group(1).replace(",", ""))
        except ValueError:
            pass
    return oxides, fw


def fetch_material_oxide(
    client: httpx.Client, name: str, mat_id: int
) -> dict | None:
    """Given a Digitalfire material ID, return a materials.json entry or None."""
    url = f"{BASE_URL}/material/{mat_id}"
    try:
        html = fetch_text(url, client)
    except Exception:
        return None
    oxides, fw = parse_oxide_table(html)
    if not oxides:
        return None
    # Filter out LOI from oxides (it's loss-on-ignition, not a real oxide)
    if "LOI" in oxides:
        loi = oxides.pop("LOI")
    else:
        # Some pages have LOI in the standard row, some call it "LOI"
        loi = 0.0
    return {
        "name": name.title(),
        "aliases": [],
        "loi": loi,
        "analysis": oxides,
    }


# ---- 3. Main ----

def main():
    print("=" * 60)
    print("Digitalfire Material Scraper")
    print("=" * 60)
    with httpx.Client() as client:
        print("\n1. Scraping material list pages (A–Z, 1-9, Frits) …")
        all_materials = scrape_all_material_ids(client)
        print(f"   Found {len(all_materials)} unique material names")

        # ---- Load top GlazyBench materials we want to match ----
        # Focus on materials that appear most frequently in GlazyBench recipes
        wanted = {
            "silica", "flint", "quartz",
            "potash feldspar", "potassium feldspar", "feldspar",
            "soda feldspar", "sodium feldspar", "albite",
            "kaolin", "china clay", "ep kaolin", "epk",
            "whiting", "calcium carbonate",
            "dolomite",
            "zinc oxide",
            "ball clay",
            "nepheline syenite",
            "bentonite",
            "talc",
            "alumina hydrate", "aluminum hydrate",
            "custer feldspar",
            "grolleg kaolin",
            "wollastonite",
            "petalite",
            "barium carbonate",
            "kona f-4 feldspar",
            "minspar", "minspar 200",
            "cornish stone", "china stone",
            "ferro frit", "frit",
            "rutile",
            "titanium dioxide",
            "red iron oxide", "iron oxide",
            "tin oxide",
            "cobalt carbonate",
            "manganese dioxide",
            "copper carbonate",
            "cryolite",
            "lithium carbonate",
            "spodumene",
            "strontium carbonate",
            "zirconium silicate", "zircopax",
            "bone ash",
            "colemanite",
            "gerstley borate",
            "borax",
            "soda ash", "sodium carbonate",
            "magnesium carbonate",
            "alumina",
            "calcined kaolin",
            "glaze ball clay",
            "om4 ball clay",
            "goldart",
            "redart",
            "fireclay",
            "kentucky ball clay",
            "tennessee ball clay",
            "old hickory ball clay",
        }

        matched: set[str] = set()
        for df_name, df_id in all_materials.items():
            for w in wanted:
                if w in df_name or df_name in w:
                    matched.add(df_name)
                    break

        print(f"   Matched {len(matched)} Digitalfire materials to wanted list")

        # ---- 4. Score matches: prefer the Digitalfire name that's closest to the target ----
        def similarity(a: str, b: str) -> float:
            a_words = set(a.split())
            b_words = set(b.split())
            if not a_words or not b_words:
                return 0.0
            return len(a_words & b_words) / max(len(a_words), len(b_words))

        # For each wanted term, pick the best-matching Digitalfire material
        seen_ids: set[int] = set()
        selected: list[tuple[str, int]] = []
        for w in sorted(wanted, key=len, reverse=True):
            best_score = 0.0
            best_pair = None
            for df_name, df_id in all_materials.items():
                if df_id in seen_ids:
                    continue
                # Normalize both
                a = df_name.replace("-", " ").replace(",", "").replace(".", "")
                b = w.replace("-", " ").replace(",", "").replace(".", "")
                s = similarity(a, b)
                if s > best_score and s > 0.3:
                    best_score = s
                    best_pair = (df_name, df_id)
            if best_pair and best_pair[1] not in seen_ids:
                selected.append(best_pair)
                seen_ids.add(best_pair[1])

        print(f"   Selected {len(selected)} unique Digitalfire materials to scrape")

        # ---- 5. Fetch each selected material ----
        new_entries: dict[str, dict] = {}
        for df_name, df_id in selected:
            print(f"   Fetching {df_name} (ID {df_id}) …")
            entry = fetch_material_oxide(client, df_name, df_id)
            if entry:
                # Normalize oxide names (capitalize first letter after subscript-style)
                key = df_name.lower().replace(" ", "_").replace("-", "_")
                new_entries[key] = entry
            time.sleep(DELAY)

    print(f"\n  Fetched {len(new_entries)} material analyses from Digitalfire")

    # ---- 6. Merge with existing materials.json ----
    existing = {}
    if MATERIALS_PATH.exists():
        existing = json.loads(MATERIALS_PATH.read_text()).get("materials", {})

    merged = dict(existing)
    merged.update(new_entries)

    output = {"materials": merged}
    MATERIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    MATERIALS_PATH.write_text(json.dumps(output, indent=2) + "\n")
    print(f"  Written {len(merged)} total materials to {MATERIALS_PATH}")


if __name__ == "__main__":
    main()
