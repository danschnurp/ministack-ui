import { useState } from 'react'
import { useLambdaFunctions, useLambdaInvocation, useLambdaLogs } from '../hooks/useLambda'

export default function LambdaPage() {
  const [selectedFunction, setSelectedFunction] = useState('')
  const { data: functions, isLoading: isLoadingFunctions } = useLambdaFunctions()
  const invocation = useLambdaInvocation(selectedFunction)
  const { data: logs, isLoading: isLoadingLogs } = useLambdaLogs(selectedFunction)

  if (isLoadingFunctions) return <p>Loading functions…</p>

  return (
    <div className="flex gap-4 p-4">
      <div className="w-48 border rounded">
        <h3 className="text-sm font-semibold p-2">Functions</h3>
        <ul className="mt-2">
          {functions?.map(f => (
            <li key={f} className={`p-2 cursor-pointer hover:bg-gray-100 ${selectedFunction === f ? 'bg-blue-50 font-medium' : ''}`}
                onClick={() => setSelectedFunction(f)}>
              {f}
            </li>
          ))}
        </ul>
      </div>

      <div className="flex-1 border rounded p-2">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold">Function Logs</h3>
          {selectedFunction && (
            <button 
              onClick={() => invocation.mutate()}
              className="px-3 py-1 bg-blue-500 text-white rounded text-xs hover:bg-blue-600">
              {invocation.isPending ? 'Invoking...' : 'Invoke Function'}
            </button>
          )}
        </div>

        {logs?.length === 0 ? (
          <p className="text-gray-500 text-sm">No logs available yet. Click "Invoke Function" to start.</p>
        ) : (
          <div className="space-y-1 font-mono text-xs bg-gray-900 text-green-400 p-2 rounded overflow-auto h-96">
            {logs?.map((log: any, index: number) => (
              <div key={index} className="border-b border-gray-700 pb-1">
                <span className="text-gray-500">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                <span className="ml-2">{log.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
