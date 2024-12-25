import json

stats = {}
for i in open("esci-s/en_esci.json"):
    i = json.loads(i)
    if category := i.get("category"):
        top_category = category[0]
        if top_category not in stats:
            stats[top_category] = 0
        stats[top_category] += 1

stats = dict(sorted(stats.items(), reverse=True, key=lambda x: x[1]))

print(json.dumps(stats))
