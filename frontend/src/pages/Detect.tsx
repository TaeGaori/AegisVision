import { useEffect, useRef, useState } from "react"
import type { ChangeEvent } from "react"
import { Upload } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { apiPostFile, apiPostFileForBlob } from "@/lib/api"

type Detection = {
    class_name: string
    confidence: number
    bbox: number[]
}

type PredictResult = {
    detections: Detection[]
}

export function DetectPage() {
    const inputRef = useRef<HTMLInputElement>(null)
    const [preview, setPreview] = useState<string | null>(null)
    const [resultImage, setResultImage] = useState<string | null>(null)
    const [result, setResult] = useState<PredictResult | null>(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        return () => {
            if (preview) URL.revokeObjectURL(preview)
        }
    }, [preview])

    useEffect(() => {
        return () => {
            if (resultImage) URL.revokeObjectURL(resultImage)
        }
    }, [resultImage])

    async function handleFile(e: ChangeEvent<HTMLInputElement>) {
        const file = e.target.files?.[0]
        e.target.value = ""
        if (!file) return

        setPreview(URL.createObjectURL(file))
        setResultImage(null)
        setResult(null)
        setError(null)
        setLoading(true)

        try {
            const [data, blob] = await Promise.all([
                apiPostFile<PredictResult>("/predict", file),
                apiPostFileForBlob("/predict/visualize", file),
            ])
            setResult(data)
            setResultImage(URL.createObjectURL(blob))
        } catch (err) {
            setError(err instanceof Error ? err.message : "알 수 없는 오류")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center gap-4">
                <input
                    ref={inputRef}
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleFile}
                />
                <Button onClick={() => inputRef.current?.click()} disabled={loading}>
                    <Upload className="size-4" />
                    이미지 선택
                </Button>
                {loading && <span className="text-sm text-muted-foreground">분석 중...</span>}
            </div>

            {error && (
                <Card>
                    <CardContent className="py-5 text-sm text-destructive">
                        탐지에 실패했습니다 ({error})
                    </CardContent>
                </Card>
            )}

            {preview && (
                <div className="flex max-w-5xl flex-col gap-4">
                    <div className="grid gap-4 lg:grid-cols-2">
                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    원본 이미지
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <img src={preview} alt="업로드한 이미지" className="w-full rounded-md" />
                            </CardContent>
                        </Card>

                        <Card>
                            <CardHeader>
                                <CardTitle className="text-sm font-medium text-muted-foreground">
                                    탐지 결과 이미지
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {resultImage ? (
                                    <img src={resultImage} alt="탐지 결과" className="w-full rounded-md" />
                                ) : (
                                    <p className="py-6 text-sm text-muted-foreground">
                                        {loading ? "분석 중..." : "결과 이미지가 없습니다."}
                                    </p>
                                )}
                            </CardContent>
                        </Card>
                    </div>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-sm font-medium text-muted-foreground">
                                탐지 목록
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-4">
                            {loading && <p className="text-sm text-muted-foreground">분석 중...</p>}

                            {result && result.detections.length === 0 && (
                                <p className="text-sm text-muted-foreground">탐지된 객체가 없습니다.</p>
                            )}

                            {result?.detections.map((d, index) => {
                                const percent = Math.round(d.confidence * 100)
                                return (
                                    <div key={index} className="flex flex-col gap-1.5">
                                        <div className="flex items-baseline justify-between">
                                            <span className="font-semibold">{d.class_name}</span>
                                            <span className="font-mono text-sm">{percent}%</span>
                                        </div>
                                        <div className="h-1.5 w-full rounded-full bg-muted">
                                            <div
                                                className="h-full rounded-full bg-primary"
                                                style={{ width: `${percent}%` }}
                                            />
                                        </div>
                                    </div>
                                )
                            })}
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    )
}