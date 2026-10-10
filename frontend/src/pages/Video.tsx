import { useEffect, useRef, useState } from "react"
import type { ChangeEvent } from "react"
import { LoaderCircle, Upload } from "lucide-react"

import { CountBarChart, toRows } from "@/components/CountBarChart"
import { Stat } from "@/components/Stat"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiPostFileWithHeaders } from "@/lib/api"

const MAX_BYTES = 50 * 1024 * 1024

type Summary = {
    total_frames: number
    frames_with_detection: number
    class_counts: Record<string, number>
    duration_sec: number
}

function parseSummary(raw: string | null): Summary | null {
    if (!raw) return null
    try {
        return JSON.parse(raw) as Summary
    } catch {
        return null
    }
}

export function VideoPage() {
    const inputRef = useRef<HTMLInputElement>(null)
    const [fileInfo, setFileInfo] = useState<{ name: string; size: number } | null>(null)
    const [resultUrl, setResultUrl] = useState<string | null>(null)
    const [summary, setSummary] = useState<Summary | null>(null)
    const [loading, setLoading] = useState(false)
    const [elapsed, setElapsed] = useState(0)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        return () => {
            if (resultUrl) URL.revokeObjectURL(resultUrl)
        }
    }, [resultUrl])

    useEffect(() => {
        if (!loading) return
        const timer = setInterval(() => setElapsed((s) => s + 1), 1000)
        return () => clearInterval(timer)
    }, [loading])

    async function handleFile(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]
        e.target.value = ""
        if (!file) return

        setFileInfo({ name: file.name, size: file.size })
        setResultUrl(null)
        setSummary(null)
        setError(null)

        if (file.size > MAX_BYTES) {
            setError("파일이 너무 큽니다. 50MB 이하의 영상을 선택해 주세요")
            return
        }

        setElapsed(0)
        setLoading(true)

        try {
            const { blob, headers } = await apiPostFileWithHeaders("/predict/video", file)
            setResultUrl(URL.createObjectURL(blob))
            setSummary(parseSummary(headers.get("X-Detection-summary")))
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류")
        } finally {
            setLoading(false)
        }
    }

    const ratio =
        summary && summary.total_frames > 0
            ? ((summary.frames_with_detection / summary.total_frames) * 100).toFixed(1)
            : "-"
    return (
        <div className="flex max-w-5xl flex-col gap-6">
            <div className="flex flex-wrap items-center gap-4">
                <input
                    ref={inputRef}
                    type="file"
                    accept="video/*"
                    className="hidden"
                    onChange={handleFile}
                />
                <Button onClick={() => inputRef.current?.click()} disabled={loading}>
                    <Upload className="size-4" />
                    영상 선택
                </Button>
                {fileInfo && (
                    <span className="font-mono text-xs text-muted-foreground">
                        {fileInfo.name} ({(fileInfo.size / 1024 / 1024).toFixed(1)}MB)
                    </span>
                )}
                <span className="text-xs text-muted-foreground">최대 50MB / 60초</span>
            </div>

            {loading && (
                <Card>
                    <CardContent className="flex items-center gap-3 py-5 text-sm">
                        <LoaderCircle className="size-5 animate-spin text-primary" />
                        <span>영상 분석 중... {elapsed}초 경과</span>
                        <span className="text-xs text-muted-foreground">
                            영상 길이에 따라 수 분이 걸릴 수 있습니다. 다른 탭으로 이동하지 마세요.
                        </span>
                    </CardContent>
                </Card>
            )}

            {error && (
                <Card>
                    <CardContent className="py-5 text-sm text-destructive">
                        영상 탐지에 실패했습니다 ({error})
                    </CardContent>
                </Card>
            )}

            {resultUrl && (
                <>
                    {summary ? (
                        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                            <Stat label="총 프레임" value={summary.total_frames.toLocaleString()} />
                            <Stat
                                label="탐지된 프레임"
                                value={summary.frames_with_detection.toLocaleString()}
                            />
                            <Stat label="탐지 비율" value={ratio} unit="%" tone="text-primary" />
                            <Stat label="영상 길이" value={summary.duration_sec.toFixed(1)} unit="초" />
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground">
                            요약 정보를 읽지 못했습니다. 결과 영상만 표시합니다.
                        </p>
                    )}

                    <div className="grid gap-4 lg:grid-cols-3">
                        <Card className="lg:col-span-2">
                            <CardHeader>
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    탐지 결과 영상
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="flex flex-col gap-3">
                                <video src={resultUrl} controls className="w-full rounded-md" />
                                <a
                                    href={resultUrl}
                                    download="result.mp4"
                                    className="text-sm text-primary underline"
                                >
                                    결과 영상 다운로드
                                </a>
                            </CardContent>
                        </Card>

                        {summary && (
                            <CountBarChart
                                title="클래스별 탐지 횟수"
                                rows={toRows(summary.class_counts)}
                                unit="건"
                            />
                        )}
                    </div>
                </>
            )}
        </div>
    )
}
