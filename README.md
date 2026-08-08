# Pair Trading & Statistical Arbitrage — MSFT/GOOGL puis V/MA

Projet de portfolio quant : détection de paires d'actions cointégrées et backtest
d'une stratégie de trading basée sur le retour à la moyenne (mean-reversion) du spread.

Aucune API payante utilisée — uniquement des sources gratuites (yfinance).

---

## 📖 Glossaire (pour les non-financiers)

- **Cointégration** : deux séries de prix sont cointégrées si leur écart (spread) reste
  statistiquement stable dans le temps, même si chaque prix individuellement fluctue
  beaucoup. C'est différent d'une simple corrélation : deux actions peuvent monter
  ensemble sans que leur écart soit stable.
- **Spread** : la différence (pondérée) entre les prix des deux actions de la paire.
  Formule utilisée ici : `spread = prix_1 - (ratio_couverture × prix_2)`.
- **Ratio de couverture (hedge ratio)** : combien d'actions du titre 2 il faut détenir
  pour 1 action du titre 1, pour que le spread soit le plus stable possible. Calculé
  par régression linéaire (OLS).
- **Z-score** : mesure de combien d'écarts-types le spread actuel s'éloigne de sa
  moyenne historique. Un z-score de +2 veut dire "le spread est 2 écarts-types
  au-dessus de sa moyenne habituelle" — statistiquement un écart rare.
- **Mean-reversion (retour à la moyenne)** : hypothèse selon laquelle un spread qui
  s'écarte trop de sa moyenne a tendance à y revenir. C'est le pari au cœur de la
  stratégie.
- **Test d'Engle-Granger** : test statistique qui donne une p-value pour juger si deux
  séries sont cointégrées. Convention : p-value < 0.05 → cointégration jugée
  significative.
- **p-value** : probabilité d'observer un résultat au moins aussi extrême si, en
  réalité, il n'y avait AUCUNE relation de cointégration. Plus elle est basse, plus la
  preuve de cointégration est solide.
- **Position longue / courte sur le spread** :
  - *Acheter le spread* : acheter le titre 1, vendre à découvert le titre 2 (pari sur la
    hausse du spread).
  - *Vendre le spread* : l'inverse (pari sur la baisse du spread).
- **Backtest** : simulation d'une stratégie sur des données historiques, pour évaluer
  comment elle se serait comportée dans le passé (ne garantit rien sur le futur).

---

## 🧱 Pipeline

```
data/recuperation.py        → télécharge les prix (yfinance)
analyse/cointegration.py    → test d'Engle-Granger + calcul du spread et du z-score
strategie/signaux.py        → génère les signaux ACHETER / VENDRE / CLOTURER / NEUTRE
backtest/simulateur.py      → simule les trades et calcule les statistiques
main.py                     → orchestre tout le pipeline + graphique
tester_paires.py            → criblage rapide de plusieurs paires candidates
```

Modèles de données (Pydantic) dans `models/schema.py` : `PrixJournalier`,
`PaireActions`, `PointSpread`, `SignalTrading`, `TradeSimule`.

---

## ▶️ Lancer le projet

```bash
pip install -r requirements.txt
python main.py
```

Génère un fichier `backtest_resultat.png` avec le spread, le z-score et les seuils de
trading.

Pour tester d'autres paires candidates :

```bash
python tester_paires.py
```

---

## 📊 Résultats

### V1 — MSFT/GOOGL (rejetée honnêtement)

Test de cointégration : **p = 0.35** → pas significatif (seuil : 0.05). Cette paire n'a
donc **pas** été retenue pour le backtest. Conservé dans l'historique du projet par
souci de transparence méthodologique : un résultat négatif documenté vaut mieux qu'un
résultat positif maquillé.

### V2 — Criblage de 5 paires sectorielles

Script `tester_paires.py` sur JPM/BAC, XOM/CVX, KO/PEP, V/MA, HD/LOW :

| Paire   | p-value | Cointégrée ? |
|---------|---------|--------------|
| V/MA    | 0.0021  | ✅            |
| HD/LOW  | 0.2697  | ❌            |
| KO/PEP  | 0.8026  | ❌            |
| XOM/CVX | 0.8100  | ❌            |
| JPM/BAC | 0.9101  | ❌            |

### Backtest final — V/MA (Visa / Mastercard)

- Cointégration : **p = 0.0021**, ratio de couverture = 0.5402
- Seuils : entrée à |z-score| ≥ 2.0, sortie à |z-score| ≤ 0.5
- **4 trades** sur la période 2022–2024, **100% de réussite**, profit total positif

---

## ⚠️ Limites (à lire avant toute conclusion hâtive)

- **Échantillon petit** : 4 trades ne suffisent pas à prouver statistiquement la
  robustesse de la stratégie. Un taux de réussite de 100% sur un si petit nombre
  d'essais peut facilement être dû au hasard.
- **P&L en "unités de spread"**, pas en dollars réels avec tailles de position et
  capital alloué — simplification volontaire pour rester pédagogique et lisible.
  Une V3 pourrait ajouter un sizing réel en capital.
- **Pas de frais de marché réalistes** (slippage, coût d'emprunt du titre vendu à
  découvert) au-delà d'un forfait de 0.1% par transaction.
- **Backtest ≠ garantie future** : la cointégration observée sur 2022–2024 peut se
  rompre (changement structurel du secteur, fusion, etc.).

---

## 🔧 Stack technique

Python, pandas, numpy, statsmodels (test de cointégration), pydantic (modèles de
données validés), matplotlib (visualisation), yfinance (données gratuites, sans clé
API).