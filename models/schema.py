"""
Modèles de données pour le projet de pair trading (V1).
On modélise : les prix bruts, le spread entre deux actions, et les signaux de trading.
"""

from datetime import date
from pydantic import BaseModel, Field
from typing import Literal


class PrixJournalier(BaseModel):
    """Prix de clôture d'une action à une date donnée."""
    ticker: str  # ex: "JPM", "BAC"
    date_cours: date
    prix_cloture: float = Field(gt=0, description="Prix de clôture, doit être positif")


class PaireActions(BaseModel):
    """Représente une paire d'actions qu'on teste pour cointégration."""
    ticker_1: str
    ticker_2: str
    est_cointegree: bool
    p_value: float  # résultat du test statistique (< 0.05 = probablement cointégrée)
    ratio_couverture: float  # combien d'actions de ticker_2 pour 1 action de ticker_1 (hedge ratio)


class PointSpread(BaseModel):
    """Un point du spread (écart) entre les deux actions à une date donnée."""
    date_cours: date
    valeur_spread: float
    z_score: float  # à combien d'écarts-types le spread est de sa moyenne


class SignalTrading(BaseModel):
    """Signal généré par la stratégie à une date donnée."""
    date_cours: date
    action: Literal["ACHETER_SPREAD", "VENDRE_SPREAD", "NEUTRE", "CLOTURER"]
    z_score: float
    raison: str  # explication lisible, ex: "z-score > 2, spread trop écarté"


class TradeSimule(BaseModel):
    """Un trade simulé pendant le backtest, avec son résultat."""
    date_entree: date
    date_sortie: date | None = None
    z_score_entree: float
    profit_perte: float | None = None  # None tant que le trade n'est pas clôturé
    frais_transaction: float = 0.0