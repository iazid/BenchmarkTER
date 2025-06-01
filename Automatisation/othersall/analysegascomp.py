import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob

# 1. Load benchmark CSVs for gas
csv_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results/GasComparator'))
all_csvs = glob.glob(os.path.join(csv_folder, "benchmark_*.csv"))

# 2. Parse gas data per network and test
def parse_gas_csv(path):
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
        first_line = f.readline().strip()
        if first_line.startswith("__REFERENCE__"):
            header = f.readline().strip().split(",")
        else:
            header = first_line.split(",")

        try:
            idx_name = header.index("TestName")
            idx_gas = header.index("GasNet")
        except ValueError:
            return None

        rows = []
        for line in f:
            parts = line.strip().split(",", len(header) - 1)
            if len(parts) <= max(idx_name, idx_gas):
                continue
            name = parts[idx_name]
            if name.lower() == "reference":
                continue
            try:
                gas = int(parts[idx_gas])
                rows.append((net, name, gas))
            except ValueError:
                continue

    if not rows:
        return None

    return pd.DataFrame(rows, columns=["Network", "TestName", "GasNet"])

# 3. Combine all gas data
dfs = [parse_gas_csv(f) for f in all_csvs]
dfs = [df for df in dfs if df is not None]
gas_df = pd.concat(dfs, ignore_index=True)

# 4. Generate bar charts per network for GasNet
output_dir = os.path.join(csv_folder, "Graphes")
os.makedirs(output_dir, exist_ok=True)

saved_paths = []

for net in sorted(gas_df["Network"].unique()):
    sub_df = gas_df[gas_df["Network"] == net]
    if sub_df.empty:
        continue

    agg = sub_df.groupby("TestName")["GasNet"].agg(["mean", "std", "count"])
    if agg.empty:
        continue
    agg["sem"] = agg["std"] / np.sqrt(agg["count"])
    agg["ci95"] = agg["sem"] * 1.96  # approx 95% CI for normal dist
    agg = agg.sort_values("mean")

    plt.figure(figsize=(16, 6), dpi=120)
    if (agg["count"] > 1).any():
        plt.bar(agg.index, agg["mean"], yerr=agg["ci95"], capsize=4)
    else:
        plt.bar(agg.index, agg["mean"])

    plt.ylim(0, (agg["mean"] + agg["ci95"]).max() * 1.2)

    plt.xticks(rotation=90)
    plt.ylabel("Average Gas Used (Net)")
    plt.title(f"Average Gas ± CI95% by Function – {net}")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()

    path = os.path.join(output_dir, f"{net.lower()}_gasnet_avg_ic95_bar.png")
    plt.savefig(path)
    plt.close()
    saved_paths.append(path)

saved_paths
