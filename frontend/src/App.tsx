import { useState } from "react"

import { Sidebar } from "@/components/Sidebar"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { TABS } from "@/lib/tabs"
import type { TabKey } from "@/lib/tabs"

export default function App() {
  const [active, setActive] = useState<TabKey>("dashboard")
  const current = TABS.find((tab) => tab.key === active)!

  return (
    <div className="flex min-h-screen bg-background text-foreground">
      <Sidebar active={active} onChange={setActive} />

      <main className="flex-1 p-8">
        <h1 className="text-2xl font-semibold">{current.label}</h1>

        <Card className="mt-6 max-w-xl">
          <CardHeader>
            <CardTitle>{current.label}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
             이 탭의 화면은 다음 단게에서 구현합니다.
          </CardContent>
        </Card>
      </main>
    </div>
  )
}