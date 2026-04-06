import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Flag, Timer, TrendingUp, Clock, RotateCw, Share } from 'lucide-react';

// ----------------------------------------------------------------------------
// Cockpit [FINAL] Edition - Absolute Synchronization
// ----------------------------------------------------------------------------

export default function App() {
  const [schedule, setSchedule] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isFetched, setIsFetched] = useState(false);
  const [racers, setRacers] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  
  const [date, setDate] = useState('20260407');
  const [jcd, setJcd] = useState('02'); 
  const [rno, setRno] = useState('1'); 
  const [seriesDay, setSeriesDay] = useState<number>(1);

  const API_BASE = ''; // 鋼鉄の相対パス： 1 mm の不備も許さない 100% の自律性

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
    setLoading(true);
    setIsFetched(false);
    try {
      const res = await fetch(`${API_BASE}/api/prediction/${date}/${activeJcd}/${activeRno}`);
      if (!res.ok) throw new Error('API Error');
      const data = await res.json();
      setRacers(data.racers || []);
      setPredictions(data.predictions || []);
      setIsFetched(true);
    } catch (err) {
      setError('データの取得に失敗しました。');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSchedule(); }, [date]);

  return (
    <div className="app-container">
      <header className="glass-header">
        <div className="logo">
          <h1>BoatRace <span>Cockpit [FINAL]</span></h1>
        </div>
      </header>

      <div className="schedule-bar" style={{ padding: '10px', background: 'rgba(0,0,0,0.3)', display: 'flex', gap: '5px', overflowX: 'auto' }}>
        {schedule.map(v => (
          <button key={v.jcd} className={`venue-chip ${v.jcd === jcd ? 'is-active' : ''}`} onClick={() => { setJcd(v.jcd); fetchData(v.jcd, rno, v.series_day_num); }}>
            {v.name}
          </button>
        ))}
      </div>

      <div className="race-selector-12" style={{ padding: '10px', display: 'flex', gap: '5px' }}>
        {[1,2,3,4,5,6,7,8,9,10,11,12].map(n => (
          <button key={n} className={`race-btn ${rno === String(n) ? 'is-active' : ''}`} onClick={() => { setRno(String(n)); fetchData(jcd, String(n), seriesDay); }}>
            {n}R
          </button>
        ))}
      </div>

      {!isFetched && !loading ? (
        <div className="welcome">会場とレースを選択してください。</div>
      ) : (
        <main className="dashboard">
          <h2><Trophy /> 解析結果: {jcd} - {rno}R</h2>
          {racers.map(r => (
            <div key={r.waku} className="racer-row" style={{ display: 'flex', gap: '20px', padding: '10px', borderBottom: '1px solid #333' }}>
              <div className={`w-badge w-${r.waku}`} style={{ width: 30, height: 30, textAlign: 'center', background: '#444' }}>{r.waku}</div>
              <div>{r.name}</div>
              <div>展示: {r.exhibition_time}</div>
            </div>
          ))}
        </main>
      )}
    </div>
  );
}
// FORCE_DEPLOY_SCRAPING_V1_MANIFEST_202604070133
