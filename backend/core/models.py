from typing import Optional
from sqlmodel import Field, SQLModel, create_engine
from datetime import datetime

class CandidateKeyword(SQLModel, table=True):
    """Modulo 1: Radar Idee (TikTok, Reddit, Kickstarter)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    keyword: str = Field(index=True, unique=True)
    source: str
    category: str
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    initial_traction_score: int
    
class ProductTrend(SQLModel, table=True):
    """Modulo 2: Convalida Trend (Google Trends)"""
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidatekeyword.id")
    trend_score: float  # Normalizzato 0-100
    is_breakout: bool = False
    slope: float  # Pendenza media 90gg
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Economics(SQLModel, table=True):
    """Moduli 3 e 5: Benchmark Fabbrica e Calcolo Margini FBA"""
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidatekeyword.id")
    estimated_factory_cost_eur: float
    amazon_buybox_price_eur: float
    fba_fee_eur: float
    landed_cost_eur: float
    net_margin_percent: float
    is_compliant: bool = True
    rejected_reason: Optional[str] = None
    
class Competitor(SQLModel, table=True):
    """Modulo 4: Controllo Concorrenza Amazon"""
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidatekeyword.id")
    asin: str = Field(index=True)
    title: str
    brand: str
    price_eur: float
    review_count: int
    rating: float
    position: int
    
class Opportunity(SQLModel, table=True):
    """Score finale e aggregazione"""
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidatekeyword.id")
    final_score: float
    badge_color: str  # "Verde", "Giallo", "Rosso"
    calculated_at: datetime = Field(default_factory=datetime.utcnow)

# Database Setup
sqlite_file_name = "trendradar.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
