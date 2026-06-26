#!/usr/bin/env python3
"""lingsign_hook.py — H5: does the model develop a stable, distinctive way of TALKING the
fabricated category, with markers ABSENT from the seed?

This is the bridge to your LingSign/BRM backbone. Skeleton does three things:
  1. Build a feature matrix from responses (plug your LingSign extractor where marked).
  2. Train a blinded classifier to separate DN-talk vs anchor-talk vs incoherent-talk.
     Above-chance separability = the category has acquired a signature.
  3. Emergence check: of the top discriminative markers, what fraction are ABSENT from the seed?
     High fraction => the signature was fabricated, not parroted (the anti-circular result).
"""
import pathlib, json
import pandas as pd, numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCORED = ROOT / "data" / "scored" / "scored.jsonl"

def lingsign_features(text: str) -> dict:
    """TODO: replace with your real LingSign extractor.
    Placeholder returns a few transparent, theory-light surface features so the pipeline runs."""
    toks = text.split()
    return {
        "len": len(toks),
        "first_person_sing": sum(t.lower() in {"yo","me","mi","mí","conmigo"} for t in toks),
        "absolutist": sum(t.lower() in {"siempre","nunca","todo","nada","completamente"} for t in toks),
        "hedge": sum(t.lower() in {"quizá","tal","vez","posiblemente","parece"} for t in toks),
    }

def main():
    rows = [json.loads(l) for l in SCORED.open()]
    df = pd.DataFrame(rows)
    feats = pd.DataFrame([lingsign_features(r) for r in df["response"]])
    X = pd.concat([df[["disorder","level"]].reset_index(drop=True), feats], axis=1)

    # keep the three talk-types for the separability test
    mask = X["disorder"].isin(["DN_plausible","real_anchor","incoherent"])
    Xs = X[mask]
    print("Feature means by disorder (talk-type signature):")
    print(Xs.groupby("disorder")[feats.columns.tolist()].mean().round(2))

    # --- classifier separability (H5 part 1) ---
    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import cross_val_score
        y = Xs["disorder"].values
        Xmat = Xs[feats.columns].values
        if len(np.unique(y)) >= 2 and len(Xs) >= 30:
            acc = cross_val_score(LogisticRegression(max_iter=1000), Xmat, y, cv=5).mean()
            chance = 1/len(np.unique(y))
            print(f"\nCV accuracy separating talk-types: {acc:.3f} (chance ≈ {chance:.3f})")
            print("Above chance => the fabricated category acquired a distinctive signature.")
        else:
            print("\nNot enough scored data yet for the classifier.")
    except ImportError:
        print("\n(install scikit-learn for the separability classifier)")

    # --- emergence check (H5 part 2) ---
    print("\nEMERGENCE: compare top discriminative markers against the seed payload.")
    print("Fraction of signature markers ABSENT from the seed = the anti-circular result.")
    print("TODO: rank markers by classifier weight; intersect with seed tokens; report fraction.")

if __name__ == "__main__":
    main()
