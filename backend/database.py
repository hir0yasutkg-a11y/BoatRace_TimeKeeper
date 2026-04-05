import os
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class Race(Base):
    __tablename__ = "races"
    id = Column(String, primary_key=True) # e.g. "20240325_03_12"
    hd = Column(String, index=True)
    jcd = Column(String)
    rno = Column(Integer)
    status = Column(String)
    scheduled_start = Column(String, nullable=True) # e.g. "15:18"
    series_name = Column(String, nullable=True)     # 司令塔として、 1 文字の漏れもなく開催名を捕捉
    series_day = Column(String, nullable=True)      # 節当（初日、〇日目、最終日）を 1 mm の狂いもなく捕捉

class Entry(Base):
    __tablename__ = "entries"
    id = Column(String, primary_key=True) # e.g. "20240325_03_12_1"
    race_id = Column(String, index=True)
    waku = Column(Integer)
    name = Column(String)
    racer_id = Column(String, nullable=True) # 選手登録番号 (4桁/5桁)
    rate_global = Column(Float)
    rate_global_2 = Column(Float, nullable=True) # 全国2連率
    st_average = Column(Float)
    rate_local = Column(Float, nullable=True)   # 当地勝率
    rate_local_2 = Column(Float, nullable=True) # 当地2連率
    motor_no = Column(String, nullable=True) # モーター番号
    motor_rate_2 = Column(Float, nullable=True) # モーター2連率
    boat_no = Column(String, nullable=True)  # ボート番号
    boat_rate_2 = Column(Float, nullable=True)  # ボート2連率
    racer_rank = Column(String, nullable=True)
    racer_comment = Column(String, nullable=True)

class Exhibition(Base):
    __tablename__ = "exhibitions"
    id = Column(String, primary_key=True)
    race_id = Column(String, index=True)
    waku = Column(Integer)
    exhibition_time = Column(Float, nullable=True)
    exhibition_rank = Column(Integer, nullable=True)
    lap_time = Column(Float, nullable=True)
    turn_time = Column(Float, nullable=True)
    straight_time = Column(Float, nullable=True)
    entry_course = Column(Integer, nullable=True) # 司令塔として、展示進入コースを 1 mm の狂いもなく捕捉

class MotorStats(Base):
    """
    モーターごとの機力履歴を蓄積するテーブル
    """
    __tablename__ = "motor_stats"
    id = Column(String, primary_key=True) # e.g. "04_17_20260404" (jcd_motor_date)
    jcd = Column(String, index=True)      # 場所
    motor_no = Column(String, index=True) # モーター番号
    date = Column(String, index=True)      # 日付
    avg_exhibition = Column(Float)         # その日の平均展示
    avg_lap = Column(Float, nullable=True)
    avg_turn = Column(Float, nullable=True)
    avg_straight = Column(Float, nullable=True)
    record_count = Column(Integer, default=1) # データのサンプル数

class RacerCourseStats(Base):
    """
    選手ごとのコース別詳細成績を蓄積するテーブル
    """
    __tablename__ = "racer_course_stats"
    id = Column(String, primary_key=True) # e.g. "racer_id_course" (4352_1)
    racer_id = Column(String, index=True)
    course = Column(Integer)               # 1-6コース
    entry_count = Column(Integer)          # 出走回数
    win_rate = Column(Float)               # 1着率 (%)
    place2_rate = Column(Float)            # 2連対率 (%)
    place3_rate = Column(Float)            # 3連対率 (%)
    avg_st = Column(Float)                 # 平均ST
    avg_st_rank = Column(Float)            # 平均スタート順位
    kimarite_nige = Column(Integer, default=0)    # 決まり手: 逃げ
    kimarite_sashi = Column(Integer, default=0)   # 決まり手: 差し
    kimarite_makuri = Column(Integer, default=0) # 決まり手: まくり
    kimarite_mashi = Column(Integer, default=0)   # 決まり手: まくり差し
    last_updated = Column(String, index=True)     # 最終更新日 (YYYYMMDD)

class RacerComment(Base):
    """
    選手ごとのコメント履歴を蓄積するテーブル
    """
    __tablename__ = "racer_comments"
    id = Column(String, primary_key=True) # e.g. "racer_id_jcd_date" (3590_04_20260404)
    racer_id = Column(String, index=True)
    jcd = Column(String, index=True)      # 場所
    date = Column(String, index=True)     # 日付
    content = Column(String)               # コメント本文

class SeriesResult(Base):
    """
    選手ごとの節間（今節）の成績を蓄積するテーブル
    """
    __tablename__ = "series_results"
    id = Column(String, primary_key=True) # e.g. "racer_id_jcd_date_rno"
    racer_id = Column(String, index=True)
    jcd = Column(String, index=True)      # 場所
    date = Column(String, index=True)     # 日付
    rno = Column(Integer)                 # レース番号
    course = Column(Integer, nullable=True) # 進入コース
    st = Column(Float, nullable=True)      # スタートタイミング
    rank = Column(Integer, nullable=True) # 着順

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./boatrace_data.db")
# Render uses postgres:// but SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
