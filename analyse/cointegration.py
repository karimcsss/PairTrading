"""
Test de cointégration entre deux actions.

Idée : si deux actions sont "cointégrées", leur écart (spread) reste stable
dans le temps même si chaque prix individuellement varie beaucoup.
On utilise le test d'Engle-Granger (statsmodels le fait en une fonction).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm

from models.schema import PaireActions, PointSpread


def tester_cointegration(prix_1: pd.Series, prix_2: pd.Series, ticker_1: str, ticker_2: str) -> PaireActions:
    """
    Teste si deux séries de prix sont cointégrées.

    p_value < 0.05 : on rejette "pas de relation stable" -> probablement cointégrées
    p_value >= 0.05 : pas assez de preuve -> on ne trade pas cette paire

    Returns:
        PaireActions avec le résultat du test et le ratio de couverture (hedge ratio)
    """
    # aligner les deux séries sur les mêmes dates
    donnees = pd.concat([prix_1, prix_2], axis=1, join="inner")
    donnees.columns = [ticker_1, ticker_2]

    score, p_value, _ = coint(donnees[ticker_1], donnees[ticker_2])

    # calcul du hedge ratio via régression linéaire : prix_1 = ratio * prix_2 + constante
    modele = sm.OLS(donnees[ticker_1], sm.add_constant(donnees[ticker_2])).fit()
    ratio_couverture = modele.params[ticker_2]

    return PaireActions(
        ticker_1=ticker_1,
        ticker_2=ticker_2,
        est_cointegree=p_value < 0.05,
        p_value=round(p_value, 4),
        ratio_couverture=round(ratio_couverture, 4),
    )


def calculer_spread(prix_1: pd.Series, prix_2: pd.Series, ratio_couverture: float) -> pd.DataFrame:
    """
    Calcule le spread (écart) entre les deux actions et son z-score.

    spread = prix_1 - (ratio_couverture * prix_2)
    z_score = combien d'écarts-types le spread actuel est de sa moyenne historique
    """
    donnees = pd.concat([prix_1, prix_2], axis=1, join="inner")
    donnees.columns = ["prix_1", "prix_2"]

    donnees["spread"] = donnees["prix_1"] - (ratio_couverture * donnees["prix_2"])

    moyenne = donnees["spread"].mean()
    ecart_type = donnees["spread"].std()
    donnees["z_score"] = (donnees["spread"] - moyenne) / ecart_type

    return donnees[["spread", "z_score"]]


if __name__ == "__main__":
    from data.recuperation import recuperer_prix, prix_vers_dataframe

    prix_msft = prix_vers_dataframe(recuperer_prix("MSFT", "2022-01-01", "2024-12-31"))
    prix_googl = prix_vers_dataframe(recuperer_prix("GOOGL", "2022-01-01", "2024-12-31"))

    resultat = tester_cointegration(prix_msft["prix"], prix_googl["prix"], "MSFT", "GOOGL")
    print(f"Résultat du test :\n{resultat}\n")

    if resultat.est_cointegree:
        print("-> MSFT et GOOGL semblent cointégrées, on peut construire le spread.")
    else:
        print("-> Pas assez de preuve de cointégration sur cette période.")

    spread_df = calculer_spread(prix_msft["prix"], prix_googl["prix"], resultat.ratio_couverture)
    print(f"\nAperçu du spread :\n{spread_df.tail()}")