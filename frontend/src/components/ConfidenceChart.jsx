import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

function barColor(v) {
  if (v >= 80) return "#10B981"
  if (v >= 60) return "#3B82F6"
  return "#F59E0B"
}

export default function ConfidenceChart({ sections }) {
  if (!sections || sections.length === 0) return null
  const data = sections.map((s) => ({ name: s.title, value: s.confidence }))

  return (
    <div className="bg-panel border border-edge rounded-xl p-4">
      <div className="text-xs uppercase tracking-wider text-muted mb-3">
        Confidence per section
      </div>
      <ResponsiveContainer width="100%" height={Math.max(180, 44 * data.length)}>
        <BarChart data={data} layout="vertical" margin={{ left: 4, right: 24, top: 4, bottom: 4 }}>
          <CartesianGrid stroke="#1f1f2a" strokeDasharray="3 3" />
          <XAxis
            type="number"
            domain={[0, 100]}
            tick={{ fill: "#6b7280", fontSize: 11 }}
          />
          <YAxis
            type="category"
            dataKey="name"
            tick={{ fill: "#e5e7eb", fontSize: 11 }}
            width={110}
          />
          <Tooltip
            cursor={{ fill: "#1f1f2a" }}
            contentStyle={{
              background: "#13131a",
              border: "1px solid #1f1f2a",
              borderRadius: 8,
              color: "#e5e7eb",
            }}
            formatter={(v) => `${v}%`}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={barColor(entry.value)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
