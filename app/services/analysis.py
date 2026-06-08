from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

try:
    from statsmodels.tsa.stattools import grangercausalitytests
except Exception:  # pragma: no cover
    grangercausalitytests = None

try:
    import shap
except Exception:  # pragma: no cover
    shap = None


def correlation_analysis(df: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    subset = df[[c for c in columns if c in df.columns]].copy()
    if subset.empty:
        return {"pearson": {}, "spearman": {}}
    pearson = subset.corr(method="pearson").round(4).fillna(0.0).to_dict()
    spearman = subset.corr(method="spearman").round(4).fillna(0.0).to_dict()
    return {"pearson": pearson, "spearman": spearman}


def granger_causality_analysis(df: pd.DataFrame, target: str, candidates: list[str], maxlag: int = 5) -> dict[str, Any]:
    if grangercausalitytests is None:
        return {"available": False, "reason": "statsmodels is not installed"}
    result: dict[str, Any] = {"available": True, "results": {}}
    for col in candidates:
        if col not in df.columns or target not in df.columns:
            continue
        test_df = df[[target, col]].dropna()
        if len(test_df) <= maxlag + 2:
            continue
        try:
            tests = grangercausalitytests(test_df[[target, col]], maxlag=maxlag, verbose=False)
            result["results"][col] = {
                str(lag): {
                    "ssr_ftest_pvalue": float(stats[0]["ssr_ftest"][1]),
                    "ssr_chi2test_pvalue": float(stats[0]["ssr_chi2test"][1]),
                }
                for lag, stats in tests.items()
            }
        except Exception as exc:  # pragma: no cover
            result["results"][col] = {"error": str(exc)}
    return result


def random_forest_feature_importance(df: pd.DataFrame, target: str) -> list[dict[str, Any]]:
    if target not in df.columns:
        return []
    numeric_df = df.select_dtypes(include=[np.number]).dropna().copy()
    if target not in numeric_df.columns or numeric_df.empty:
        return []
    X = numeric_df.drop(columns=[target], errors="ignore")
    X = X.drop(columns=["market_cap"], errors="ignore")
    y = numeric_df[target]
    if X.empty or len(X) < 5:
        return []
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    importances = sorted(zip(X.columns, model.feature_importances_), key=lambda x: x[1], reverse=True)
    return [{"feature": name, "importance": float(score), "rank": idx + 1} for idx, (name, score) in enumerate(importances)]


def shap_summary(df: pd.DataFrame, target: str, sample_size: int = 128) -> list[dict[str, Any]]:
    if shap is None:
        return []
    numeric_df = df.select_dtypes(include=[np.number]).dropna().copy()
    if target not in numeric_df.columns or len(numeric_df) < 5:
        return []
    X = numeric_df.drop(columns=[target], errors="ignore")
    X = X.drop(columns=["market_cap"], errors="ignore")
    y = numeric_df[target]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    sample = X.sample(min(sample_size, len(X)), random_state=42)
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(sample)
    mean_abs = np.abs(values).mean(axis=0)
    ranking = sorted(zip(sample.columns, mean_abs), key=lambda x: x[1], reverse=True)
    return [{"feature": name, "shap_value": float(score), "rank": idx + 1} for idx, (name, score) in enumerate(ranking)]
