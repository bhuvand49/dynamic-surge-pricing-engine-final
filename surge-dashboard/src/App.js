import React, { useEffect, useMemo, useState, useCallback } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar
} from "recharts";
import {
  Users,
  Activity,
  Zap,
  MapPinned,
  CloudRain,
  PartyPopper,
  Bell
} from "lucide-react";
import "./App.css";

const API =
  process.env.REACT_APP_API_URL ||
  "https://dynamic-surge-pricing-engine-backend.onrender.com";

const MAP_URL = `/map.html?embed=1&api=${encodeURIComponent(API)}`;

const AREA_NAMES = [
  "Indiranagar",
  "Koramangala",
  "Whitefield",
  "Hebbal",
  "Yelahanka",
  "Electronic City",
  "Jayanagar",
  "MG Road",
  "Rajajinagar",
  "Marathahalli",
  "HSR Layout",
  "Banashankari"
];

function mapHexToArea(hexId = "") {
  let total = 0;
  for (let i = 0; i < hexId.length; i++) {
    total += hexId.charCodeAt(i);
  }
  return AREA_NAMES[total % AREA_NAMES.length];
}

export default function App() {
  const [regions, setRegions] = useState([]);
  const [scenario, setScenario] = useState({ rain: 0, event: 0 });
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [now, setNow] = useState(new Date());

  const [stats, setStats] = useState({
    drivers: 0,
    riders: 0,
    high: 0,
    avg: 1
  });

  const buildAlerts = useCallback((data, sc, high) => {
    const top = [...data].sort(
      (a, b) => Number(b.surge_multiplier) - Number(a.surge_multiplier)
    )[0];

    setAlerts([
      {
        type: "danger",
        text: `Highest surge: ${top?.area || "N/A"} (${top?.surge_multiplier || 1}x)`
      },
      {
        type: "info",
        text: `${high} high-demand zones active`
      },
      {
        type: sc.rain ? "warning" : "success",
        text: sc.rain ? "Rain mode enabled" : "Weather stable"
      },
      {
        type: sc.event ? "warning" : "success",
        text: sc.event ? "Event spike active" : "No event hotspots"
      }
    ]);
  }, []);

  const loadAll = useCallback(async () => {
    try {
      const [res1, res2, res3, res4] = await Promise.all([
        fetch(`${API}/surge/all`),
        fetch(`${API}/scenario`),
        fetch(`${API}/drivers`),
        fetch(`${API}/riders`)
      ]);

      const data = await res1.json();
      const sc = await res2.json();
      const driverData = await res3.json();
      const riderData = await res4.json();

      const safe = Array.isArray(data) ? data : [];

      setRegions(safe);
      setScenario(sc);

      const drivers = Array.isArray(driverData) ? driverData.length : 0;
      const riders = Array.isArray(riderData) ? riderData.length : 0;

      let high = 0;
      let total = 0;

      safe.forEach((r) => {
        const s = Number(r.surge_multiplier || 1);
        total += s;
        if (s >= 2) high++;
      });

      const avg = safe.length ? total / safe.length : 1;

      setStats({
        drivers,
        riders,
        high,
        avg: avg.toFixed(2)
      });

      setHistory((prev) => [
        ...prev.slice(-11),
        {
          time: new Date().toLocaleTimeString(),
          surge: +avg.toFixed(2)
        }
      ]);

      buildAlerts(safe, sc, high);
    } catch (e) {
      console.log("Load error:", e);
    }
  }, [buildAlerts]);

  useEffect(() => {
    loadAll();

    const t1 = setInterval(loadAll, 8000);
    const t2 = setInterval(() => setNow(new Date()), 1000);

    return () => {
      clearInterval(t1);
      clearInterval(t2);
    };
  }, [loadAll]);

  async function updateScenario(key, value) {
    try {
      const body = {
        ...scenario,
        [key]: value
      };

      await fetch(`${API}/scenario`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(body)
      });

      setScenario(body);
      setTimeout(loadAll, 500);
    } catch (e) {
      console.log("Scenario error:", e);
    }
  }

  const topRegions = useMemo(() => {
    return [...regions]
      .sort(
        (a, b) => Number(b.surge_multiplier) - Number(a.surge_multiplier)
      )
      .slice(0, 6);
  }, [regions]);

  const groupedAreas = useMemo(() => {
    const grouped = {};

    regions.forEach((r) => {
      const areaName = mapHexToArea(r.area);

      if (!grouped[areaName]) {
        grouped[areaName] = {
          area: areaName,
          drivers: 0,
          riders: 0,
          surgeTotal: 0,
          count: 0,
          maxSurge: 1
        };
      }

      const surge = Number(r.surge_multiplier || 1);

      grouped[areaName].drivers += Number(r.drivers || 0);
      grouped[areaName].riders += Number(r.riders || 0);
      grouped[areaName].surgeTotal += surge;
      grouped[areaName].count += 1;
      grouped[areaName].maxSurge = Math.max(grouped[areaName].maxSurge, surge);
    });

    return Object.values(grouped)
      .map((g) => ({
        ...g,
        surge_multiplier: (g.surgeTotal / g.count).toFixed(2)
      }))
      .sort((a, b) => Number(b.maxSurge) - Number(a.maxSurge));
  }, [regions]);

  return (
    <div className="app-shell">
      <header className="topbar glass">
        <div>
          <div className="brand">🚀 Dynamic Surge Intelligence</div>
          <div className="sub">Real-time Pricing Control Center</div>
        </div>

        <div className="top-right">
          <span className="live-dot"></span>
          <span>ONLINE</span>
          <span className="clock">{now.toLocaleTimeString()}</span>
        </div>
      </header>

      <section className="kpi-grid">
        <KPI icon={<Users size={18} />} title="Drivers" value={stats.drivers} />
        <KPI icon={<Activity size={18} />} title="Riders" value={stats.riders} />
        <KPI icon={<Zap size={18} />} title="High Surge" value={stats.high} />
        <KPI icon={<MapPinned size={18} />} title="Avg Surge" value={`${stats.avg}x`} />
      </section>

      <section className="main-grid">
        <div className="left-col">
          <div className="glass panel">
            <div className="panel-title">🗺 Live Map</div>
            <iframe title="map" src={MAP_URL} className="map-frame" />
          </div>

          <div className="glass panel">
            <div className="panel-title">📈 Surge Trend</div>

            <div className="chart-wrap">
              {history.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={history}>
                    <CartesianGrid stroke="#334155" strokeDasharray="4 4" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[1, 4]} />
                    <Tooltip />
                    <Area
                      dataKey="surge"
                      stroke="#00ffd0"
                      fill="#00ffd033"
                      strokeWidth={3}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">Loading...</div>
              )}
            </div>
          </div>
        </div>

        <div className="right-col">
          <div className="glass panel">
            <div className="panel-title">⚙ Controls</div>

            <div className="control-row">
              <button
                className={scenario.rain ? "btn active" : "btn"}
                onClick={() => updateScenario("rain", scenario.rain ? 0 : 1)}
              >
                <CloudRain size={16} />
                Rain {scenario.rain ? "ON" : "OFF"}
              </button>

              <button
                className={scenario.event ? "btn pink active" : "btn pink"}
                onClick={() => updateScenario("event", scenario.event ? 0 : 1)}
              >
                <PartyPopper size={16} />
                Event {scenario.event ? "ON" : "OFF"}
              </button>
            </div>
          </div>

          <div className="glass panel">
            <div className="panel-title">🔔 AI Insights</div>

            <div className="alerts-wrap">
              {alerts.map((a, i) => (
                <div key={i} className={`alert-box ${a.type}`}>
                  <Bell size={14} />
                  {a.text}
                </div>
              ))}
            </div>
          </div>

          <div className="glass panel">
            <div className="panel-title">🏆 Top Zones</div>

            <div className="chart-wrap tall">
              {topRegions.length ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topRegions} layout="vertical" margin={{ left: 30 }}>
                    <CartesianGrid stroke="#334155" strokeDasharray="4 4" />
                    <XAxis type="number" domain={[0, 4]} />
                    <YAxis type="category" dataKey="area" width={100} />
                    <Tooltip />
                    <Bar
                      dataKey="surge_multiplier"
                      fill="#7c3aed"
                      radius={[0, 8, 8, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="empty-state">Loading...</div>
              )}
            </div>
          </div>
        </div>
      </section>

      <section>
        <div className="section-head">📍 Area Surge Pricing</div>

        <div className="zones-grid">
          {groupedAreas.map((r, i) => {
            const high = Number(r.maxSurge) >= 2;

            return (
              <div
                key={i}
                className={`zone-card glass ${high ? "danger" : ""}`}
              >
                <div className="zone-top">
                  <span>{r.area}</span>
                  <span className="badge">{r.surge_multiplier}x</span>
                </div>

                <div className="zone-stats">
                  <div>Drivers: {r.drivers}</div>
                  <div>Riders: {r.riders}</div>
                </div>

                <div className="mini">
                  <span>Peak {r.maxSurge}x</span>
                  <span>{r.count} zones</span>
                </div>

                {high && <div className="alert">HIGH DEMAND 🔥</div>}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

function KPI({ title, value, icon }) {
  return (
    <div className="glass kpi">
      <div className="kpi-top">
        {icon}
        <span>{title}</span>
      </div>
      <div className="kpi-value">{value}</div>
    </div>
  );
}