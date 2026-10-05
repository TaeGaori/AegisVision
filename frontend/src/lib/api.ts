const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const API_KEY = import.meta.env.VITE_API_KEY ?? ""

export async function apiGet<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: API_KEY ? { "X-API-Key": API_KEY} : {},
    })

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
    }

    return response.json() as Promise<T>
}