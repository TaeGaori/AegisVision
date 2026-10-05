import { useEffect, useState} from "react"

import { apiGet} from "@/lib/api"
import { cn } from "@/lib/utils"

type Health = { status: string; model_loaded: boolean }
type Status = "loading" | "ok" | "error"

export function ApiStatus() {
    const [status, setStatus] = useState<Status>("loading")
    const [modelLoaded, setModelLoaded] = useState(false)
 
    useEffect(() => {
        let cancelled = false
        async function check() {
            try {
                const data = await apiGet<Health>("/health")
                if (cancelled) return
                setModelLoaded(data.model_loaded)
                setStatus("ok")
            } catch {
                if (!cancelled) setStatus("error")
            }
        }

        check()
        const timer = setInterval(check, 10000)

        return () => {
            cancelled = true
            clearInterval(timer)
        }
    }, [])

    const label = 
    status === "ok" ? "API 정상" : status === "error" ? "API 연결 실패" : "확인 중 ..."

    return(
        <div className="flex flex-col gap-1.5 text-xs">
            <div className="flex items-center gap-2">
                <span 
                className={cn(
                    "size-2 rounded-full",
                    status === "ok" && "bg-primary",
                    status === "error" && "bg-destructive",
                    status === "loading" && "bg-muted-foreground"
                )}
                />
                <span className="font-medium">{label}</span>
            </div>
            {status === "ok" && (
                <span className="text-muted-foreground">모델: {modelLoaded ? "로드됨": "미로드"}</span>
            )}
        </div>
    )
}