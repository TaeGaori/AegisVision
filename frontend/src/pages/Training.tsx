import { Stat } from "@/components/Stat"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { usePolling } from "@/lib/usePolling"
import { cn } from "@/lib/utils"
import { TrainingChart } from "@/components/TrainingChart"
import type { Cumulative } from "@/components/TrainingChart"

type Run = {
    run_name: string
    status: string
    epochs: number
    actual_epochs: number
    mAP50: number
    mAP50_95: number
    precision: number
    recall: number
    started_at: string
}

type TrainingHistory = {
    total_sessions: number
    total_epochs: number
    runs: Run[]
    cumulative_metrics: Cumulative
}

const STATUS_STYLE: Record<string, string> = {
    FINISHED: "text-primary",
    FAILED: "text=destructive",
    RUNNING: "text-amber-400",
}

function formatDate(ms: string) {
    return new Date(Number(ms)).toLocaleDateString("ko-KR")
}

export function TrainingPage() {
    const { data, error } = usePolling<TrainingHistory>("/model/training-history", 0)

    if (error && !data) {
        return (
            <Card>
                <CardContent className="py-5 text-sm text-destructive">
                    학습 이력을 불러오지 못했습니다 ({error})
                </CardContent>
            </Card>
        )
    }

    if (!data) {
        return <p className="text-sm text-muted-foreground">불러오는 중</p>
    }
    const runs = [...data.runs].sort(
        (a, b) => Number(b.started_at) - Number(a.started_at)
    )
    const finished = data.runs.filter((run) => run.status === "FINISHED")
    const bestMap50 =
        finished.length > 0
            ? Math.max(...finished.map((run) => run.mAP50)).toFixed(3)
            : "-"

    return (
        <div className="flex max-w-5xl flex-col gap-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <Stat label="학습 세션 수" value={data.total_sessions} />
                <Stat label="총 에폭" value={data.total_epochs} />
                <Stat label="최고 mAP50 (완료된 학습)" value={bestMap50} tone="text-primary" />
            </div>

            <TrainingChart data={data.cumulative_metrics} />

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                        학습 실행 기록
                    </CardTitle>
                </CardHeader>
                <CardContent className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="border-b border-border text-left text-xs text-muted-foreground">
                                <th className="py-2 pr-4 font-medium">실행 이름</th>
                                <th className="py-2 pr-4 font-medium">상태</th>
                                <th className="py-2 pr-4 text-right font-medium">에폭</th>
                                <th className="py-2 pr-4 text-right font-medium">mAP50</th>
                                <th className="py-2 pr-4 text-right font-medium">mAP50-95</th>
                                <th className="py-2 pr-4 text-right font-medium">정밀도</th>
                                <th className="py-2 pr-4 text-right font-medium">재현율</th>
                                <th className="py-2 text-right font-medium">시작일</th>
                            </tr>
                        </thead>
                        <tbody>
                            {runs.map((run) => (
                                <tr key={run.run_name} className="border-b border-border last:border-0">
                                    <td className="py-3 pr-4 font-mono text-xs">{run.run_name}</td>
                                    <td
                                        className={cn(
                                            "py-3 pr-4 text-xs font-semibold",
                                            STATUS_STYLE[run.status] ?? "text-muted-foreground"
                                        )}
                                    >
                                        {run.status}
                                    </td>
                                    <td className="py-3 pr-4 text-right font-mono">
                                        {run.actual_epochs} / {run.epochs}
                                    </td>
                                    <td className="py-3 pr-4 text-right font-mono">{run.mAP50.toFixed(3)}</td>
                                    <td className="py-3 pr-4 text-right font-mono">{run.mAP50_95.toFixed(3)}</td>
                                    <td className="py-3 pr-4 text-right font-mono">{run.precision.toFixed(3)}</td>
                                    <td className="py-3 pr-4 text-right font-mono">{run.recall.toFixed(3)}</td>
                                    <td className="py-3 text-right font-mono text-xs text-muted-foreground">
                                        {formatDate(run.started_at)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </CardContent>
            </Card>
        </div>
    )
}

