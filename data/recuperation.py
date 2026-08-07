"""
Récupération des prix historiques via yfinance (gratuit).
Convertit les données brutes en liste de PrixJournalier (nos modèles Pydantic).
"""

import sys
from pathlib import Path

# permet d'importer models/schema.py depuis ce fichier
sys.path.append(str(Path(__file__).resolve().parent.parent))

import yfinance as yf
import pandas as pd
from models.schema import PrixJournalier


def recuperer_prix(ticker: str, date_debut: str, date_fin: str) -> list[PrixJournalier]:
    """
    Télécharge les prix de clôture pour un ticker donné entre deux dates.

    Args:
        ticker: symbole boursier, ex "MSFT"
        date_debut: format "AAAA-MM-JJ", ex "2020-01-01"
        date_fin: format "AAAA-MM-JJ", ex "2024-12-31"

    Returns:
        Liste de PrixJournalier, un par jour de bourse.
    """
    donnees = yf.download(ticker, start=date_debut, end=date_fin, progress=False)

    if donnees.empty:
        raise ValueError(f"Aucune donnée trouvée pour {ticker}")

    # yfinance renvoie parfois des colonnes multi-niveaux (MultiIndex), on nettoie
    if isinstance(donnees.columns, pd.MultiIndex):
        donnees.columns = donnees.columns.get_level_values(0)

    prix_liste = []
    for date_idx, ligne in donnees.iterrows():
        prix_liste.append(
            PrixJournalier(
                ticker=ticker,
                date_cours=date_idx.date(),
                prix_cloture=float(ligne["Close"]),
            )
        )

    return prix_liste


def prix_vers_dataframe(prix_liste: list[PrixJournalier]) -> pd.DataFrame:
    """Convertit une liste de PrixJournalier en DataFrame pandas (plus facile pour l'analyse)."""
    return pd.DataFrame(
        [{"date": p.date_cours, "prix": p.prix_cloture} for p in prix_liste]
    ).set_index("date")


if __name__ == "__main__":
    # test rapide
    prix_msft = recuperer_prix("MSFT", "2022-01-01", "2024-12-31")
    print(f"MSFT : {len(prix_msft)} jours récupérés")
    print(f"Premier jour : {prix_msft[0]}")
    print(f"Dernier jour : {prix_msft[-1]}")