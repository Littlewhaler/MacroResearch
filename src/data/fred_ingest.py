import time
import logging
from datetime import datetime, datetime as dt
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Importation de vos configurations propres (Stage 1)
from src.config import DATABASE_URL, FRED_API_KEY, TARGET_SERIES
from src.data.models import Base, MacroData  # On suppose que le modèle est dans src/data/models.py

# Configuration du logging pour suivre l'exécution sur le VPS
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def fetch_fred_series(series_id: str, max_retries: int = 5, base_delay: float = 2.0) -> dict:
    """Télécharge une série FRED avec un algorithme de retry de type exponential backoff."""
    if not FRED_API_KEY:
        raise ValueError("FRED_API_KEY manquante dans les variables d'environnement.")

    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "realtime_start": "1776-07-04",  # On demande l'historique depuis le début
        "realtime_end": "9999-12-31"
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                logger.error(f"Échec définitif après {max_retries} tentatives pour {series_id}.")
                raise e
            delay = base_delay * (2 ** attempt)  # Évolution : 2s, 4s, 8s, 16s...
            logger.warning(f"Erreur API ({e}). Nouvelle tentative dans {delay}s...")
            time.sleep(delay)
    return {}

def save_to_sqlite(data: dict, series_id: str) -> None:
    """Valide, formate et insère les observations dans la base SQLite locale."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)  # Crée la table si elle n'existe pas
    Session = sessionmaker(bind=engine)
    
    rows_added = 0
    gaps_detected = 0

    with Session() as session:
        observations = data.get("observations", [])
        
        for obs in observations:
            # Gestion des valeurs manquantes indiquées par '.' dans la FRED
            raw_val = obs.get("value")
            if raw_val == "." or raw_val is None:
                gaps_detected += 1
                continue
            
            try:
                # Parsing strict des dates pour le respect du Point-in-Time
                ref_date = datetime.strptime(obs["date"], "%Y-%m-%d").date()
                rel_date = datetime.strptime(obs["realtime_start"], "%Y-%m-%d").date()
                val = float(raw_val)
                
                # Préparation de la ligne
                macro_row = MacroData(
                    series_id=series_id,
                    source="FRED",
                    date=ref_date,
                    release_date=rel_date,
                    value=val,
                    fetched_at=dt.utcnow()
                )
                
                # Fusion (Upsert) pour éviter les doublons si le script tourne plusieurs fois
                session.merge(macro_row)
                rows_added += 1
                
            except (ValueError, KeyError) as e:
                logger.debug(f"Donnée ignorée ou mal formatée : {obs}. Erreur : {e}")
                continue
        
        session.commit()
    
    logger.info(f"Ingestion terminée pour {series_id} : {rows_added} lignes insérées, {gaps_detected} valeurs manquantes détectées.")

if __name__ == "__main__":
    logger.info(f"Démarrage de l'ingestion de la cible : {TARGET_SERIES}")
    try:
        raw_data = fetch_fred_series(TARGET_SERIES)
        save_to_sqlite(raw_data, TARGET_SERIES)
    except Exception as error:
        logger.critical(f"Plantage de la pipeline d'ingestion : {error}")