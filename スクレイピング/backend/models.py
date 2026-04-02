from pydantic import BaseModel
from typing import List, Optional

class Racer(BaseModel):
    waku: int
    name: str
    rate_global: float
    st_average: float
    st_course: Optional[int] = None
    exhibition_time: float
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None
    racer_comment: Optional[str] = None

class ExhibitionInfo(BaseModel):
    waku: int
    exhibition_time: float
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None

class PredictionResult(BaseModel):
    waku: int
    score: float
    rank_prediction: int
