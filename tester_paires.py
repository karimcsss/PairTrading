"""
Test rapide de cointégration sur plusieurs paires candidates.
Objectif : trouver une paire avec p_value < 0.05 pour un backtest qui a du sens.

Lance simplement : python tester_paires.py
"""

from data.recuperation import recuperer_prix, prix_vers_dataframe
from analyse.cointegration import tester_cointegration

DATE_DEBUT, DATE_FIN = "2022-01-01", "2024-12-31"

PAIRES_CANDIDATES = [
    ("JPM", "BAC"),    # banques US
    ("XOM", "CVX"),    # pétrole/énergie
    ("KO", "PEP"),     # boissons
    ("V", "MA"),       # paiements
    ("HD", "LOW"),     # bricolage/distribution
]

resultats = []

for t1, t2 in PAIRES_CANDIDATES:
    try:
        p1 = prix_vers_dataframe(recuperer_prix(t1, DATE_DEBUT, DATE_FIN))
        p2 = prix_vers_dataframe(recuperer_prix(t2, DATE_DEBUT, DATE_FIN))
        res = tester_cointegration(p1["prix"], p2["prix"], t1, t2)
        resultats.append(res)
        marqueur = "✅" if res.est_cointegree else "❌"
        print(f"{marqueur} {t1}/{t2} : p={res.p_value}, ratio={res.ratio_couverture}")
    except Exception as e:
        print(f"⚠️  {t1}/{t2} : erreur - {e}")

print("\n=== Classement par p-value (plus bas = mieux) ===")
for res in sorted(resultats, key=lambda r: r.p_value):
    print(f"{res.ticker_1}/{res.ticker_2} : p={res.p_value}")