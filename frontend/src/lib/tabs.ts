import {
    Bell,
    Cpu,
    LayoutDashboard,
    ScanSearch,
    TrendingUp,
    Video,
} from "lucide-react"
import type { LucideIcon } from "lucide-react"

export type TabKey =
    | "dashboard"
    | "alerts"
    | "detect"
    | "video"
    | "training"
    | "model"

export const TABS: { key: TabKey; label: string; icon: LucideIcon }[] = [
    { key: "dashboard", label: "운영 대시보드", icon: LayoutDashboard },
    { key: "alerts", label: "경보", icon: Bell },
    { key: "detect", label: "객체 탐지", icon: ScanSearch },
    { key: "video", label: "비디오 탐지", icon: Video },
    { key: "training", label: "학습 이력", icon: TrendingUp },
    { key: "model", label: "모델 정보", icon: Cpu },
]