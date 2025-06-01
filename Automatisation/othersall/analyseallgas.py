# Générer des courbes GasNet vs Complexité par fonction pour chaque blockchain
import matplotlib.pyplot as plt

# Regrouper les données utiles
if "merged" not in locals():
    # fallback in case we need to recompute merged from files (assume previous cells were skipped)
    raise ValueError("Le DataFrame 'merged' n'est pas défini.")

plot_dir = "/mnt/data/Graphes/ComparaisonGasComplexity"
os.makedirs(plot_dir, exist_ok=True)

plot_paths = []

# Générer un graphe par fonction
for fn in merged["Function"].unique():
    fn_df = merged[merged["Function"] == fn]
    if fn_df["Gasnet"].isnull().all():
        continue

    plt.figure(figsize=(10, 6), dpi=120)
    for net in sorted(fn_df["Network"].dropna().unique()):
        sub = fn_df[(fn_df["Network"] == net) & (~fn_df["Gasnet"].isnull())]
        if sub.empty:
            continue
        sub = sub.sort_values("Complexity")
        plt.plot(sub["Complexity"], sub["Gasnet"], marker='o', label=net)

    plt.title(f"GasNet vs Complexity – {fn}")
    plt.xlabel("Complexity")
    plt.ylabel("Average GasNet")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend()
    plt.tight_layout()

    out_path = os.path.join(plot_dir, f"{fn}_gas_vs_complexity.png")
    plt.savefig(out_path)
    plt.close()
    plot_paths.append(out_path)

plot_paths
