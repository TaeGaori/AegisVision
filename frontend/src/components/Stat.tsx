import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

type StatProps = {
    label: string
    value: number | string
    unit? : string
    tone? : string
}

export function Stat({ label, value, unit, tone }: StatProps) {
    return(
        <Card>
            <CardContent className="flex flex-col gap-1 py-5">
                <span className="text-xs tracking-wider text-muted-foreground">{label}</span>
                <span className={cn("font-mono text-3xl front-semibold", tone)}>
                    {value}
                    {unit && (
                        <span className="ml-1 text-sm font-normal text-muted-foreground">{unit}</span>
                    )}
                </span>
            </CardContent>
        </Card>
    )
}