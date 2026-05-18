import { useQuery } from '@tanstack/react-query'
import { SDK_ENDPOINT } from '../aws/clients'

async function checkHealth(): Promise<boolean> {
  try {
    // Use the same base URL the SDK uses — works in both dev and Tauri prod build
    const url = SDK_ENDPOINT.replace(/\/api$/, '')
    const res = await fetch(url, { signal: AbortSignal.timeout(2000) })
    return res.ok
  } catch {
    return false
  }
}

export default function StatusBar() {
  const { data: healthy } = useQuery({
    queryKey: ['health'],
    queryFn: checkHealth,
    refetchInterval: 5000,
    retry: 0,
  })

  const color = healthy === undefined ? '#aaa' : healthy ? '#198754' : '#dc3545'
  const label = healthy === undefined ? 'connecting…' : healthy ? ':4566 · healthy' : ':4566 · unreachable'

  return (
    <div className="px-3 py-2 border-top" style={{ fontSize: 12 }}>
      <span className="me-2" style={{
        display: 'inline-block', width: 8, height: 8,
        borderRadius: '50%', background: color,
      }} />
      {label}
    </div>
  )
}