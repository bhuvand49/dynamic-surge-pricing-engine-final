// src/App.js
import React, { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
} from "recharts";

import {
  Activity,
  MapPinned,
  Users,
  Zap,
  CloudRain,
  PartyPopper,
  Bell,
} from "lucide-react";

import "./App.css";

/* -------------------------
   CLOUD READY URLS
-------------------------- */
const API =
  process.env.REACT_APP_API_URL || "http://127.0.0.1:8000";

const MAP_URL =
  process.env.REACT_APP_MAP_URL || "/map.html";

export default function App() {
  const [regions, setRegions] = useState([]);
  const [scenario, setScenario] = useState({
    rain: 0,
    event: 0,
  });
  const [history, setHistory] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [now, setNow] = useState(new Date());

  const [stats, setStats] = useState({
    drivers: 0,
    riders: 0,
    high: 0,
    avg: 1,
  });

  /* -------------------------
     INITIAL LOAD
  -------------------------- */
  useEffect(() => {
    loadAll();

    const t1 = setInterval(loadAll, 4000);
    const t2 = setInterval(
      () => setNow(new Date()),
      1000
    );

    return () => {
      clearInterval(t1);
      clearInterval(t2);
    };
  }, []);

  /* -------------------------
     LOAD DATA
  -------------------------- */
  async function loadAll() {
    try {
      const [surgeRes, scenarioRes] =
        await Promise.all([
          fetch(`${API}/surge/all`),
          fetch(`${API}/scenario`),
        ]);

      const data = await surgeRes.json();
      const sc = await scenarioRes.json();

      setRegions(data);
      setScenario(sc);

      let drivers = 0;
      let riders = 0;
      let high = 0;
      let total = 0;

      data.forEach((r) => {
        const surge = Number(
          r.surge_multiplier || 1
        );

        drivers += Number(r.drivers || 0);
        riders += Number(r.riders || 0);
        total += surge;

        if (surge >= 2) high++;
      });

      const avg = data.length
        ? total / data.length
        : 1;

      setStats({
        drivers,
        riders,
        high,
        avg: avg.toFixed(2),
      });

      /* live chart effect */
      const liveAvg = Number(
        (
          avg +
          (Math.random() * 0.18 - 0.09) +
          (sc.rain ? 0.18 : 0) +
          (sc.event ? 0.22 : 0)
        ).toFixed(2)
      );

      setHistory((prev) => {
        const next = [
          ...prev,
          {
            time:
              new Date().toLocaleTimeString(),
            surge: Math.max(1, liveAvg),
          },
        ];

        return next.slice(-12);
      });

      buildAlerts(data, sc, high);
    } catch (err) {
      console.log("API Error:", err);
    }
  }

  /* -------------------------
     ALERTS
  -------------------------- */
  function buildAlerts(
    data,
    sc,
    highCount
  ) {
    const sorted = [...data].sort(
      (a, b) =>
        Number(b.surge_multiplier) -
        Number(a.surge_multiplier)
    );

    const top = sorted[0];

    setAlerts([
      {
        type: "danger",
        text: `Highest surge in ${
          top?.area || "N/A"
        } (${top?.surge_multiplier || 1}x)`,
      },
      {
        type: "info",
        text: `${highCount} high-demand zones active`,
      },
      {
        type: sc.rain
          ? "warning"
          : "success",
        text: sc.rain
          ? "Rain mode affecting supply"
          : "Weather conditions stable",
      },
      {
        type: sc.event
          ? "warning"
          : "success",
        text: sc.event
          ? "Event demand spikes detected"
          : "No event hotspots active",
      },
    ]);
  }

  /* -------------------------
     CONTROL CENTER
  -------------------------- */
  async function updateScenario(
    key,
    value
  ) {
    const body = {
      ...scenario,
      [key]: value,
    };

    await fetch(`${API}/scenario`, {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify(body),
    });

    setScenario(body);

    setTimeout(loadAll, 400);
  }

  /* -------------------------
     TOP REGIONS
  -------------------------- */
  const topRegions = useMemo(() => {
    return [...regions]
      .sort(
        (a, b) =>
          Number(b.surge_multiplier) -
          Number(a.surge_multiplier)
      )
      .slice(0, 6);
  }, [regions]);

  /* -------------------------
     UI
  -------------------------- */
  return (
    <div className="app-shell">
      {/* HEADER */}
      <header className="topbar glass">
        <div>
          <div className="brand">
            🚀 Dynamic Surge
            Intelligence
          </div>

          <div className="sub">
            Real-time Pricing
            Control Center
          </div>
        </div>

        <div className="top-right">
          <span className="live-dot"></span>
          <span>ONLINE</span>

          <span className="clock">
            {now.toLocaleTimeString()}
          </span>
        </div>
      </header>

      {/* KPI */}
      <section className="kpi-grid">
        <KPI
          icon={<Users size={18} />}
          title="Active Drivers"
          value={stats.drivers}
        />

        <KPI
          icon={<Activity size={18} />}
          title="Active Riders"
          value={stats.riders}
        />

        <KPI
          icon={<Zap size={18} />}
          title="High Surge Areas"
          value={stats.high}
        />

        <KPI
          icon={<MapPinned size={18} />}
          title="Average Surge"
          value={`${stats.avg}x`}
        />
      </section>

      {/* MAIN GRID */}
      <section className="main-grid">
        {/* LEFT */}
        <div className="left-col">
          {/* MAP */}
          <div className="glass panel">
            <div className="panel-title">
              🗺 Live Surge Map
            </div>

            <iframe
              title="map"
              src={MAP_URL}
              className="map-frame"
            />
          </div>

          {/* TREND */}
          <div className="glass panel">
            <div className="panel-title">
              📈 Surge Trend
            </div>

            <div className="chart-wrap">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <AreaChart data={history}>
                  <defs>
                    <linearGradient
                      id="fillSurge"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="#00ffd0"
                        stopOpacity={0.35}
                      />
                      <stop
                        offset="100%"
                        stopColor="#00ffd0"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>

                  <CartesianGrid
                    stroke="#334155"
                    strokeDasharray="4 4"
                  />

                  <XAxis dataKey="time" />

                  <YAxis
                    domain={[1, 4]}
                  />

                  <Tooltip />

                  <Area
                    type="monotone"
                    dataKey="surge"
                    stroke="#00ffd0"
                    fill="url(#fillSurge)"
                    strokeWidth={3}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* RIGHT */}
        <div className="right-col">
          {/* CONTROLS */}
          <div className="glass panel">
            <div className="panel-title">
              ⚙ Control Center
            </div>

            <div className="control-row">
              <button
                className={
                  scenario.rain
                    ? "btn active"
                    : "btn"
                }
                onClick={() =>
                  updateScenario(
                    "rain",
                    scenario.rain
                      ? 0
                      : 1
                  )
                }
              >
                <CloudRain size={16} />
                Rain{" "}
                {scenario.rain
                  ? "ON"
                  : "OFF"}
              </button>

              <button
                className={
                  scenario.event
                    ? "btn pink active"
                    : "btn pink"
                }
                onClick={() =>
                  updateScenario(
                    "event",
                    scenario.event
                      ? 0
                      : 1
                  )
                }
              >
                <PartyPopper size={16} />
                Event{" "}
                {scenario.event
                  ? "ON"
                  : "OFF"}
              </button>
            </div>

            <div className="mini-wrap">
              {scenario.rain && (
                <span className="mini-badge">
                  🌧 Rain Active
                </span>
              )}

              {scenario.event && (
                <span className="mini-badge pink-badge">
                  🎉 Event Active
                </span>
              )}
            </div>
          </div>

          {/* AI INSIGHTS */}
          <div className="glass panel">
            <div className="panel-title">
              🔔 AI Insights
            </div>

            <div className="alerts-wrap">
              {alerts.map((a, i) => (
                <div
                  key={i}
                  className={`alert-box ${a.type}`}
                >
                  <Bell size={14} />
                  <span>{a.text}</span>
                </div>
              ))}
            </div>
          </div>

          {/* TOP DEMAND */}
          <div className="glass panel">
            <div className="panel-title">
              🏆 Top Demand Areas
            </div>

            <div className="chart-wrap tall">
              <ResponsiveContainer
                width="100%"
                height="100%"
              >
                <BarChart
                  data={topRegions}
                  layout="vertical"
                  margin={{
                    top: 10,
                    right: 20,
                    left: 50,
                    bottom: 10,
                  }}
                >
                  <CartesianGrid
                    stroke="#334155"
                    strokeDasharray="4 4"
                  />

                  <XAxis
                    type="number"
                    domain={[0, 4]}
                  />

                  <YAxis
                    type="category"
                    dataKey="area"
                    width={120}
                  />

                  <Tooltip />

                  <Bar
                    dataKey="surge_multiplier"
                    fill="#7c3aed"
                    radius={[
                      0, 8, 8, 0,
                    ]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </section>

      {/* AREA CARDS */}
      <section className="zones-section">
        <div className="section-head">
          📍 Area Surge Pricing
        </div>

        <div className="zones-grid">
          {regions.map((r, i) => {
            const high =
              Number(
                r.surge_multiplier
              ) >= 2;

            return (
              <div
                key={i}
                className={`zone-card glass ${
                  high
                    ? "danger"
                    : ""
                }`}
              >
                <div className="zone-top">
                  <span>{r.area}</span>

                  <span className="badge">
                    {
                      r.surge_multiplier
                    }
                    x
                  </span>
                </div>

                <div className="zone-stats">
                  <div>
                    Drivers:{" "}
                    {r.drivers}
                  </div>

                  <div>
                    Riders:{" "}
                    {r.riders}
                  </div>
                </div>

                <div className="mini">
                  <span>
                    Rule{" "}
                    {r.rule_surge}x
                  </span>

                  <span>
                    ML {r.ml_surge}x
                  </span>
                </div>

                {high && (
                  <div className="alert">
                    HIGH DEMAND 🔥
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}

/* -------------------------
   KPI CARD
-------------------------- */
function KPI({
  title,
  value,
  icon,
}) {
  return (
    <div className="glass kpi">
      <div className="kpi-top">
        {icon}
        <span>{title}</span>
      </div>

      <div className="kpi-value">
        {value}
      </div>
    </div>
  );
}