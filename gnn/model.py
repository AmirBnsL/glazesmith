import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GINConv, global_mean_pool, global_max_pool

NUM_NODE_FEATURES = 7
HIDDEN_DIM = 128
NUM_CLASSES_SURFACE = 4


class GlazeGNN(torch.nn.Module):
    def __init__(self):
        super().__init__()

        nn1 = nn.Sequential(
            nn.Linear(NUM_NODE_FEATURES, HIDDEN_DIM),
            nn.BatchNorm1d(HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
        )
        nn2 = nn.Sequential(
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.BatchNorm1d(HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
        )
        nn3 = nn.Sequential(
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
            nn.BatchNorm1d(HIDDEN_DIM),
            nn.ReLU(),
            nn.Linear(HIDDEN_DIM, HIDDEN_DIM),
        )

        self.conv1 = GINConv(nn1, train_eps=True)
        self.conv2 = GINConv(nn2, train_eps=True)
        self.conv3 = GINConv(nn3, train_eps=True)

        self.dropout = nn.Dropout(0.15)

        pooled_dim = HIDDEN_DIM * 2

        self.cte_head = nn.Linear(pooled_dim, 1)
        self.crazing_head = nn.Linear(pooled_dim, 1)
        self.surface_head = nn.Linear(pooled_dim, NUM_CLASSES_SURFACE)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)

        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = self.dropout(x)

        x = self.conv3(x, edge_index)
        x = F.relu(x)

        x_mean = global_mean_pool(x, batch)
        x_max = global_max_pool(x, batch)
        x = torch.cat([x_mean, x_max], dim=-1)

        cte = self.cte_head(x)
        crazing = torch.sigmoid(self.crazing_head(x))
        surface = F.log_softmax(self.surface_head(x), dim=-1)

        return cte.squeeze(-1), crazing.squeeze(-1), surface
