import { useEffect, useState } from "react"

import { apiGet } from "@/lib/api"

type PollingState<T> = {
    data: T | null
    error: string | null
    loading: boolean
}

export function usePolling<T>(path: string, intervalMs = 10000): PollingState<T> {
    const [state, setState] = useState<PollingState<T>>({
        data: null,
        error: null,
        loading: true,
    })

    useEffect(() => {
        let cancelled = false
        async function load() {
            try {
                const data = await apiGet<T>(path)
                if (!cancelled) setState({ data, error: null, loading: false })
            } catch (e) {
                if (!cancelled) {
                    const message = e instanceof Error ? e.message : "알 수 없는 오류"
                    setState((prev) => ({ ...prev, error: message, loading: false }))
                }
            }
        }

        load()
        const timer = intervalMs > 0 ? setInterval(load, intervalMs) : undefined
        return () => {
            cancelled = true
            clearInterval(timer)
        }
    }, [path, intervalMs])

    return state
}