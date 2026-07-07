"""
Low-latency inference wrapper for GlazeGNN.
Loads trained weights, accepts UMF matrix, returns predictions in <50ms.
"""

import torch
import torch.nn.functional as F
from torch_geometric.data import Data, Batch
import numpy as np

from model import GlazeGNN

MODEL_PATH = "glaze_gnn_state.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Node features per oxide [mol%, role_one_hot(4), atomic_mass/100]
# Oxides: SiO2, Al2O3, Na2O, K2O, CaO, MgO, Fe2O3
OXIDE_ROLES = {"former": 0, "stabilizer": 1, "flux": 2, "colorant": 3}
OXIDE_ATOMIC_MASSES = {
    "SiO2": 60.08, "Al2O3": 101.96, "Na2O": 61.98, "K2O": 94.20,
    "CaO": 56.08, "MgO": 40.30, "Fe2O3": 159.69,
}


class GNNInference:
    def __init__(self):
        self.model = None

    def load(self, path: str = MODEL_PATH):
        self.model = GlazeGNN().to(DEVICE)
        state = torch.load(path, map_location=DEVICE, weights_only=True)
        self.model.load_state_dict(state)
        self.model.eval()

    def _build_graph(self, umf_matrix: dict[str, float]) -> Data:
        oxide_names = ["SiO2", "Al2O3", "Na2O", "K2O", "CaO", "MgO", "Fe2O3"]
        role_map = {
            "SiO2": 0, "B2O3": 0,
            "Al2O3": 1, "Fe2O3": 1,
            "Na2O": 2, "K2O": 2, "CaO": 2, "MgO": 2, "ZnO": 2, "Li2O": 2, "PbO": 2,
        }

        nodes = []
        for ox in oxide_names:
            mol = umf_matrix.get(ox, 0.0)
            role = role_map.get(ox, 2)
            role_one_hot = [1.0 if i == role else 0.0 for i in range(4)]
            mass = OXIDE_ATOMIC_MASSES.get(ox, 50.0) / 100.0
            nodes.append([mol] + role_one_hot + [mass])

        x = torch.tensor(nodes, dtype=torch.float32)

        num_nodes = len(oxide_names)
        edge_index = []
        for i in range(num_nodes):
            for j in range(num_nodes):
                if i != j:
                    edge_index.append([i, j])
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()

        return Data(x=x, edge_index=edge_index)

    @torch.inference_mode()
    def predict(self, umf_matrix: dict[str, float]) -> dict:
        if self.model is None:
            self.load()

        data = self._build_graph(umf_matrix)
        data = data.to(DEVICE)
        batch = torch.zeros(data.x.size(0), dtype=torch.long, device=DEVICE)

        cte, crazing, surface_logits = self.model(data.x, data.edge_index, batch)

        surface_probs = F.softmax(surface_logits, dim=-1)
        surface_classes = ["glossy", "satin", "matte", "crystalline"]
        predicted_class = surface_classes[surface_logits.argmax().item()]

        return {
            "coefficient_of_thermal_expansion": cte.item(),
            "crazing_risk_probability": crazing.item(),
            "surface_finish_logits": surface_logits.cpu().tolist(),
            "predicted_surface_class": predicted_class,
            "transparency_class": "transparent_clear",
        }


inference = GNNInference()
