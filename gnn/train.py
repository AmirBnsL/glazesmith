"""
Training script for GlazeGNN on GlazyBench dataset.
Usage: python train.py --data ../data/glazybench/glazybench.parquet
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.loader import DataLoader
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
from app.models.dataset import GlazyBenchDataset
from model import GlazeGNN


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training device: {device}")

    dataset = GlazyBenchDataset(args.data)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)

    model = GlazeGNN().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-5)

    cte_loss_fn = nn.MSELoss()
    crazing_loss_fn = nn.BCELoss()
    surface_loss_fn = nn.NLLLoss()

    for epoch in range(args.epochs):
        model.train()
        total_cte_loss = 0
        total_crazing_loss = 0
        total_surface_loss = 0

        for batch in loader:
            batch = batch.to(device)
            cte_pred, crazing_pred, surface_pred = model(batch.x, batch.edge_index, batch.batch)

            loss_cte = cte_loss_fn(cte_pred, batch.y_cte)
            loss_crazing = crazing_loss_fn(crazing_pred, batch.y_crazing)
            loss_surface = surface_loss_fn(surface_pred, batch.y_surface)

            loss = loss_cte + loss_crazing + loss_surface

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_cte_loss += loss_cte.item()
            total_crazing_loss += loss_crazing.item()
            total_surface_loss += loss_surface.item()

        if (epoch + 1) % 10 == 0:
            n = len(loader)
            print(f"Epoch {epoch+1:3d}/{args.epochs}  "
                  f"CTE: {total_cte_loss/n:.6f}  "
                  f"Crazing: {total_crazing_loss/n:.6f}  "
                  f"Surface: {total_surface_loss/n:.6f}")

    torch.save(model.state_dict(), args.output)
    print(f"Model saved: {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="../data/glazybench/glazybench.parquet")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--output", default="glaze_gnn_state.pt")
    args = parser.parse_args()
    train(args)
