#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

# ─── 1) Chemins ───────────────────────────────────────────────────────────────
CSV_FOLDER = r"C:\Users\yaya\Desktop\Benchmarks\Results\Gascomparator"
OUT_DIR    = os.path.join(CSV_FOLDER, "Graphes", "Séparés")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── 2) Chargement standardisé ─────────────────────────────────────────────────
def load_std(fname, mapping):
    df = pd.read_csv(os.path.join(CSV_FOLDER, fname))
    return df.rename(columns=mapping)[["TestName"] + list(mapping.values())]

df = (load_std("benchmark_near.csv",   {"GasRatio(%)":"NEAR_Cost","TxLatency(ms)":"NEAR_Lat"})
      .merge(load_std("benchmark_solana.csv", {"CUratioToRef":"SOL_Cost","LatencyTxMs":"SOL_Lat"}), on="TestName", how="outer")
      .merge(load_std("benchmark_eth.csv",    {"GasRatioToRef":"ETH_Cost","TxLatency":"ETH_Lat"}),    on="TestName", how="outer")
      .merge(load_std("benchmark_avax.csv",   {"GasRatioToRef":"AVAX_Cost","TxLatency":"AVAX_Lat"}),   on="TestName", how="outer")
      .merge(load_std("benchmark_moon.csv",   {"GasRatioToRef":"MOON_Cost","TxLatency":"MOON_Lat"}),   on="TestName", how="outer"))

# ─── 3) Normalisation des latences ─────────────────────────────────────────────
lat_cols = ["NEAR_Lat","SOL_Lat","ETH_Lat","AVAX_Lat","MOON_Lat"]
df["minLat"] = df[lat_cols].min(axis=1)
for c in lat_cols:
    df[c + "_Norm"] = df[c] / df["minLat"]

# ─── 4) Prépa variables ────────────────────────────────────────────────────────
cost_cols  = ["NEAR_Cost","SOL_Cost","ETH_Cost","AVAX_Cost","MOON_Cost"]
latn_cols  = [c + "_Norm" for c in lat_cols]
names      = [c.split("_")[0] for c in cost_cols]

# Pour alléger les labels si beaucoup de tests
n = len(df)
step = max(1, n // 20)
ticks = np.arange(0, n, step)
labels = df["TestName"].iloc[::step]

# ─── 5) Graphe 1 : Barres groupées – Cost Ratios (log) ────────────────────────
fig, ax = plt.subplots(figsize=(10,5))
x = np.arange(n)
w = 0.15
for i, col in enumerate(cost_cols):
    ax.bar(x + i*w, df[col], w, label=names[i])
ax.set_yscale("log")
ax.set_title("Cost Ratios par réseau")
ax.set_ylabel("Ratio (réf. = 1)")
ax.set_xticks(ticks + 2*w)
ax.set_xticklabels(labels, rotation=45, fontsize=8)
ax.legend(title="Réseaux", loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "cost_ratios_separate.png"), dpi=150)
plt.close(fig)

# ─── 6) Graphe 2 : Barres groupées – Latences normalisées ────────────────────
fig, ax = plt.subplots(figsize=(10,5))
for i, col in enumerate(latn_cols):
    ax.bar(x + i*w, df[col], w, label=names[i])
ax.set_title("Latences normalisées par réseau")
ax.set_ylabel("× latence minimale")
ax.set_xticks(ticks + 2*w)
ax.set_xticklabels(labels, rotation=45, fontsize=8)
ax.legend(title="Réseaux", loc="upper left", bbox_to_anchor=(1,1))
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "latency_normalized_separate.png"), dpi=150)
plt.close(fig)

# ─── 7) Graphe 3 : Scatter – Coût vs Latence normalisée ──────────────────────
fig, ax = plt.subplots(figsize=(6,6))
for col in cost_cols:
    net = col.split("_")[0]
    ax.scatter(df[col], df[f"{net}_Lat_Norm"], s=30, alpha=0.6, label=net)
ax.set_xscale("log")
ax.set_title("Coût vs Latence normalisée")
ax.set_xlabel("Cost Ratio (log)")
ax.set_ylabel("Latency ×")
ax.legend(title="Réseaux", bbox_to_anchor=(1,1), loc="upper left")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "cost_vs_latency_separate.png"), dpi=150)
plt.close(fig)

# ─── 8) Graphe 4 : Heatmap – Cost Ratios (log) ───────────────────────────────
fig, ax = plt.subplots(figsize=(6,8))
mat = df[cost_cols].to_numpy()
pos = mat[mat>0]
norm = LogNorm(vmin=pos.min() if pos.size else None, vmax=np.nanmax(mat))
im = ax.imshow(mat, aspect="auto", norm=norm)
ax.set_title("Heatmap des Cost Ratios")
ax.set_yticks(ticks)
ax.set_yticklabels(labels, fontsize=8)
ax.set_xticks(np.arange(len(names)))
ax.set_xticklabels(names, rotation=45, fontsize=9)
cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("Ratio (log)")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "heatmap_cost_separate.png"), dpi=150)
plt.close(fig)

print("✅ Tous les graphes séparés avec légende sont dans :", OUT_DIR)
