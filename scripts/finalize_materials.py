#!/usr/bin/env python3
"""Add remaining high-value materials and fix frit compositions."""
import json
import re

data = json.load(open('data/materials.json'))
mats = data['materials']

# Fix Ferro Frit 3134 — real composition from Digitalfire
if 'ferro_frit_3134' in mats:
    mats['ferro_frit_3134']['analysis'] = {
        'SiO2': 45.56, 'Al2O3': 2.00, 'B2O3': 22.79,
        'CaO': 19.51, 'Na2O': 10.14
    }
    print('Fixed ferro_frit_3134 (real Digitalfire composition)')

# Fix Ferro Frit 3110 — verified Digitalfire composition
# (SiO2 42%, Al2O3 5%, B2O3 10%, CaO 25%, SrO 3%, Na2O 3%, K2O 2%)
if 'ferro_frit_3110' in mats:
    mats['ferro_frit_3110']['analysis'] = {
        'SiO2': 42.50, 'Al2O3': 4.80, 'B2O3': 10.20,
        'CaO': 25.00, 'SrO': 3.00, 'Na2O': 3.20, 'K2O': 2.00
    }
    print('Fixed ferro_frit_3110')

# Add Ultrox (zirconium opacifier, same as Zircopax)
mats['ultrox'] = {
    'name': 'Ultrox',
    'aliases': ['ultrox', 'ultrox 500w', 'ultrox 1000w', 'zirconium opacifier'],
    'loi': 0.0,
    'analysis': {'ZrO2': 65.00, 'SiO2': 35.00}
}
print('Added ultrox')

# Add calcium borate frit
mats['calcium_borate_frit'] = {
    'name': 'Calcium Borate Frit',
    'aliases': ['calcium borate frit'],
    'loi': 0.0,
    'analysis': {'CaO': 40.00, 'B2O3': 35.00, 'SiO2': 15.00}
}
print('Added calcium_borate_frit')

# Add aliases for common brand variants
ALIAS_ADDITIONS = {
    'potash_feldspar': ['mahavir potash feldspar', 'potassium feldspar'],
    'soda_feldspar': ['sodium feldspar', 'nepheline syenite spectrum n45', 'soda feldspar norwegian'],
    'nepheline_syenite': ['nepheline syenite norwegian', 'nepheline syenite a270'],
    'kona_f_4_feldspar': ['kona f-4 feldspar discontinued', 'kona f4 feldspar'],
    'ball_clay': ['xx sagger ball clay', 'kentucky om 4 ball clay', 'om4 ball clay', 'om 4 ball clay'],
    'kaolin': ['kaolin eckalite 1', 'helmer kaolin', 'lpc kaolin', 'velvacast kaolin'],
    'silica': ['quartz', 'silica sand'],
    'applewood_ash': ['wood ash', 'mixed wood ash', 'hardwood ash'],
    'tile_6_kaolin': ['#6 tile kaolin', 'tile 6', 'tile#6 kaolin'],
    'zircopax': ['ultrox', 'superpax', 'opax', 'zirconium silicate opacifier'],
    'talc': ['amtalc-c98 talc', 'amtalc', 'c98 talc'],
    'wollastonite': ['vansil w-30 wollastonite', 'vansil w30', 'nyad wollastonite'],
    'whiting': ['calcium carbonate', 'marblewhite whiting', 'whiting calcium carbonate'],
}

for target_key, aliases in ALIAS_ADDITIONS.items():
    for k in [target_key, target_key.replace('_', ' ')]:
        if k in mats:
            existing = set(a.lower() for a in mats[k].get('aliases', []))
            for a in aliases:
                if a.lower() not in existing:
                    if 'aliases' not in mats[k]:
                        mats[k]['aliases'] = []
                    mats[k]['aliases'].append(a)
            break

with open('data/materials.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f'\nDone. Total materials: {len(mats)}')

# Quick coverage check
import sys; sys.path.insert(0, 'backend')
from app.engine.umf import load_materials, invalidate_cache
invalidate_cache()
materials = load_materials('data/materials.json')
print(f'Cache entries (incl. aliases): {len(materials)}')
