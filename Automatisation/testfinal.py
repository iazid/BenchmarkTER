#!/usr/bin/env python3

import os
import glob
import pandas as pd
import matplotlib.pyplot as plt

# ─── 1) CHEMIN VERS VOS CSV ─────────────────────────────────────────────────────
# Remplacez ce chemin par le chemin absolu de votre dossier Benchmarks\Results\Gascomparator
CSV_FOLDER = r"C:\Users\yaya\Desktop\Benchmarks\Results\Gascomparator"

# Le dossier de sortie restant relatif
OUT_DIR = os.path.join(CSV_FOLDER, "Graphes", "ComparaisonLatencyComplexity")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── 2) Fonction pour récupérer un CSV selon son nom exact ───────────────────────
def load_and_std_exact(name, mapping):
    path = os.path.join(CSV_FOLDER, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Fichier introuvable : {path}")
    df = pd.read_csv(path)
    return df.rename(columns=mapping)[["TestName"] + list(mapping.values())]

# ─── 3) Chargement de chaque benchmark CSV ──────────────────────────────────────
df_near   = load_and_std_exact("benchmark_near.csv",   {"GasRatio(%)":"NEAR_CostRatio","TxLatency(ms)":"NEAR_Latency"})
df_solana = load_and_std_exact("benchmark_solana.csv", {"CUratioToRef":"SOL_CostRatio","LatencyTxMs":"SOL_Latency"})
df_eth    = load_and_std_exact("benchmark_eth.csv",    {"GasRatioToRef":"ETH_CostRatio","TxLatency":"ETH_Latency"})
df_avax   = load_and_std_exact("benchmark_avax.csv",   {"GasRatioToRef":"AVAX_CostRatio","TxLatency":"AVAX_Latency"})
df_moon   = load_and_std_exact("benchmark_moon.csv",   {"GasRatioToRef":"MOON_CostRatio","TxLatency":"MOON_Latency"})

# ─── 4) Fusion de tous les résultats ────────────────────────────────────────────
df = df_near.merge(df_solana, on="TestName", how="outer") \
            .merge(df_eth,    on="TestName", how="outer") \
            .merge(df_avax,   on="TestName", how="outer") \
            .merge(df_moon,   on="TestName", how="outer")

# ─── 5) Normalisation des latences ──────────────────────────────────────────────
LAT = ["NEAR_Latency","SOL_Latency","ETH_Latency","AVAX_Latency","MOON_Latency"]
df["min_latency"] = df[LAT].min(axis=1)
for c in LAT:
    df[f"{c}_Norm"] = df[c] / df["min_latency"]

# ─── 6) Variables pour tracés ──────────────────────────────────────────────────
x = range(len(df))
w = 0.15

# ─── 7) Barres groupées – Cost Ratios ──────────────────────────────────────────
plt.figure(figsize=(12,6))
for i,key in enumerate(["NEAR_CostRatio","SOL_CostRatio","ETH_CostRatio","AVAX_CostRatio","MOON_CostRatio"]):
    plt.bar([xi + i*w for xi in x], df[key], w, label=key.split("_")[0])
plt.xticks([xi+2*w for xi in x], df["TestName"], rotation=90)
plt.ylabel("Cost Ratio")
plt.title("Comparaison des Cost Ratios")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR,"cost_ratios.png"))

# ─── 8) Barres groupées – Latences Normalisées ──────────────────────────────────
plt.figure(figsize=(12,6))
for i,c in enumerate(LAT):
    plt.bar([xi + i*w for xi in x], df[f"{c}_Norm"], w, label=c.split("_")[0])
plt.xticks([xi+2*w for xi in x], df["TestName"], rotation=90)
plt.ylabel("Latency ×")
plt.title("Comparaison des Latences Normalisées")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR,"latency_normalized.png"))

# ─── 9) Scatter – Coût vs Latence ──────────────────────────────────────────────
plt.figure(figsize=(8,6))
for net in ["NEAR","SOL","ETH","AVAX","MOON"]:
    plt.scatter(df[f"{net}_CostRatio"], df[f"{net}_Latency_Norm"], label=net)
plt.xlabel("Cost Ratio")
plt.ylabel("Latency ×")
plt.title("Coût vs Latence")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR,"cost_vs_latency.png"))

# ─── 🔟 Heatmap – Cost Ratios ─────────────────────────────────────────────────
plt.figure(figsize=(8,6))
cost_mat = df[["NEAR_CostRatio","SOL_CostRatio","ETH_CostRatio","AVAX_CostRatio","MOON_CostRatio"]].to_numpy()
plt.imshow(cost_mat, aspect='auto')
plt.yticks(range(len(df)), df["TestName"])
plt.xticks(range(5), ["NEAR","SOL","ETH","AVAX","MOON"])
plt.colorbar(label="Cost Ratio")
plt.title("Heatmap Cost Ratios")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR,"cost_heatmap.png"))

# ─── ⓫ Heatmap – Latences Normalisées ─────────────────────────────────────────
plt.figure(figsize=(8,6))
lat_mat = df[[f"{c}_Norm" for c in LAT]].to_numpy()
plt.imshow(lat_mat, aspect='auto')
plt.yticks(range(len(df)), df["TestName"])
plt.xticks(range(5), ["NEAR","SOL","ETH","AVAX","MOON"])
plt.colorbar(label="Latency ×")
plt.title("Heatmap Latencies Normalized")
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR,"latency_heatmap.png"))

print(f"✅ Graphiques générés dans : {OUT_DIR}")
