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

class Entry(Base):
    __tablename__ = "entries"
    id = Column(String, primary_key=True) # e.g. "20240325_03_12_1"
    race_id = Column(String, index=True)
    waku = Column(Integer)
    name = Column(String)
    rate_global = Column(Float)
    st_average = Column(Float)
    racer_comment = Column(String, nullable=True)

class Exhibition(Base):
    __tablename__ = "exhibitions"
    id = Column(String, primary_key=True)
    race_id = Column(String, index=True)
    waku = Column(Integer)
    exhibition_time = Column(Float, nullable=True)
    lap_time = Column(Float, nullable=True)
    turn_time = Column(Float, nullable=True)
    straight_time = Column(Float, nullable=True)

engine = create_engine("sqlite:///./boatrace_data.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
