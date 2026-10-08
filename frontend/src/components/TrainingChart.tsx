import { useState } from "react"
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, } from "recharts"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type Point = { step: number; value: number }
type MetricKey = "mAP50" | "mAP50_95" | "precision" | "recall"

export type Cumulative = {
    single_class: Record<MetricKey, Point[]>
    multi_class: Record<MetricKey, Point[]>
}

const METRICS: { key: MetricKey; label: string; desc: string }[] = [
    {
        key: "mAP50",
        label: "mAP50",
        desc: "예측 박스가 정답과 50% 이상 겹치면 맞다고 칠 때의 종합 정확도입니다. 1에 가까울수록 좋습니다.",
    },
    {
        key: "mAP50_95",
        label: "mAP50-95",
        desc: "겹침 기준을 50%에서 95%까지 점점 엄격하게 올려가며 평균한 값입니다. 박스 위치가 얼마나 정밀한지까지 반영해서 mAP50보다 항상 낮게 나옵니다.",
    },
    {
        key: "precision",
        label: "정밀도",
        desc: "모델이 탐지했다고 한 것 중 실제로 맞은 비율입니다. 높을수록 오탐(잘못된 경보)이 적습니다.",
    },
    {
        key: "recall",
        label: "재현율",
        desc: "실제로 있는 객체 중 모델이 찾아낸 비율입니다. 높을수록 놓치는 객체가 적습니다.",
    },
]

type Row = { step: number; single?: number; multi?: number }

function mergeSeries(single: Point[], multi: Point[]): Row[] {
    const rows = new Map<number, Row>()

    for (const p of single) {
        rows.set(p.step, { step: p.step, single: p.value })
    }
    for (const p of multi) {
        const row = rows.get(p.step) ?? { step: p.step}
        rows.set(p.step, { ...row, multi: p.value })
    }

    return [...rows.values()].sort((a, b) => a.step - b.step)
}

export function TrainingChart({ data }: { data: Cumulative }) {
    const [metric, setMetric] = useState<MetricKey>("mAP50")

    const current = METRICS.find((m) => m.key === metric)!
    const rows = mergeSeries(data.single_class[metric], data.multi_class[metric])

    return (
        <Card>
            <CardHeader>
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    누적 학습 곡선 (단일 클래스 vs 다중 클래스)
                </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
                <div className="flex flex-wrap gap-2">
                    {METRICS.map((m) => (
                        <button
                            key={m.key}
                            onClick={() => setMetric(m.key)}
                            className={cn(
                                "rounded-md px-3 py-1.5 text-sm transition-colors",
                                metric === m.key
                                    ? "bg-primary/10 text-primary"
                                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                            )}
                        >
                            {m.label}
                        </button>
                    ))}
                </div>

                <p className="text-sm text-muted-foreground">{current.desc}</p>

                <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                        <CartesianGrid vertical={false} stroke="var(--border)" />
                        <XAxis
                            dataKey="step"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                        />
                        <YAxis
                            domain={[(min: number) => Math.max(0, +(min - 0.05).toFixed(2)), 1]}
                            axisLine={false}
                            tickLine={false}
                            width={44}
                            tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                        />
                        <Tooltip
                            formatter={(value, name) => [Number(value).toFixed(3), String(name)]}
                            labelFormatter={(step) => `${step}번째 에폭`}
                            contentStyle={{
                                background: "var(--popover)",
                                border: "1px solid var(--border)",
                                borderRadius: 8,
                                color: "var(--foreground)",
                            }}
                            labelStyle={{ color: "var(--foreground)" }}
                        />
                        <Legend
                            iconType="plainline"
                            formatter={(value) => (
                                <span style={{ color: "var(--foreground)", fontSize: 12 }}>{value}</span>
                            )}
                        />
                        <Line
                            type="monotone"
                            dataKey="single"
                            name="단일 클래스"
                            stroke="var(--primary)"
                            strokeWidth={2}
                            dot={false}
                            activeDot={{ r: 4 }}
                        />
                        <Line
                            type="monotone"
                            dataKey="multi"
                            name="다중 클래스"
                            stroke="#a78bfa"
                            strokeWidth={2}
                            strokeDasharray="6 4"
                            dot={false}
                            activeDot={{ r: 4 }}
                        />
                    </LineChart>
                </ResponsiveContainer>

                <p className="text-xs text-muted-foreground">가로축: 누적 에폭</p>
            </CardContent>
        </Card>
    )
}
