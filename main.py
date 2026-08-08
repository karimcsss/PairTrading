"""
Point d'entrée du projet de pair trading / statistical arbitrage.

Pipeline complet (V2) :
1. Récupération des prix (yfinance, gratuit)
2. Test de cointégration (Engle-Granger)
3. Calcul du spread et de son z-score
4. Génération des signaux de trading (ACHETER / VENDRE / CLOTURER / NEUTRE)
5. Backtest de la stratégie et statistiques de performance
6. Graphique du spread, du z-score et des seuils de trading

Note méthodologique :
La V1 avait testé MSFT/GOOGL (p=0.35, non significatif -- documenté et
conservé dans l'historique du projet par souci de rigueur). Un criblage
rapide sur 5 paires du même secteur (tester_paires.py) a identifié V/MA
(Visa/Mastercard, secteur paiements) comme cointégrée : p=0.0021, très
en dessous du seuil de 0.05. C'est cette paire qui est utilisée ici.
"""

import matplotlib.pyplot as plt

from data.recuperation import recuperer_prix, prix_vers_dataframe
from analyse.cointegration import tester_cointegration, calculer_spread
from strategie.signaux import generer_signaux
from backtest.simulateur import simuler_backtest, statistiques_backtest


def main() -> None:
    ticker_1, ticker_2 = "V", "MA"
    date_debut, date_fin = "2022-01-01", "2024-12-31"

    print(f"Récupération des prix {ticker_1} et {ticker_2}...")
    prix_1 = prix_vers_dataframe(recuperer_prix(ticker_1, date_debut, date_fin))
    prix_2 = prix_vers_dataframe(recuperer_prix(ticker_2, date_debut, date_fin))

    print("\nTest de cointégration (Engle-Granger)...")
    resultat = tester_cointegration(prix_1["prix"], prix_2["prix"], ticker_1, ticker_2)
    print(resultat)

    if not resultat.est_cointegree:
        print(
            f"\n⚠️  ATTENTION : p-value = {resultat.p_value} >= 0.05, la cointégration "
            "n'est PAS statistiquement significative sur cette période.\n"
            "On poursuit quand même pour valider le pipeline V2 (signaux + backtest), "
            "mais les résultats ci-dessous sont à but démonstratif uniquement."
        )

    print("\nCalcul du spread et du z-score...")
    spread_df = calculer_spread(prix_1["prix"], prix_2["prix"], resultat.ratio_couverture)

    print("\nGénération des signaux de trading...")
    signaux = generer_signaux(spread_df, seuil_entree=2.0, seuil_sortie=0.5)
    nb_signaux_actifs = sum(1 for s in signaux if s.action != "NEUTRE")
    print(f"{nb_signaux_actifs} signaux actifs générés sur {len(signaux)} jours.")

    print("\nBacktest de la stratégie...")
    trades = simuler_backtest(signaux, spread_df)
    stats = statistiques_backtest(trades)

    print("\n=== Résultats du backtest ===")
    for cle, valeur in stats.items():
        print(f"{cle} : {valeur}")

    # --- graphique : spread + z-score avec seuils de trading ---
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax1.plot(spread_df.index, spread_df["spread"], label="Spread", color="steelblue")
    ax1.set_ylabel("Spread")
    ax1.set_title(f"Spread {ticker_1} - {ticker_2} (ratio de couverture = {resultat.ratio_couverture})")
    ax1.legend()

    ax2.plot(spread_df.index, spread_df["z_score"], label="Z-score", color="darkorange")
    ax2.axhline(2.0, color="red", linestyle="--", linewidth=0.8, label="Seuil entrée (±2)")
    ax2.axhline(-2.0, color="red", linestyle="--", linewidth=0.8)
    ax2.axhline(0.5, color="green", linestyle=":", linewidth=0.8, label="Seuil sortie (±0.5)")
    ax2.axhline(-0.5, color="green", linestyle=":", linewidth=0.8)
    ax2.set_ylabel("Z-score")
    ax2.set_xlabel("Date")
    ax2.legend()

    plt.tight_layout()
    plt.savefig("backtest_resultat.png", dpi=120)
    print("\nGraphique sauvegardé : backtest_resultat.png")


if __name__ == "__main__":
    main()