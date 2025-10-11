import json

with open("results_md.json", "r") as f:
    results_md = json.load(f)

print(len(results_md))
