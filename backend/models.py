from pydantic import BaseModel
from typing import List, Optional

class Racer(BaseModel):
    waku: int
    name: str
    rate_global: float
    st_average: float
    st_course: Optional[int] = None
    exhibition_time: float
    exhibition_rank: Optional[int] = None
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None
    comment: Optional[str] = None

class ExhibitionInfo(BaseModel):
    waku: int
    exhibition_time: float
    exhibition_rank: Optional[int] = None
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None

class Prediction(BaseModel):
    waku: int
    score: float
    rank_prediction: Optional[int] = None

class RaceInfo(BaseModel):
    hd: str
    jcd: str
    rno: int
    racelist_url: str
    beforeinfo_url: str
    racers: List[Racer]
    predictions: List[Prediction]
    is_mock: bool
