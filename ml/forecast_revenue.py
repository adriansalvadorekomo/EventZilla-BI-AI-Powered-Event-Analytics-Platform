"""DSO1 (serves BO1): forecast monthly confirmed revenue.

    python ml/forecast_revenue.py

Series: confirmed revenue per month from marts.fact_reservation, 2022-01 to 2025-12 (48 points). The last 12
months are held out. Candidates: naive (last value), seasonal naive (same month last year), historical mean,
Holt-Winters (additive trend and seasonality) and SARIMA(1,0,1)(1,0,0,12). Deployment gate, the team's own
criterion: SMAPE < 30 % and MASE < 1 (MASE scaled by the in-sample one-step naive error). The model with the
lowest holdout SMAPE that passes the gate wins, unless a simpler one is within 0.5 SMAPE points of it: then the
simpler model is published (parsimony: on a flat, noisy series a small gain is noise). The winner is refitted on
all 48 months and forecasts the next 6; if nothing passes, the report says so and the naive forecast is shown.
Writes ml/reports/forecast_revenue.json.
"""

import warnings

import numpy as np
import pandas as pd
from common import query, write_report
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

HOLDOUT, HORIZON, SEASON = 12, 6, 12
TOLERANCE = 0.5  # SMAPE points
SIMPLICITY = ["naive", "seasonal naive", "historical mean", "Holt-Winters", "SARIMA(1,0,1)(1,0,0,12)"]


def smape(actual, forecast) -> float:
    actual, forecast = np.asarray(actual, float), np.asarray(forecast, float)
    return float(np.mean(2 * np.abs(forecast - actual) / (np.abs(actual) + np.abs(forecast))) * 100)


def mase(actual, forecast, train) -> float:
    scale = np.mean(np.abs(np.diff(np.asarray(train, float))))
    return float(np.mean(np.abs(np.asarray(actual, float) - np.asarray(forecast, float))) / scale)


def candidates(train: pd.Series, steps: int) -> dict[str, np.ndarray]:
    out = {
        "naive": np.repeat(train.iloc[-1], steps),
        "seasonal naive": np.array([train.iloc[-SEASON + (i % SEASON)] for i in range(steps)]),
        "historical mean": np.repeat(train.mean(), steps),
    }
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out["Holt-Winters"] = ExponentialSmoothing(train, trend="add", seasonal="add",
                                                   seasonal_periods=SEASON).fit().forecast(steps).to_numpy()
        out["SARIMA(1,0,1)(1,0,0,12)"] = SARIMAX(train, order=(1, 0, 1), seasonal_order=(1, 0, 0, SEASON),
                                                 trend="c").fit(disp=False).forecast(steps).to_numpy()
    return out


def main() -> None:
    df = query("""select date_trunc('month', reservation_date)::date as month, sum(revenue)::float as revenue
                  from marts.fact_reservation group by 1 order by 1""")
    series = pd.Series(df["revenue"].to_numpy(), index=pd.PeriodIndex(df["month"], freq="M"))
    train, test = series.iloc[:-HOLDOUT], series.iloc[-HOLDOUT:]

    results = []
    for name, forecast in candidates(train, HOLDOUT).items():
        s, m = smape(test, forecast), mase(test, forecast, train)
        results.append({"model": name, "smape": round(s, 2), "mase": round(m, 3), "passes_gate": s < 30 and m < 1})
    results.sort(key=lambda r: r["smape"])
    passing = [r for r in results if r["passes_gate"]]
    if passing:
        near_best = [r for r in passing if r["smape"] - passing[0]["smape"] <= TOLERANCE]
        winner = min(near_best, key=lambda r: SIMPLICITY.index(r["model"]))
        chosen = winner["model"]
    else:
        chosen = "naive"

    future = candidates(series, HORIZON)[chosen]
    months = pd.period_range(series.index[-1] + 1, periods=HORIZON, freq="M")
    best = results[0]
    report = {
        "objective": "DSO1 · forecast monthly confirmed revenue (serves BO1)",
        "data": {"months": len(series), "from": str(series.index[0]), "to": str(series.index[-1]),
                 "holdout_months": HOLDOUT, "mean_monthly_revenue": round(float(series.mean()))},
        "gate": "SMAPE < 30 % and MASE < 1",
        "holdout_results": results,
        "chosen_model": chosen,
        "conclusion": (
            (f"{chosen} is published: it passes the gate (SMAPE {winner['smape']} %, MASE {winner['mase']}) and is "
             f"within {TOLERANCE} points of the best model, {best['model']} ({best['smape']} %), while being simpler. "
             "On a flat series, the more complex models add nothing that the holdout can tell apart from noise.")
            if passing else
            f"No model passes the gate; the best, {best['model']}, reaches SMAPE {best['smape']} % and MASE "
            f"{best['mase']}. The naive forecast is published, labelled as such."),
        "history": [{"month": str(p), "revenue": round(v)} for p, v in series.items()],
        "forecast": [{"month": str(p), "revenue": round(float(v))} for p, v in zip(months, future, strict=True)],
    }
    path = write_report("forecast_revenue", report)
    for r in results:
        print(f"{r['model']:26} SMAPE {r['smape']:6.2f} %  MASE {r['mase']:.3f}  {'PASS' if r['passes_gate'] else '-'}")
    print(f"chosen: {chosen} · {path}")


if __name__ == "__main__":
    main()
