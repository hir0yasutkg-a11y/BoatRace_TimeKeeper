from pydantic import BaseModel
from typing import List, Optional

class MotorHistory(BaseModel):
    avg_exhibition: float = 0.0
    avg_lap: float = 0.0
    avg_turn: float = 0.0
    avg_straight: float = 0.0
    record_count: int = 0

class CourseStats(BaseModel):
    course: int
    entry_count: int = 0
    win_rate: float = 0.0
    place2_rate: float = 0.0
    place3_rate: float = 0.0
    avg_st: float = 0.0
    avg_st_rank: float = 0.0
    kimarite_nige: int = 0
    kimarite_sashi: int = 0
    kimarite_makuri: int = 0
    kimarite_mashi: int = 0

class CommentEntry(BaseModel):
    date: str
    jcd: str
    content: str

class SeriesResultEntry(BaseModel):
    date: str
    jcd: str
    rno: int
    course: Optional[int] = None
    st: Optional[float] = None
    rank: Optional[int] = None

class Racer(BaseModel):
    waku: int
    name: str
    racer_id: Optional[str] = None # 登録番号
    rate_global: float
    rate_global_2: Optional[float] = None
    st_average: float
    rate_local: Optional[float] = None
    rate_local_2: Optional[float] = None
    motor_no: Optional[str] = None # モーター番号
    motor_rate_2: Optional[float] = None
    boat_no: Optional[str] = None  # ボート番号
    boat_rate_2: Optional[float] = None
    history: Optional[MotorHistory] = None # モーター履歴
    course_stats: List[CourseStats] = []    # 1-6コース別の全統計
    rank: Optional[str] = None
    st_course: Optional[int] = None # スタートコース
    exhibition_time: float
    exhibition_rank: Optional[int] = None
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None
    entry_course: Optional[int] = None # 司令塔として、展示進入コースを 1 mm の狂いもなく捕捉
    comment: Optional[str] = None
    comment_history: List[CommentEntry] = [] # 過去のコメント履歴
    series_results: List[SeriesResultEntry] = [] # 今節の成績履歴

class ExhibitionInfo(BaseModel):
    waku: int
    exhibition_time: float
    exhibition_rank: Optional[int] = None
    lap_time: Optional[float] = None
    turn_time: Optional[float] = None
    straight_time: Optional[float] = None
    entry_course: Optional[int] = None # 司令塔として、展示進入コースを 1 mm の狂いもなく捕捉

class Prediction(BaseModel):
    waku: int
    score: float
    rank_prediction: Optional[int] = None

class RaceInfo(BaseModel):
    hd: str
    jcd: str
    rno: int
    scheduled_start: Optional[str] = None # 司令塔として、 1 mm の狂いもない締切時刻を 100% 確実に捕捉
    racelist_url: str
    beforeinfo_url: str
    racers: List[Racer]
    predictions: List[Prediction]
    is_mock: bool
