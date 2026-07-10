"""
GlazyBench dataset loader for PyTorch Geometric.
Converts parquet formulations into graph Data objects.
"""

import pandas as pd
import torch
from torch_geometric.data import Data, Dataset
import re
from pathlib import Path

OXIDE_ORDER = ["SiO2", "Al2O3", "Na2O", "K2O", "CaO", "MgO", "Fe2O3"]
NUM_NODES = len(OXIDE_ORDER)

OXIDE_ROLE = {
    "SiO2": 0, "Al2O3": 1, "Na2O": 2, "K2O": 2,
    "CaO": 2, "MgO": 2, "Fe2O3": 1,
}

ATOMIC_MASS = {
    "SiO2": 60.08, "Al2O3": 101.96, "Na2O": 61.98, "K2O": 94.20,
    "CaO": 56.08, "MgO": 40.30, "Fe2O3": 159.69,
}


def _parse_formula(formula: str) -> list[float]:
    """Parse oxide formula string into normalized vector."""
    vec = [0.0] * NUM_NODES
    if not isinstance(formula, str):
        return vec
    for i, oxide in enumerate(OXIDE_ORDER):
        m = re.search(rf"{oxide}\s*([\d.]+)", formula, re.IGNORECASE)
        if m:
            vec[i] = float(m.group(1))
    total = sum(vec)
    if total > 0:
        vec = [v / total * 100 for v in vec]
    return vec


def _make_graph(oxide_vec: list[float]) -> Data:
    nodes = []
    for i, ox in enumerate(OXIDE_ORDER):
        mol = oxide_vec[i]
        role = OXIDE_ROLE[ox]
        role_oh = [1.0 if j == role else 0.0 for j in range(4)]
        mass = ATOMIC_MASS[ox] / 100.0
        nodes.append([mol] + role_oh + [mass])

    x = torch.tensor(nodes, dtype=torch.float32)
    edge_index = []
    for i in range(NUM_NODES):
        for j in range(NUM_NODES):
            if i != j:
                edge_index.append([i, j])
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

    return Data(x=x, edge_index=edge_index)


class GlazyBenchDataset(Dataset):
    def __init__(self, parquet_path: str):
        super().__init__()
        self.df = pd.read_parquet(parquet_path)

    def len(self):
        return len(self.df)

    def get(self, idx: int) -> Data:
        row = self.df.iloc[idx]
        oxide_vec = _parse_formula(row.get("formula", ""))
        data = _make_graph(oxide_vec)

        props = row.get("properties", {})
        if isinstance(props, dict):
            data.y_cte = torch.tensor([props.get("cte", 6.0)], dtype=torch.float32)
            data.y_crazing = torch.tensor([props.get("crazing", 0.0)], dtype=torch.float32)
            data.y_surface = torch.tensor([props.get("surface", 0)], dtype=torch.long)
        else:
            data.y_cte = torch.tensor([6.0], dtype=torch.float32)
            data.y_crazing = torch.tensor([0.0], dtype=torch.float32)
            data.y_surface = torch.tensor([0], dtype=torch.long)

        return data
