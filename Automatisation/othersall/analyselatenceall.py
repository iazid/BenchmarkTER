import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st
import glob

# 1. Load benchmark CSVs
csv_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results/GasComparator'))
all_csvs = glob.glob(os.path.join(csv_folder, "benchmark_*.csv"))
print("📂 Fichiers détectés :", [os.path.basename(f) for f in all_csvs])

# 2. Parse CSV with support for __REFERENCE__ line
def parse_latency_csv(path):
    filename = os.path.basename(path)

    if "solana" in filename.lower():
        net = "Solana"
    elif "eth" in filename.lower():
        net = "Ethereum"
    elif "avax" in filename.lower():
        net = "Avalanche"
    elif "moon" in filename.lower():
        net = "Moonbeam"
    elif "near" in filename.lower():
        net = "NEAR"
    else:
        net = "Unknown"

    with open(path, "r", encoding="utf-8") as f:
        # Skip __REFERENCE__ line if present
        first_line = f.readline().strip()
        if first_line.startswith("__REFERENCE__"):
            header = f.readline().strip().split(",")
        else:
            header = first_line.split(",")

        try:
            idx_name = header.index("TestName")
            idx_lat = next((i for i, h in enumerate(header) if "lat" in h.lower()), None)
            if idx_lat is None:
                print(f"⚠️ Pas de colonne latence : {filename}")
                return None
        except ValueError:
            print(f"⚠️ Structure invalide : {filename}")
            return None

        rows = []
        for line in f:
            parts = line.strip().split(",", len(header) - 1)
            if len(parts) <= max(idx_name, idx_lat):
                continue
            name = parts[idx_name]
            if name.lower() == "reference":
                continue
            try:
                lat = float(parts[idx_lat])
                rows.append((net, name, lat))
            except ValueError:
                continue

    if not rows:
        print(f"⚠️ Ignoré (aucune donnée) : {filename}")
        return None

    print(f"✅ Chargé : {filename} ({len(rows)} lignes)")
    return pd.DataFrame(rows, columns=["Network", "TestName", "Latency"])

# 3. Chargement global
dfs = [parse_latency_csv(f) for f in all_csvs]
dfs = [df for df in dfs if df is not None]
if not dfs:
    raise SystemExit("❌ Aucun fichier CSV valide trouvé.")

lat_df = pd.concat(dfs, ignore_index=True)
print("🧪 Réseaux chargés :", lat_df["Network"].unique())

# 4. Génération des graphes
output_dir = os.path.join(csv_folder, "Graphes")
os.makedirs(output_dir, exist_ok=True)
saved_paths = []

for net in sorted(lat_df["Network"].unique()):
    sub_df = lat_df[lat_df["Network"] == net]
    if sub_df.empty:
        continue

    agg = sub_df.groupby("TestName")["Latency"].agg(["mean", "std", "count"]).copy()
    if agg.empty:
        continue
    agg["sem"] = agg["std"] / np.sqrt(agg["count"])
    agg["ci95"] = agg["sem"] * st.t.ppf(0.975, agg["count"] - 1)
    agg = agg.sort_values("mean")

    plt.figure(figsize=(16, 6), dpi=120)
    if (agg["count"] > 1).any():
        plt.bar(agg.index, agg["mean"], yerr=agg["ci95"], capsize=4)
    else:
        plt.bar(agg.index, agg["mean"])

    # ✅ Ajout d'une échelle dynamique locale
    ymax = (agg["mean"] + agg["ci95"]).max()
    plt.ylim(0, ymax * 1.2)

    plt.xticks(rotation=90)
    plt.ylabel("Average Tx Latency (ms)")
    plt.title(f"Average Latency ± IC95% by Function – {net}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    path = os.path.join(output_dir, f"{net.lower()}_latency_avg_ic95_bar.png")
    plt.savefig(path)
    plt.close()
    saved_paths.append(path)

print("✅ Graphiques générés :", saved_paths)
