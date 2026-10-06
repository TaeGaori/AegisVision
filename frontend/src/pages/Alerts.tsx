import { Stat } from "@/components/Stat"
import { Card, CardContent } from "@/components/ui/card"
import { usePolling } from "@/lib/usePolling"
import { cn } from "@/lib/utils"

type Level = "critical" | "high" | "medium" | "low" | "none"

type Alert = {
  filename: string
  class_name: string
  confidence: number
  threat_level: Level
  detected_at: string
}

const LEVEL_STYLE: Record<Level, { label: string; bar: string; text: string }> = {
  critical: { label: "CRITICAL", bar: "bg-destructive", text: "text-destructive" },
  high: { label: "HIGH", bar: "bg-amber-400", text: "text-amber-400" },
  medium: { label: "MEDIUM", bar: "bg-sky-400", text: "text-sky-400" },
  low: { label: "LOW", bar: "bg-muted-foreground", text: "text-muted-foreground" },
  none: { label: "NONE", bar: "bg-muted-foreground", text: "text-muted-foreground" },
}


export function AlertsPage() {
  const { data, error, loading } = usePolling<Alert[]>("/alerts")
  const alerts = data ?? []

  const criticalCount = alerts.filter((a) => a.threat_level === "critical").length
  const highCount = alerts.filter((a) => a.threat_level === "high").length

  return (
    <div className="flex flex-col gap-6">
      <div className="grid max-w-2xl grid-cols-3 gap-4">
        <Stat label="전체 경보" value={alerts.length} />
        <Stat label="CRITICAL" value={criticalCount} tone="text-destructive" />
        <Stat label="HIGH" value={highCount} tone="text-amber-400" />
      </div>

      {error && !data && (
        <Card>
          <CardContent className="py-5 text-sm text-destructive">
            경보 목록을 불러오지 못했습니다 ({error})
          </CardContent>
        </Card>
      )}

      {loading && !data && (
        <p className="text-sm text-muted-foreground">불러오는 중</p>
      )}

      {data && alerts.length === 0 && (
        <Card>
          <CardContent className="py-5 text-sm text-muted-foreground">
            현재 고위험 경보가 없습니다.
          </CardContent>
        </Card>
      )}

      <div className="flex flex-col gap-3">
        {alerts.map((alert, index) => {
          const style = LEVEL_STYLE[alert.threat_level] ?? LEVEL_STYLE.none
          return (
            <Card key={`${alert.detected_at}-${index}`} className="overflow-hidden py-0">
              <CardContent className="flex items-stretch gap-4 p-0">
                <div className={cn("w-1.5 shrink-0", style.bar)} />

                <div className="flex flex-1 items-center justify-between gap-4 py-4 pr-5">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "size-2 rounded-full",
                          style.bar,
                          alert.threat_level === "critical" && "animate-pulse"
                        )}
                      />
                      <span className={cn("text-xs font-semibold tracking-wider", style.text)}>
                        {style.label}
                      </span>
                    </div>
                    <span className="text-lg font-semibold">{alert.class_name}</span>
                    <span className="font-mono text-xs text-muted-foreground">
                      {alert.filename}
                    </span>
                  </div>

                  <div className="flex flex-col items-end gap-1">
                    <span className="font-mono text-2xl">
                      {Math.round(alert.confidence * 100)}%
                    </span>
                    <span className="font-mono text-xs text-muted-foreground">
                      {alert.detected_at.slice(0, 19)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}