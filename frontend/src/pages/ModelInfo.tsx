import { Stat } from "@/components/Stat"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { usePolling } from "@/lib/usePolling"

type ModelInfo = {
    model_path: string
    num_classes: number
    classes: Record<string, string>
}

export function ModelPage() {
    const { data, error } = usePolling<ModelInfo>("/model/info", 0)

    if (error && !data) {
        return (
            <Card>
                <CardContent className="py-5 text-sm text-destructive">
                    모델 정보를 불러오지 못했습니다 ({error})
                </CardContent>
            </Card>
        )
    }

    if (!data) {
        return <p className="text-sm text-muted-foreground">불러오는 중</p>
    }

    const fileName = data.model_path.split(/[\\/]/).pop() ?? data.model_path
    const classes = Object.entries(data.classes).sort(
        ([a], [b]) => Number(a) - Number(b)
    )

    return (
        <div className="flex max-w-4xl flex-col gap-6">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
                <Stat label="탐지 클래스 수" value={data.num_classes} />

                <Card className="sm:col-span-3">
                    <CardContent className="flex flex-col gap-1 py-5">
                        <span className="text-xs tracking-wider text-muted-foreground">
                            모델 파일
                        </span>
                        <span className="break-all font-mono text-xl font-semibold">
                            {fileName}
                        </span>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                        탐지 클래스
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        {classes.map(([id, name]) => (
                            <div
                                key={id}
                                className="flex items-center gap-3 rounded-md border border-border px-3 py-2.5"
                            >
                                <span className="font-mono text-xs text-muted-foreground">{id}</span>
                                <span className="font-medium">{name}</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    )
}