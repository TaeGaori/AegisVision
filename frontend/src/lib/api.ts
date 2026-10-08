const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const API_KEY = import.meta.env.VITE_API_KEY ?? ""

export async function apiGet<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        headers: API_KEY ? { "X-API-Key": API_KEY } : {},
    })

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
    }

    return response.json() as Promise<T>
}

async function postFile(path: string, file: File): Promise<Response> {
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}${path}`, {
        method: "POST",
        headers: API_KEY ? { "X-API-Key": API_KEY } : {},
        body: formData,
    })

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
    }
    return response
}

export async function apiPostFile<T>(path: string, file: File): Promise<T> {
    const response = await postFile(path, file)
    return response.json() as Promise<T>
}

export async function apiPostFileForBlob(path: string, file: File): Promise<Blob> {
    const response = await postFile(path, file)
    return response.blob()
}

export async function apiPostFileWithHeaders(path: string, file: File): Promise<{ blob: Blob; headers: Headers }> {
    const response = await postFile(path, file)
    const blob = await response.blob()
    return { blob, headers: response.headers}
}