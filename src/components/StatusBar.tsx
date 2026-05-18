import { useQuery } from '@tanstack/react-query'

async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch('/api/health')
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
  })

  return (
    <div className="px-3 py-2 border-top" style={{ fontSize: 12 }}>
      <span
        className="me-2"
        style={{
          display: 'inline-block',
          width: 8, height: 8, borderRadius: '50%',
          background: healthy === undefined ? '#aaa' : healthy ? '#198754' : '#dc3545',
        }}
      />
      {healthy === undefined ? 'connecting…' : healthy ? ':4566 · healthy' : ':4566 · unreachable'}
    </div>
  )
}
