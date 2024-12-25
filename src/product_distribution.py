"""
This script is used to calculate the distribution of products in the ESCI dataset.
"""

import json

stats = {}
for i in open("esci-s/en_esci.json", encoding="utf-8"):
    if category := json.loads(i).get("category"):
        top_category = category[0]
        if top_category not in stats:
            stats[top_category] = 0
        stats[top_category] += 1

stats = dict(sorted(stats.items(), reverse=True, key=lambda x: x[1]))

print(json.dumps(stats))
