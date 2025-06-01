import os
import subprocess
import time

BASE_DIR = "C:/Users/yaya/Desktop/Benchmarks"

# Définir les commandes par dossier (toutes blockchains)
COMMANDS = {
    "BenchmarkEthereum": "npx hardhat run scripts/mesure.js --network sepolia",
    "BenchmarkMoonBeam": "npx hardhat run scripts/mesure.js --network moonbase",
    "BenchmarkAvaxFuji": "npx hardhat run scripts/mesure.js --network fuji",
    "benchmark-solana-v2": [
        'wsl', 'bash', '-i', '-c',
        'export ANCHOR_PROVIDER_URL="https://api.devnet.solana.com"; '
        'export ANCHOR_WALLET="$HOME/.config/solana/id.json"; '
        'cd /mnt/c/Users/yaya/Desktop/Benchmarks/benchmark-solana-v2 && npm run benchmark1'
    ],
    "BenchmarkNear": [
        'wsl', 'bash', '-i', '-c',
        'cd /mnt/c/Users/yaya/Desktop/Benchmarks/BenchmarkNear && npm run bench1'
    ],
}
    
# Liste des blockchains à traiter
blockchain_dirs = [d for d in COMMANDS.keys()]

while True:
    print("\n--- Nouvelle boucle de benchmark lancee ---")

    for blockchain in blockchain_dirs:
        print(f"\n>>> Execution pour {blockchain}...")
        blockchain_path = os.path.join(BASE_DIR, blockchain)

        command = COMMANDS[blockchain]
        print(f"Commande lancée : {command}")

        if isinstance(command, list):
            process = subprocess.Popen(command)
        else:
            process = subprocess.Popen(command, cwd=blockchain_path, shell=True)

        process.wait()

        print(f"Processus pour {blockchain} termine.")

    print("\nTous les benchmarks ont été exécutés. Pause de 5 minutes...")
    time.sleep(120)  # Pause de 5 minutes avant la prochaine boucle
