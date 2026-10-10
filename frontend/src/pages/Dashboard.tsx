import { Stat } from "@/components/Stat"
import { Card, CardContent } from "@/components/ui/card"
import { usePolling } from "@/lib/usePolling"
import { CountBarChart, toRows } from "@/components/CountBarChart"

type Metrics = {
    total_requests: number
    total_detections: number
    avg_confidence: number
    avg_inference_time_ms: number
    requests_by_endpoint: Record<string, number>
}

type Defense = {
    low_fpr_recall: {
        conf_threshold: number
        precision: number
        recall: number
    } | null
    fps_benchmark: {
        sample_size: number
        elapsed_sec: number
        fps: number
    } | null
    class_distribution: Record<string, number>
}

export function DashboardPage() {
    const metrics = usePolling<Metrics>("/metrics")
    const defense = usePolling<Defense>("/metrics/defense", 30000)

    if (metrics.error && !metrics.data) {
        return (
            <Card>
                <CardContent className="py-5 text-sm text-destructive">
                    지표를 불러오지 못했습니다({metrics.error})
                </CardContent>
            </Card>
        )
    }

    if (!metrics.data) {
        return <p className="text-sm text-muted-foreground">불러오는 중...</p>
    }

    const m = metrics.data
    const fps = defense.data?.fps_benchmark?.fps
    const recall = defense.data?.low_fpr_recall?.recall
    const endpointRows = toRows(m.requests_by_endpoint)
    const classRows = toRows(defense.data?.class_distribution ?? {})

    return (
        <div className="flex flex-col gap-6">
            <div className="grid max-w-4xl grid-cols-2 gap-4 lg:grid-cols-4">
                <Stat label="이미지 탐지 요청 수" value={m.total_requests.toLocaleString()} />
                <Stat label="이미지 탐지 수" value={m.total_detections.toLocaleString()} />
                <Stat label="평균 신뢰도" value={(m.avg_confidence * 100).toFixed(1)} unit="%" />
                <Stat label="평균 추론 시간" value={m.avg_inference_time_ms.toFixed(1)} unit="ms" />
            </div>

            <div className="grid max-w-4xl grid-cols-2 gap-4 lg:grid-cols-4">
                <Stat
                    label="처리 속도"
                    value={fps !== undefined ? fps.toFixed(1) : "-"}
                    unit="FPS"
                    tone="text-primary"
                />
                <Stat
                    label="Low-FPR 재현율"
                    value={recall !== undefined ? (recall * 100).toFixed(1) : "-"}
                    unit="%"
                    tone="text-primary"
                />
            </div>

            <div className="grid max-w-4xl gap-4 lg:grid-cols-2">
                <CountBarChart title="엔드포인트별 요청 수" rows={endpointRows} unit="회" />
                <CountBarChart title="클래스별 탐지 수" rows={classRows} unit="건" />
            </div>
        </div>
    )
}