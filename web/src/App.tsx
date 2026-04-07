import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Flag, Timer, TrendingUp, Clock, RotateCw, Share } from 'lucide-react';
import './App.css';

// Types
interface Racer {
  waku: number;
  name: string;
  rank: string;
  rate_global: number;
  st_average: number;
  exhibition_time: number;
  lap_time: number;
  turn_time: number;
  straight_time: number;
  comment?: string;
  series_results?: Array<{
    date: string;
    rno: string;
    rank: string;
    course: string;
    st: string;
  }>;
}

interface Prediction {
  waku: number;
  score: number;
}

interface VenueSchedule {
  jcd: string;
  name: string;
  status: string;
  next_race: string | number;
  deadline: string;
  grade?: string;
  event?: string;
  has_exh_data: boolean;
  series_name?: string;
  series_day?: string;
  series_day_num?: number;
}

const AVAILABLE_DATES = [
  { label: '本日 (4/7)', value: '20260407' },
  { label: '昨日 (4/6)', value: '20260406' },
  { label: '4/5', value: '20260405' },
];

// Sub-components
const TimeVisualizer = ({ title, racers, timeKey, icon }: {
  title: string;
  racers: Racer[];
  timeKey: keyof Racer;
  icon: React.ReactNode;
}) => {
  const times = racers.map(r => r[timeKey] as number).filter(t => t > 0);
  const min = Math.min(...times);
  const max = Math.max(...times);

  return (
    <section className="glass-card visualizer-card">
      <h3>{icon} {title}</h3>
      <div className="vis-container">
        {racers.map(r => {
          const val = r[timeKey] as number;
          if (!val) return null;
          const diff = val - min;
          const normalized = (max - min) > 0 ? (diff / (max - min)) : 0;
          return (
            <div key={r.waku} className="vis-row">
              <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
              <div className="vis-track">
                <motion.div
                  className="vis-ship"
                  initial={{ left: 0 }}
                  animate={{ left: `${normalized * 75}%` }}
                  transition={{ duration: 1, ease: "easeOut" }}
                >
                  <div className="ship-dot"></div>
                </motion.div>
              </div>
              <div className="vis-val">{val.toFixed(2)}</div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

const TotalVisualizer = ({ racers }: { racers: Racer[] }) => {
  const getScore = (r: Racer) => {
    let s = (7 - r.exhibition_time) * 10;
    if (r.lap_time) s += (40 - r.lap_time) * 5;
    if (r.turn_time) s += (20 - r.turn_time) * 15;
    return s;
  };

  const scores = racers.map((r, i) => ({ waku: i + 1, score: getScore(r) }));
  const maxScore = Math.max(...scores.map(s => s.score));

  return (
    <section className="glass-card total-vis-card">
      <h3>機力トータル評価</h3>
      <div className="bar-grid">
        {scores.map(s => (
          <div key={s.waku} className="bar-row">
            <span className={`w-badge w-${s.waku}`}>{s.waku}</span>
            <div className="bar-bg">
              <motion.div
                className="bar-fill"
                initial={{ width: 0 }}
                animate={{ width: `${(s.score / maxScore) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

export default function App() {
  const [date, setDate] = useState('20260407');
  const [jcd, setJcd] = useState('02'); // 戸田
  const [rno, setRno] = useState(1);
  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [schedule, setSchedule] = useState<VenueSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [roughAlerts, setRoughAlerts] = useState<any[]>([]);
  const [seriesInfo, setSeriesInfo] = useState({ name: '', day: '' });

  useEffect(() => {
    fetchSchedule(date);
  }, [date]);

  useEffect(() => {
    fetchData();
  }, [date, jcd, rno]);

  const fetchSchedule = async (targetDate: string) => {
    try {
      const res = await fetch(`/api/schedule/${targetDate}`);
      const data = await res.json();
      setSchedule(data);
    } catch (e) {
      console.error("Schedule fetch error:", e);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/prediction/${date}/${jcd}/${rno}`);
      const data = await res.json();
      setRacers(data.racers || []);
      setPredictions(data.predictions || []);
      setRoughAlerts(data.rough_alerts || []);
      
      const venue = schedule.find(v => v.jcd === jcd);
      if (venue) {
        setSeriesInfo({ name: venue.series_name || '', day: venue.series_day || '' });
      }
    } catch (e) {
      console.error("Data fetch error:", e);
      setRacers([]);
    } finally {
      setLoading(false);
    }
  };

  const sortedPredictions = [...predictions].sort((a, b) => b.score - a.score);
  const minExh = racers.length > 0 ? Math.min(...racers.map(r => r.exhibition_time).filter(t => t > 0)) : 0;

  return (
    <div className="dashboard-container">
      <header className="main-header">
        <div className="header-left">
          <div className="logo-section">
            <div className="logo-icon"><RotateCw className="spin" /></div>
            <h1>BoatRace <span>Cockpit</span></h1>
          </div>
          <div className="live-ticker">
            <div className="ticker-item"><Clock size={14} /> <span>本日(今日)の開催一覧</span></div>
            <div className="ticker-track">
              {schedule.map(v => (
                <span key={v.jcd} className={`ticker-venue ${v.has_exh_data ? 'active' : ''}`} onClick={() => setJcd(v.jcd)}>
                  {v.name} {v.next_race && <span>{v.next_race}R</span>}
                </span>
              ))}
            </div>
          </div>
        </div>
        <div className="header-right">
          <div className="date-selector">
            {AVAILABLE_DATES.map(d => (
              <button key={d.value} className={date === d.value ? 'active' : ''} onClick={() => setDate(d.value)}>
                {d.label}
              </button>
            ))}
          </div>
          <button className="icon-btn highlight"><Share size={18} /></button>
        </div>
      </header>

      <nav className="control-bar">
        <div className="venue-grid">
          {schedule.map(v => (
            <button key={v.jcd} className={`venue-btn ${jcd === v.jcd ? 'selected' : ''}`} onClick={() => setJcd(v.jcd)}>
              <span className="v-name">{v.name}</span>
              <span className="v-meta">{v.next_race ? `${v.next_race}R` : '終了'}</span>
            </button>
          ))}
        </div>
        <div className="race-selector">
          {[1,2,3,4,5,6,7,8,9,10,11,12].map(num => (
            <button key={num} className={`race-btn ${rno === num ? 'current' : ''}`} onClick={() => setRno(num)}>
              <span className="r-num">{num}</span>
              <span className="r-label">R</span>
            </button>
          ))}
        </div>
      </nav>

      {loading ? (
        <div className="loading-state">
          <div className="scanner"></div>
          <p>データを索敵中...</p>
        </div>
      ) : (
        <main className="dashboard-layout">
          <div className="series-banner-mini">
            <div className="banner-label">CURRENT_SERIES_DATA</div>
            <div className="banner-content">{seriesInfo.name || '一般戦'} 開催中</div>
            <div className="banner-day">{seriesInfo.day || '本日'}</div>
          </div>

          {roughAlerts && roughAlerts.length > 0 && (
            <div className="alerts-container">
              {roughAlerts.map((alert, idx) => (
                <motion.div key={idx} className={`alert-card ${alert.type}`} initial={{ scale: 0.95, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                  {alert.message}
                </motion.div>
              ))}
            </div>
          )}
          
          <div className="info-row">
            <section className="glass-card racer-info-section">
              <h3><Flag size={20} /> 出走表 & 展示情報</h3>
              <div className="table-wrapper">
                <div className="cards-header">
                  <div>枠</div><div>選手名</div><div>勝率</div><div>平均ST</div><div>展示</div><div>1周</div><div>まわり</div><div>直線</div>
                </div>
                <div className="racer-cards-container">
                  {racers.map((r) => (
                    <div key={r.waku} className="racer-card">
                      <div className="col-waku"><div className={`w-badge w-${r.waku}`}>{r.waku}</div></div>
                      <div className="col-name">
                        <div className="racer-meta">{r.waku}号艇 {r.rank && <span className={`rank-badge rank-${r.rank.charAt(0)}`}>{r.rank}</span>}</div>
                        <div className="racer-full-name">{r.name}</div>
                        {r.series_results && r.series_results.length > 0 && (
                          <div className="series-history-bar">
                            {r.series_results.map((sr, idx) => (
                              <div key={idx} className={`sr-chip rank-${sr.rank}`} title={`${sr.date} ${sr.rno}R: ${sr.rank}着`}>{sr.rank}</div>
                            ))}
                          </div>
                        )}
                      </div>
                      <div className="col-stat">{r.rate_global.toFixed(2)}</div>
                      <div className="col-stat">{r.st_average.toFixed(2)}</div>
                      <div className="col-stat" style={{ color: r.exhibition_time === minExh ? '#ff4500' : 'inherit', fontWeight: '900' }}>{r.exhibition_time.toFixed(2)}</div>
                      <div className="col-stat text-lap">{r.lap_time ? r.lap_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-maw">{r.turn_time ? r.turn_time.toFixed(2) : '-'}</div>
                      <div className="col-stat text-str">{r.straight_time ? r.straight_time.toFixed(2) : '-'}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
            <section className="glass-card comment-section">
              <h3><TrendingUp size={20} /> 選手コメント</h3>
              <div className="comment-list">
                {racers.map(r => (
                  <div key={r.waku} className="comment-row">
                    <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                    <div className="comment-text">
                      {r.comment ? r.comment.split('前日').map((part, i) => {
                        const cleanText = part.replace('当日', '').replace(':', '').replace('：', '').trim();
                        if (!cleanText && i === 1) return null;
                        return <div key={i} className={i === 0 ? 'c-today' : 'c-yesterday'}><span className="c-label">{i === 0 ? '当日:' : '前日:'}</span>{cleanText}</div>;
                      }) : <span className="no-comment">(コメントなし)</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <div className="simulators-row">
            <TimeVisualizer title="展示タイム" icon={<Timer size={18} />} timeKey="exhibition_time" racers={racers} />
            <TimeVisualizer title="まわり足" icon={<TrendingUp size={18} />} timeKey="turn_time" racers={racers} />
            <TimeVisualizer title="直線タイム" icon={<TrendingUp size={18} />} timeKey="straight_time" racers={racers} />
          </div>
          <div className="total-row"><TotalVisualizer racers={racers} /></div>
          <div className="predictions-row">
            <section className="glass-card predictions-section">
              <h2><Trophy size={24} /> AI 予想結果</h2>
              <div className="podium-box">
                {[1, 0, 2].map((idx) => {
                  const p = sortedPredictions[idx];
                  if (!p) return <div key={idx} className="podium-rank"></div>;
                  return (
                    <div key={p.waku} className={`podium-rank p-${idx === 0 ? '1st' : idx === 1 ? '2nd' : '3rd'}`}>
                      <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                      <div className="podium-base">{idx === 0 ? '1着' : idx === 1 ? '2着' : '3着'}</div>
                    </div>
                  );
                })}
              </div>
              <div className="score-bars">
                {sortedPredictions.map((p) => (
                  <div key={p.waku} className="score-row">
                    <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                    <div className="progress-container"><motion.div className="progress-fill" initial={{ width: 0 }} animate={{ width: `${(p.score / 120) * 100}%` }} /></div>
                    <div className="score-val">{p.score.toFixed(1)}</div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </main>
      )}
    </div>
  );
}
