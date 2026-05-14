import { useEffect, useState } from 'react'

export default function StatusBar() {
  const [status, setStatus] = useState('Connecting...')

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch('/api/health')
        if (res.ok) {
          setStatus('✓ Connected to MiniStack')
        } else {
          setStatus('✗ MiniStack not responding')
        }
      } catch (error) {
        setStatus('✗ Connection error')
      }
    }

    checkStatus()
    const interval = setInterval(checkStatus, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="fixed bottom-0 right-0 left-0 bg-gray-800 text-white p-2 text-xs flex items-center justify-between">
      <span>{status}</span>
      <span className="text-gray-400">MiniStack UI v0.1.0</span>
    </div>
  )
}
