"""
Génération de signaux de trading à partir du spread et de son z-score.

Logique du pair trading (stratégie de retour à la moyenne / mean-reversion) :
- Si le spread est TROP HAUT (z-score très positif) -> on s'attend à ce qu'il
  redescende -> on VEND le spread (vendre l'action 1, acheter l'action 2 * ratio)
- Si le spread est TROP BAS (z-score très négatif) -> on s'attend à ce qu'il
  remonte -> on ACHETE le spread (acheter l'action 1, vendre l'action 2 * ratio)
- Quand le spread revient proche de sa moyenne (z-score proche de 0) -> on CLOTURE
  la position, qu'elle soit gagnante ou perdante à ce stade.

On ne prend qu'une position à la fois (pas d'empilement de trades).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from models.schema import SignalTrading


def generer_signaux(
    spread_df: pd.DataFrame,
    seuil_entree: float = 2.0,
    seuil_sortie: float = 0.5,
) -> list[SignalTrading]:
    """
    Parcourt le spread jour par jour et génère un signal à chaque date.

    Args:
        spread_df: DataFrame avec colonnes "spread" et "z_score" (index = dates),
                   typiquement le résultat de `calculer_spread()`.
        seuil_entree: |z_score| au-dessus duquel on ouvre une position.
        seuil_sortie: |z_score| en dessous duquel on clôture une position ouverte.

    Returns:
        Liste de SignalTrading, un par jour (y compris les jours "NEUTRE").
    """
    if seuil_sortie >= seuil_entree:
        raise ValueError("seuil_sortie doit être strictement inférieur à seuil_entree")

    signaux: list[SignalTrading] = []
    position_ouverte = False
    sens_position: str | None = None  # "ACHETER_SPREAD" ou "VENDRE_SPREAD"

    for date_cours, ligne in spread_df.iterrows():
        z = ligne["z_score"]

        if pd.isna(z):
            signaux.append(
                SignalTrading(
                    date_cours=date_cours,
                    action="NEUTRE",
                    z_score=0.0,
                    raison="z-score non disponible (donnée manquante ou fenêtre insuffisante)",
                )
            )
            continue

        if not position_ouverte:
            if z >= seuil_entree:
                position_ouverte = True
                sens_position = "VENDRE_SPREAD"
                signaux.append(
                    SignalTrading(
                        date_cours=date_cours,
                        action="VENDRE_SPREAD",
                        z_score=round(float(z), 4),
                        raison=f"z-score={z:.2f} >= seuil {seuil_entree}, spread trop écarté au-dessus de sa moyenne",
                    )
                )
            elif z <= -seuil_entree:
                position_ouverte = True
                sens_position = "ACHETER_SPREAD"
                signaux.append(
                    SignalTrading(
                        date_cours=date_cours,
                        action="ACHETER_SPREAD",
                        z_score=round(float(z), 4),
                        raison=f"z-score={z:.2f} <= seuil -{seuil_entree}, spread trop écarté en dessous de sa moyenne",
                    )
                )
            else:
                signaux.append(
                    SignalTrading(
                        date_cours=date_cours,
                        action="NEUTRE",
                        z_score=round(float(z), 4),
                        raison="pas de signal, z-score dans la zone neutre",
                    )
                )
        else:
            if abs(z) <= seuil_sortie:
                signaux.append(
                    SignalTrading(
                        date_cours=date_cours,
                        action="CLOTURER",
                        z_score=round(float(z), 4),
                        raison=f"z-score={z:.2f} revenu proche de 0 (<= {seuil_sortie}), on clôture la position",
                    )
                )
                position_ouverte = False
                sens_position = None
            else:
                signaux.append(
                    SignalTrading(
                        date_cours=date_cours,
                        action="NEUTRE",
                        z_score=round(float(z), 4),
                        raison=f"position {sens_position} toujours ouverte, en attente de retour à la moyenne",
                    )
                )

    return signaux


if __name__ == "__main__":
    from data.recuperation import recuperer_prix, prix_vers_dataframe
    from analyse.cointegration import tester_cointegration, calculer_spread

    prix_msft = prix_vers_dataframe(recuperer_prix("MSFT", "2022-01-01", "2024-12-31"))
    prix_googl = prix_vers_dataframe(recuperer_prix("GOOGL", "2022-01-01", "2024-12-31"))

    resultat = tester_cointegration(prix_msft["prix"], prix_googl["prix"], "MSFT", "GOOGL")
    spread_df = calculer_spread(prix_msft["prix"], prix_googl["prix"], resultat.ratio_couverture)

    signaux = generer_signaux(spread_df)
    actifs = [s for s in signaux if s.action != "NEUTRE"]

    print(f"{len(actifs)} signaux actifs sur {len(signaux)} jours.\n")
    for s in actifs[:10]:
        print(s)