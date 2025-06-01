import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import glob

# 1. Charger les fichiers benchmark
csv_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Results/GasComparator'))
all_csvs = glob.glob(os.path.join(csv_folder, "benchmark_*.csv"))

# 2. Détection de réseau + parsing latence
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
        first = f.readline().strip()
        if first.startswith("__REFERENCE__"):
            header = f.readline().strip().split(",")
        else:
            header = first.split(",")

        try:
            idx_name = header.index("TestName")
            idx_lat = next(i for i, h in enumerate(header) if "lat" in h.lower())
        except (ValueError, StopIteration):
            return None

        rows = []
        for line in f:
            parts = line.strip().split(",", len(header) - 1)
            if len(parts) <= max(idx_name, idx_lat):
                continue
            name = parts[idx_name]
            if name.lower() == "reference" or name.startswith("__"):
                continue
            try:
                val = float(parts[idx_lat])
                rows.append((net, name, val))
            except:
                continue

    return pd.DataFrame(rows, columns=["Network", "TestName", "Latency"])

# 3. Extraire fonction + complexité
def extract_fn_complexity(name):
    match = re.match(r"(\w+)\(([^)]*)\)", name)
    if not match:
        return name, None
    fn = match.group(1)
    args = match.group(2).split(",")
    try:
        return fn, max(int(a.strip()) for a in args if a.strip().isdigit())
    except:
        return fn, None

# 4. Charger tous les fichiers
dfs = [parse_latency_csv(f) for f in all_csvs]
lat_df = pd.concat([df for df in dfs if df is not None], ignore_index=True)
lat_df[["Function", "Complexity"]] = lat_df["TestName"].apply(lambda x: pd.Series(extract_fn_complexity(x)))
lat_df = lat_df.dropna(subset=["Complexity"])

# 5. Complexités Big-O connues
complexities = {
    "fibonacciRecursive": "O(2^n)",
    "fibonacciIterative": "O(n)",
    "factorialRecursive": "O(n)",
    "factorialIterative": "O(n)",
    "loopSum": "O(n)",
    "isPrime": "O(√n)",
    "expBySquaring": "O(log n)",
    "gcd": "O(log min(a,b))",
    "setValue": "O(1)"
}

# 6. Agrégation moyenne
lat_agg = lat_df.groupby(["Function", "Complexity", "Network"])["Latency"].mean().reset_index()

# 7. Génération des courbes par fonction
out_dir = os.path.join(csv_folder, "Graphes", "ComparaisonLatencyComplexity")
os.makedirs(out_dir, exist_ok=True)

for fn in lat_agg["Function"].unique():
    sub = lat_agg[lat_agg["Function"] == fn]
    if sub.empty:
        continue

    pivot = sub.pivot_table(index="Complexity", columns="Network", values="Latency")

    plt.figure(figsize=(10, 6), dpi=120)
    for net in sorted(pivot.columns):
        plt.plot(pivot.index, pivot[net], marker='o', label=net)

    complexity_str = complexities.get(fn, "")
    full_title = f"{fn} – Latency vs Complexity" + (f" ({complexity_str})" if complexity_str else "")
    plt.suptitle(full_title, fontsize=14, fontweight='bold')
    plt.xlabel("Complexity")
    plt.ylabel("Average Latency (ms)")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    filename = f"{fn}_latency_vs_complexity.png"
    plt.savefig(os.path.join(out_dir, filename))
    plt.close()

print(f"✅ Graphiques enregistrés dans : {out_dir}")
