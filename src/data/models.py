import datetime as dt
from sqlalchemy import String, Float, DateTime, Date, PrimaryKeyConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """Classe de base déclarative pour SQLAlchemy."""
    pass

class MacroData(Base):
    """Table de stockage Point-in-Time pour les données macro et de marché."""
    __tablename__ = "macro_data"

    series_id: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)  # 'FRED', 'YFINANCE'
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)  # Date de référence (ex: mois du CPI)
    release_date: Mapped[dt.date] = mapped_column(Date, nullable=False)  # Date de publication réelle
    value: Mapped[float] = mapped_column(Float, nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)

    # Clé primaire composite pour gérer les révisions successives sans doublons
    __table_args__ = (
        PrimaryKeyConstraint('series_id', 'date', 'release_date', name='pk_macro_data'),
    )