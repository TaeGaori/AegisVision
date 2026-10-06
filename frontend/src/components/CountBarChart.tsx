import {
    Bar,
    BarChart,
    CartesianGrid,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
type Row = { name: string; value: number }

export function toRows(counts: Record<string, number>): Row[] {
    return Object.entries(counts)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
}

type CountBarChartProps = {
    title: string
    rows: Row[]
    unit: string
}

export function CountBarChart({ title, rows, unit }: CountBarChartProps) {
  const height = rows.length * 40 + 30

return (
    <Card>
        <CardHeader>
            <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        </CardHeader>
        <CardContent>
            {rows.length === 0 ? (
                <p className="py-6 text-sm text-muted-foreground">아직 데이터가 없습니다.</p>
            ) : (
                <ResponsiveContainer width="100%" height={height}>
                    <BarChart data={rows} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
                        <CartesianGrid horizontal={false} stroke="var(--border)" />
                        <XAxis
                            type="number"
                            allowDecimals={false}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
                            width={110}
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: "var(--foreground)", fontSize: 12 }}
                        />
                        <Tooltip
                            cursor={{ fill: "var(--accent)" }}
                            formatter={(value) => [`${Number(value).toLocaleString()} ${unit}`, ""]}
                            contentStyle={{
                                background: "var(--popover)",
                                border: "1px solid var(--border)",
                                borderRadius: 8,
                                color: "var(--foreground)",
                            }}
                            labelStyle={{ color: "var(--foreground)" }}
                            itemStyle={{ color: "var(--foreground)" }}
                        />
                        <Bar dataKey="value" fill="var(--primary)" barSize={14} radius={[0, 4, 4, 0]} />
                    </BarChart>
                </ResponsiveContainer>
            )}
        </CardContent>
    </Card>
)
}