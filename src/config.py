import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Charger les variables d'environnement du fichier .env
load_dotenv()

# 2. Gestion dynamique des chemins (Pas de chemins écrits en dur)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

# Création automatique des dossiers s'ils n'existent pas encore
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# 3. Base de données
DB_PATH = DATA_DIR / "macro.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# 4. Clés API
FRED_API_KEY = os.getenv("FRED_API_KEY")

# 5. Configuration Macro (La cible du modèle)
TARGET_SERIES = "CPIAUCSL"  # Code officiel FRED pour le US CPI (Consumer Price Index)

# Actifs financiers à suivre sur Yahoo Finance
MARKET_TICKERS = {
    "WTI": "CL=F",
    "DXY": "DX-Y.NYB",
    "SPY": "SPY",
    "GOLD": "GC=F"
}