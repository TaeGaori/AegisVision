import { ApiStatus } from "@/components/ApiStatus"
import { Radar } from "lucide-react"

import { TABS } from "@/lib/tabs"
import type { TabKey } from "@/lib/tabs"
import { cn } from "@/lib/utils"

type SidebarProps = {
    active: TabKey
    onChange: (key: TabKey) => void
}

export function Sidebar({ active, onChange }: SidebarProps) {
    return (
        <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card">
            <div className="flex items-center gap-2 border-b border-border px-5 py-5">
                <Radar className="size-6 text-primary" />
                <span className="text-sm font-semibold tracking-[0.2em">
                    AEGISVISION
                </span>
            </div>

            <nav className="flew flew-col gap-1 p-3">
                {TABS.map(({ key, label, icon: Icon }) => (
                    <button
                        key={key}
                        onClick={() => onChange(key)}
                        className={cn(
                            "flex items-center gap-3 rounded-md px-3 py-2.5 text-left text-sm transition-colors",
                            active === key
                                ? "bg-primary/10 text=primary"
                                : "text-muted-foreground hover:bg-accent hover:text-foreground"
                        )}
                    >
                        <Icon className="size-4" />
                        {label}
                    </button>
                ))}
            </nav>

            <div className="mt-auto border-t border-border p-4">
                <ApiStatus />
            </div>
        </aside>
    )
}
