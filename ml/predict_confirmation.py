"""DSO2 (serves BO2): predict whether a reservation will be confirmed.

    python ml/predict_confirmation.py

Rows: every reservation that left 'pending' (confirmed or cancelled). Features known at booking time: event type,
service category, region, final price, list price, customer budget, month, weekday, holiday and Ramadan flags,
and whether the customer had booked before. Model: gradient boosting, evaluated with 5-fold stratified
cross-validation (ROC AUC) against a stratified dummy classifier. Gate: AUC >= 0.60 and above the dummy by more
than its spread. Writes ml/reports/predict_confirmation.json.
"""

import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from common import query, write_report

CATEGORICAL = ["event_type", "service_category", "region"]
NUMERIC = ["final_price", "list_price", "budget", "month", "weekday", "is_holiday", "is_ramadan", "booked_before"]


def main() -> None:
    df = query("""
        select f.is_confirmed::int as confirmed, e.event_type, s.service_category, g.region,
               f.final_price::float, f.list_price::float, e.budget::float,
               extract(month from f.reservation_date)::int as month,
               extract(isodow from f.reservation_date)::int as weekday,
               d.is_holiday::int, d.is_ramadan::int,
               (exists (select 1 from marts.dim_event e2 where e2.beneficiary_id = e.beneficiary_id
                        and e2.event_date < e.event_date))::int as booked_before
        from marts.fact_reservation f
        join marts.dim_event e using (event_id) join marts.dim_service s using (service_id)
        join marts.dim_geography g using (governorate_id) join marts.dim_date d on d.date_day = f.reservation_date
        where f.status in ('confirmed', 'cancelled')""")
    X, y = df[CATEGORICAL + NUMERIC], df["confirmed"]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    prep = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL)], remainder="passthrough")
    model = make_pipeline(prep, HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=42))
    auc = cross_val_score(model, X, y, cv=folds, scoring="roc_auc")
    dummy = cross_val_score(DummyClassifier(strategy="stratified", random_state=42), X, y, cv=folds, scoring="roc_auc")
    passes = bool(auc.mean() >= 0.60 and auc.mean() - dummy.mean() > 2 * dummy.std())
    report = {
        "objective": "DSO2 · predict whether a reservation will be confirmed (serves BO2)",
        "data": {"reservations": int(len(df)), "confirmed_share": round(float(y.mean()), 3),
                 "features": CATEGORICAL + NUMERIC},
        "gate": "ROC AUC >= 0.60, and above a stratified dummy by more than twice its spread",
        "results": {"gradient_boosting_auc_mean": round(float(auc.mean()), 3),
                    "gradient_boosting_auc_folds": [round(float(a), 3) for a in auc],
                    "dummy_auc_mean": round(float(dummy.mean()), 3)},
        "passes_gate": passes,
        "conclusion": (
            "The model separates confirmed from cancelled reservations well enough to prioritise follow-ups."
            if passes else
            f"No usable signal: AUC {auc.mean():.3f} against {dummy.mean():.3f} for chance. Confirmation does not "
            "depend on any feature available at booking time in this dataset, so no prediction is served."),
    }
    path = write_report("predict_confirmation", report)
    print(f"AUC {auc.mean():.3f} (folds {np.round(auc, 3)}) vs dummy {dummy.mean():.3f} · gate {passes} · {path}")


if __name__ == "__main__":
    main()
