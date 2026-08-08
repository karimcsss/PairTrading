"""
Backtest de la stratégie de pair trading à partir des signaux générés.

Simplification pédagogique (à noter dans le README) : on raisonne en
"unités de spread" plutôt qu'en dollars réels avec des tailles de position
complexes. Une unité de spread = 1 action de ticker_1 contre `ratio_couverture`
actions de ticker_2. Le profit/perte d'un trade est la variation du spread
entre l'entrée et la sortie (inversée si on est vendeur du spread).

Frais de transaction : coût forfaitaire en pourcentage de la valeur absolue
du spread à l'entrée et à la sortie, pour rester réaliste (0.1% par défaut,
proche des frais d'un courtier low-cost / discount broker).
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import pandas as pd

from models.schema import SignalTrading, TradeSimule


def simuler_backtest(
    signaux: list[SignalTrading],
    spread_df: pd.DataFrame,
    frais_pourcentage: float = 0.001,
) -> list[TradeSimule]:
    """
    Simule les trades à partir des signaux, en calculant le profit/perte de chaque trade clôturé.

    Args:
        signaux: liste de SignalTrading (sortie de `generer_signaux()`)
        spread_df: DataFrame avec la colonne "spread", même index que les signaux
        frais_pourcentage: coût de transaction, en fraction (0.001 = 0.1%)

    Returns:
        Liste de TradeSimule, un par trade clôturé (les positions encore ouvertes
        à la fin de la période ne sont pas incluses).
    """
    trades: list[TradeSimule] = []
    trade_en_cours: TradeSimule | None = None
    sens_en_cours: str | None = None

    spread_par_date = spread_df["spread"]

    for signal in signaux:
        if signal.action in ("ACHETER_SPREAD", "VENDRE_SPREAD"):
            trade_en_cours = TradeSimule(
                date_entree=signal.date_cours,
                z_score_entree=signal.z_score,
            )
            sens_en_cours = signal.action

        elif signal.action == "CLOTURER" and trade_en_cours is not None:
            spread_entree = spread_par_date.loc[trade_en_cours.date_entree]
            spread_sortie = spread_par_date.loc[signal.date_cours]

            if sens_en_cours == "ACHETER_SPREAD":
                pnl_brut = spread_sortie - spread_entree
            else:  # VENDRE_SPREAD
                pnl_brut = spread_entree - spread_sortie

            frais = frais_pourcentage * (abs(spread_entree) + abs(spread_sortie))

            trade_en_cours.date_sortie = signal.date_cours
            trade_en_cours.profit_perte = round(float(pnl_brut - frais), 4)
            trade_en_cours.frais_transaction = round(float(frais), 4)

            trades.append(trade_en_cours)
            trade_en_cours = None
            sens_en_cours = None

    return trades


def statistiques_backtest(trades: list[TradeSimule]) -> dict:
    """
    Calcule des statistiques résumées sur les trades clôturés.

    Returns:
        Dictionnaire avec nombre de trades, taux de réussite, profit total,
        profit moyen par trade, meilleur et pire trade.
    """
    trades_clotures = [t for t in trades if t.profit_perte is not None]

    if not trades_clotures:
        return {
            "nombre_trades": 0,
            "taux_reussite_pct": None,
            "profit_total": 0.0,
            "profit_moyen": None,
            "gain_max": None,
            "perte_max": None,
        }

    profits = [t.profit_perte for t in trades_clotures]
    gagnants = [p for p in profits if p > 0]

    return {
        "nombre_trades": len(trades_clotures),
        "taux_reussite_pct": round(len(gagnants) / len(trades_clotures) * 100, 1),
        "profit_total": round(sum(profits), 4),
        "profit_moyen": round(sum(profits) / len(profits), 4),
        "gain_max": round(max(profits), 4),
        "perte_max": round(min(profits), 4),
    }


if __name__ == "__main__":
    from data.recuperation import recuperer_prix, prix_vers_dataframe
    from analyse.cointegration import tester_cointegration, calculer_spread
    from strategie.signaux import generer_signaux

    prix_msft = prix_vers_dataframe(recuperer_prix("MSFT", "2022-01-01", "2024-12-31"))
    prix_googl = prix_vers_dataframe(recuperer_prix("GOOGL", "2022-01-01", "2024-12-31"))

    resultat = tester_cointegration(prix_msft["prix"], prix_googl["prix"], "MSFT", "GOOGL")
    spread_df = calculer_spread(prix_msft["prix"], prix_googl["prix"], resultat.ratio_couverture)
    signaux = generer_signaux(spread_df)

    trades = simuler_backtest(signaux, spread_df)
    stats = statistiques_backtest(trades)

    print(f"{len(trades)} trades clôturés.\n")
    for cle, valeur in stats.items():
        print(f"{cle} : {valeur}")