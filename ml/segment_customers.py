"""DSO3 (serves BO3 and BO4): segment customers by behaviour.

    python ml/segment_customers.py

One row per customer with at least one reservation: events, reservations, confirmed revenue, share confirmed,
average valid rating, complaints. Features are log-scaled where skewed and standardised; K-Means for k = 2..6,
k chosen by silhouette. Each segment is described by its medians and named from them. Gate: silhouette >= 0.25
(segments distinct enough to target separately). Writes ml/reports/segment_customers.json.
"""

import numpy as np
from common import query, write_report
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

FEATURES = ["events", "reservations", "confirmed_revenue", "confirmed_share", "rating", "complaints"]


def main() -> None:
    df = query("""
        select b.beneficiary_id, b.events, b.complaints,
               count(f.reservation_id) as reservations, coalesce(sum(f.revenue), 0)::float as confirmed_revenue,
               avg(f.is_confirmed::int)::float as confirmed_share, coalesce(avg(f.rating_avg), 3)::float as rating
        from marts.dim_beneficiary b join marts.fact_reservation f using (beneficiary_id)
        group by b.beneficiary_id, b.events, b.complaints""")
    X = df[FEATURES].astype(float).copy()
    for col in ("events", "reservations", "confirmed_revenue", "complaints"):
        X[col] = np.log1p(X[col])
    Z = StandardScaler().fit_transform(X)

    scores = {}
    for k in range(2, 7):
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Z)
        scores[k] = float(silhouette_score(Z, labels, sample_size=3000, random_state=42))
    k = max(scores, key=scores.get)
    df["segment"] = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(Z)

    overall = df[FEATURES].median()
    segments = []
    for seg, g in df.groupby("segment"):
        med = g[FEATURES].median()
        if med["confirmed_share"] == 0:
            name, action = "Not yet converted", "booked but never confirmed: the target for conversion follow-ups"
        elif med["reservations"] >= overall["reservations"]:
            name, action = "Active customers", "book and confirm regularly: the base to retain"
        else:
            name, action = "Occasional customers", "confirm, but rarely: candidates for re-engagement"
        segments.append({"segment": int(seg), "name": name, "action": action, "customers": int(len(g)),
                         "share": round(len(g) / len(df), 3),
                         "median": {c: round(float(med[c]), 2) for c in FEATURES}})
    segments.sort(key=lambda s: -s["median"]["confirmed_revenue"])
    passes = scores[k] >= 0.25
    report = {
        "objective": "DSO3 · segment customers by behaviour (serves BO3 and BO4)",
        "data": {"customers": int(len(df)), "features": FEATURES},
        "gate": "silhouette >= 0.25",
        "silhouette_by_k": {str(kk): round(v, 3) for kk, v in scores.items()},
        "chosen_k": k, "silhouette": round(scores[k], 3), "passes_gate": bool(passes),
        "segments": segments,
        "conclusion": (
            f"{k} segments, distinct enough to target separately (silhouette {scores[k]:.2f})." if passes else
            f"{k} segments at best, but they overlap (silhouette {scores[k]:.2f}): use them to describe the "
            "customer base, not to target campaigns."),
    }
    path = write_report("segment_customers", report)
    print(f"k={k} silhouette={scores[k]:.3f} gate={passes} · {path}")
    for s in segments:
        print(f"  {s['name']}: {s['customers']} customers ({s['share']:.0%}) · {s['action']}")


if __name__ == "__main__":
    main()
