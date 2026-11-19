import { Line, LineChart } from 'recharts'

/** Mini gráfico de tendência, sem eixos (decorativo; a tendência também vem em texto). */
export function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null
  const data = values.map((v, i) => ({ i, v }))
  return (
    <LineChart width={72} height={24} data={data} aria-hidden="true">
      <Line type="monotone" dataKey="v" stroke="#404040" strokeWidth={1.5} dot={false} isAnimationActive={false} />
    </LineChart>
  )
}
