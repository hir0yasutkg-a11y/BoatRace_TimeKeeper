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
  { label: '\u672C\u65E5 (4/7)', value: '20260407' },
  { label: '\u6628\u65E5 (4/6)', value: '20260406' },
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

  const scores = racers.map(r => ({ waku: r.waku, total: getScore(r) }));
  const maxScore = Math.max(...scores.map(s => s.total));

  return (
    <section className="glass-card total-vis-card">
      <h3><Trophy size={20} /> \u7DCF\u5408\u8A55\u4FA1\u30B7\u30DF\u30E5\u30EC\u30FC\u30BF</h3>
      <div className="total-vis-container">
        {scores.map(s => (
          <div key={s.waku} className="total-vis-column">
            <div className="total-bar-wrapper">
              <motion.div
                className={`total-bar w-${s.waku}-bg`}
                initial={{ height: 0 }}
                animate={{ height: `${(s.total / maxScore) * 100}%` }}
              />
            </div>
            <div className={`w-badge w-${s.waku}`}>{s.waku}</div>
          </div>
        ))}
      </div>
    </section>
  );
};

// Main App
export default function App() {
  const [schedule, setSchedule] = useState<VenueSchedule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFetched, setIsFetched] = useState(false);

  const [racers, setRacers] = useState<Racer[]>([]);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [roughAlerts, setRoughAlerts] = useState<{type:string, message:string}[]>([]);
  const [sourceUrls, setSourceUrls] = useState({ list: '', before: '' });
  const [isMock, setIsMock] = useState(false);

  const [showPwaPrompt, setShowPwaPrompt] = useState(false);
  const [date, setDate] = useState(AVAILABLE_DATES[0].value);
  const [jcd, setJcd] = useState('02');
  const [rno, setRno] = useState('1');
  const [seriesDay, setSeriesDay] = useState<number>(1);

  useEffect(() => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
    if (isIOS && !isStandalone) setShowPwaPrompt(true);
  }, []);

  const API_BASE = '';

  const fetchSchedule = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/schedule/${date}`);
      if (res.ok) {
        const data = await res.json();
        setSchedule(data);
      }
    } catch (e) { console.error("Schedule fetch failed"); }
  };

  const fetchData = async (targetJcd?: string, targetRno?: string, targetDay?: number) => {
    const activeJcd = targetJcd || jcd;
    const activeRno = targetRno || rno;
    const activeDayNum = targetDay || seriesDay;

    let targetDate = date;
    const vInfo = schedule.find(v => v.jcd === activeJcd);
    if (vInfo && vInfo.series_day_num) {
      const diff = vInfo.series_day_num - activeDayNum;
      const d = new Date(date.slice(0,4)+"-"+date.slice(4,6)+"-"+date.slice(6,8));
      d.setDate(d.getDate() - diff);
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth() + 1).padStart(2, '0');
      const dd = String(d.getDate()).padStart(2, '0');
      targetDate = `${yyyy}${mm}${dd}`;
    }

    if (!activeJcd) return;
    setLoading(true);
    setError('');
    setIsFetched(false);
    try {
      const fetchUrl = `${API_BASE}/api/prediction/${targetDate}/${activeJcd}/${activeRno}?t=${Date.now()}`;
      const res = await fetch(fetchUrl);
      if (!res.ok) throw new Error(`API Error: ${res.status}`);
      const data = await res.json();
      if (data.error) {
        setError(data.error);
        return;
      }
      const activeRacers = (data.racers || []).filter((r: any) =>
        r.name !== "Unknown" && !r.name.includes("\u6B20\u5834")
      );
      setRacers(activeRacers);
      setPredictions(data.predictions || []);
      setIsMock(!!data.is_mock);
      setSourceUrls({ list: data.racelist_url, before: data.beforeinfo_url });
      setRoughAlerts(data.rough_alerts || []);
      setIsFetched(true);
    } catch (err) {
      setError('\u30C7\u30FC\u30BF\u306E\u53D6\u5F97\u306B\u5931\u6557\u3057\u307E\u3057\u305F');
    } finally {
      setTimeout(() => setLoading(false), 600);
    }
  };

  useEffect(() => {
    fetchSchedule();
    setIsFetched(false);
  }, [date]);

  useEffect(() => {
    setIsFetched(false);
  }, [jcd, rno]);

  const minExh = racers.length ? Math.min(...racers.map(r => r.exhibition_time)) : 6.6;
  const sortedPredictions = [...predictions].sort((a,b) => b.score - a.score);

  return (
    <div className="app-container">
      {loading && (
        <div className="loading-overlay">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="loading-spinner"
          />
          <p>\u30C7\u30FC\u30BF\u3092\u53D6\u5F97\u4E2D...</p>
        </div>
      )}

      {error && (
        <div className="error-banner">
          <Flag size={20} />
          {error}
          <button onClick={() => fetchData()}>\u518D\u8A66\u884C</button>
        </div>
      )}

      {isMock && (
        <div className="mock-badge">
          \u6CE8\u610F: \u73FE\u5728\u306F\u30E2\u30C3\u30AF\u30C7\u30FC\u30BF\u3092\u8868\u793A\u3057\u3066\u3044\u307E\u3059
        </div>
      )}

      {showPwaPrompt && (
        <div className="pwa-prompt">
          <div className="pwa-content">
            <Share size={20} />
            <span>\u30DB\u30FC\u30E0\u753B\u9762\u306B\u8FFD\u52A0\u3057\u3066\u30A2\u30D7\u30EA\u3068\u3057\u3066\u5229\u7528\u3067\u304D\u307E\u3059\uFF08\u5171\u6709 &gt; \u30DB\u30FC\u30E0\u753B\u9762\u306B\u8FFD\u52A0\uFF09</span>
            <button onClick={() => setShowPwaPrompt(false)}>\u9589\u3058\u308B</button>
          </div>
        </div>
      )}

      {/* Schedule Bar */}
      <div className="schedule-bar">
        <div className="bar-label">
          <Clock size={14} /> \u672C\u65E5\u306E\u958B\u50AC
          <button className="btn-refresh-schedule" onClick={() => fetchSchedule()} title="\u958B\u50AC\u60C5\u5831\u3092\u66F4\u65B0">
            <RotateCw size={12} />
          </button>
        </div>
        <div className="venue-list">
          {schedule.length > 0 ? schedule.map(v => (
            <div
              key={v.jcd}
              className={`venue-chip ${v.jcd === jcd ? 'is-active' : ''} ${v.status === '\u7D42\u4E86' || v.status === 'Cancelled' ? 'is-finished' : ''} grade-${v.grade || 'General'}`}
              onClick={() => {
                if (v.status === 'Cancelled') return;
                setJcd(v.jcd);
                const nextR = v.next_race ? String(v.next_race) : "1";
                setRno(nextR);
                const currentDayNum = v.series_day_num || 1;
                setSeriesDay(currentDayNum);
                fetchData(v.jcd, nextR, currentDayNum);
              }}
              style={{ position: 'relative' }}
            >
              {v.has_exh_data && (
                <span className="live-indicator-dot" title="\u5C55\u793A\u30C7\u30FC\u30BF\u53D7\u4FE1\u4E2D" />
              )}
              <span className="v-name">
                {v.grade && v.grade !== 'General' && (
                  <span className={`grade-badge ${v.grade.toLowerCase()}`}>{v.grade}</span>
                )}
                {v.name}
              </span>
              {v.status === 'canceled' ? (
                <span className="v-finished">\u4E2D\u6B62\u4E8B\u614B</span>
              ) : v.status === '\u7D42\u4E86' ? (
                <span className="v-finished">\u7D42\u4E86</span>
              ) : (
                <span className="v-deadline">
                  {v.next_race}R <span className="v-time">{v.deadline}</span>
                </span>
              )}
            </div>
          )) : (
            <span style={{fontSize: '0.8rem', color: '#00f2ff', opacity: 0.9, paddingLeft: '10px'}}>
              \u958B\u50AC\u60C5\u5831\u3092\u30B9\u30AD\u30E3\u30F3\u4E2D...
            </span>
          )}
        </div>
      </div>

      {/* Header */}
      <header className="glass-header">
        <div className="logo">
          <div className="icon">{'\u{1F3C1}'}</div>
          <h1>BoatRace <span>Cockpit</span></h1>
        </div>

        {isFetched && racers.length > 0 && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="series-info-hud">
            <div className="series-hud-label">CURRENT_SERIES_DATA</div>
            <div className="series-hud-content">
              <span className="series-name">{schedule.find(v => v.jcd === jcd)?.series_name || '\u4E00\u822C\u6226'}</span>
              <span className="series-day-badge">{schedule.find(v => v.jcd === jcd)?.series_day || '\u958B\u50AC\u4E2D'}</span>
            </div>
          </motion.div>
        )}

        <div className="race-selector">
          <div className="selector-item">
            <label>\u65E5\u4ED8</label>
            <select value={date} onChange={e => setDate(e.target.value)}>
              {AVAILABLE_DATES.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
        </div>
      </header>

      {/* Control Panel: Series Day + 12 Race Buttons */}
      <div className="control-bar-container">
        <div className="control-divider"></div>
        <div className="control-panels">
          <div className="series-day-panel">
            <span className="panel-label">\u7BC0\u9593</span>
            <div className="series-day-list">
              {Array.from({ length: (schedule.find(v => v.jcd === jcd)?.series_day_num || 1) }, (_, i) => i + 1).map(d => (
                <button key={d} className={`day-btn ${seriesDay === d ? 'is-active' : ''}`} onClick={() => { setSeriesDay(d); fetchData(jcd, rno, d); }}>
                  {d === (schedule.find(v => v.jcd === jcd)?.series_day_num) ? '\u4ECA\u65E5' : `${d}\u65E5\u76EE`}
                </button>
              ))}
            </div>
          </div>

          <div className="vertical-divider"></div>

          <div className="race-number-panel">
            <span className="panel-label">\u30EC\u30FC\u30B9\u756A\u53F7</span>
            <div className="race-number-list">
              {[1,2,3,4,5,6,7,8,9,10,11,12].map(n => {
                const nextR = parseInt(String(schedule.find(v => v.jcd === jcd)?.next_race || "13"));
                const isFinished = n < nextR && seriesDay === (schedule.find(v => v.jcd === jcd)?.series_day_num);
                return (
                  <button key={n} className={`race-btn ${rno === String(n) ? 'is-active' : ''} ${isFinished ? 'is-finished' : ''}`} onClick={() => { setRno(String(n)); fetchData(jcd, String(n), seriesDay); }}>
                    {n}<span className="unit">R</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      {!isFetched && !loading ? (
        <div className="welcome-card">
          <div className="welcome-icon">{'\u{1F680}'}</div>
          <h2>\u4F1A\u5834\u3068\u30EC\u30FC\u30B9\u756A\u53F7\u3092\u9078\u629E\u3057\u3066\u3001\u4E88\u60F3\u3092\u958B\u59CB\u3057\u3066\u304F\u3060\u3055\u3044</h2>
          <p>\u6700\u65B0\u306E\u51FA\u8D70\u8868\u3001\u5C55\u793A\u30BF\u30A4\u30E0\u3001\u9078\u624B\u30B3\u30E1\u30F3\u30C8\u3092\u30EA\u30A2\u30EB\u30BF\u30A4\u30E0\u306B\u89E3\u6790\u3057\u307E\u3059</p>
        </div>
      ) : (
        <main className="dashboard-layout">
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
              <h3><Flag size={20} /> \u51FA\u8D70\u8868 & \u5C55\u793A\u60C5\u5831</h3>
              <div className="table-wrapper">
                <div className="cards-header">
                  <div>\u67A0</div><div>\u9078\u624B\u540D</div><div>\u52DD\u7387</div><div>\u5E73\u5747ST</div><div>\u5C55\u793A</div><div>1\u5468</div><div>\u307E\u308F\u308A</div><div>\u76F4\u7DDA</div>
                </div>
                <div className="racer-cards-container">
                  {racers.map((r) => (
                    <div key={r.waku} className="racer-card">
                      <div className="col-waku"><div className={`w-badge w-${r.waku}`}>{r.waku}</div></div>
                      <div className="col-name">
                        <div className="racer-meta">{r.waku}\u53F7\u8247 {r.rank && <span className={`rank-badge rank-${r.rank.charAt(0)}`}>{r.rank}</span>}</div>
                        <div className="racer-full-name">{r.name}</div>
                        {r.series_results && r.series_results.length > 0 && (
                          <div className="series-history-bar">
                            {r.series_results.map((sr, idx) => (
                              <div key={idx} className={`sr-chip rank-${sr.rank}`} title={`${sr.date} ${sr.rno}R: ${sr.rank}\u7740`}>{sr.rank}</div>
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
              <h3><TrendingUp size={20} /> \u9078\u624B\u30B3\u30E1\u30F3\u30C8</h3>
              <div className="comment-list">
                {racers.map(r => (
                  <div key={r.waku} className="comment-row">
                    <div className={`w-badge w-${r.waku}`}>{r.waku}</div>
                    <div className="comment-text">
                      {r.comment ? r.comment.split('\u524D\u65E5').map((part, i) => {
                        const cleanText = part.replace('\u5F53\u65E5', '').replace(':', '').replace('\uFF1A', '').trim();
                        if (!cleanText && i === 1) return null;
                        return <div key={i} className={i === 0 ? 'c-today' : 'c-yesterday'}><span className="c-label">{i === 0 ? '\u5F53\u65E5:' : '\u524D\u65E5:'}</span>{cleanText}</div>;
                      }) : <span className="no-comment">(\u30B3\u30E1\u30F3\u30C8\u306A\u3057)</span>}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
          <div className="simulators-row">
            <TimeVisualizer title="\u5C55\u793A\u30BF\u30A4\u30E0" icon={<Timer size={18} />} timeKey="exhibition_time" racers={racers} />
            <TimeVisualizer title="\u307E\u308F\u308A\u8DB3" icon={<TrendingUp size={18} />} timeKey="turn_time" racers={racers} />
            <TimeVisualizer title="\u76F4\u7DDA\u30BF\u30A4\u30E0" icon={<TrendingUp size={18} />} timeKey="straight_time" racers={racers} />
          </div>
          <div className="total-row"><TotalVisualizer racers={racers} /></div>
          <div className="predictions-row">
            <section className="glass-card predictions-section">
              <h2><Trophy size={24} /> AI \u4E88\u60F3\u7D50\u679C</h2>
              <div className="podium-box">
                {[1, 0, 2].map((idx) => {
                  const p = sortedPredictions[idx];
                  if (!p) return <div key={idx} className="podium-rank"></div>;
                  return (
                    <div key={p.waku} className={`podium-rank p-${idx === 0 ? '1st' : idx === 1 ? '2nd' : '3rd'}`}>
                      <div className={`w-badge w-${p.waku}`}>{p.waku}</div>
                      <div className="podium-base">{idx === 0 ? '1\u7740' : idx === 1 ? '2\u7740' : '3\u7740'}</div>
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
