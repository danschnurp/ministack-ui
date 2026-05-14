import { useState } from 'react'
import { useLogGroups, useLogStreams, useLogEvents } from '../hooks/useCloudWatch'

export default function CloudWatchPage() {
  const [selectedLogGroup, setSelectedLogGroup] = useState('')
  const [selectedLogStream, setSelectedLogStream] = useState('')
  
  const { data: logGroups, isLoading: isLoadingGroups } = useLogGroups()
  const { data: logStreams, isLoading: isLoadingStreams } = useLogStreams(selectedLogGroup)
  const { data: logEvents, isLoading: isLoadingEvents } = useLogEvents(selectedLogGroup, selectedLogStream)

  if (isLoadingGroups) return (
    <div className="flex items-center justify-center h-96 bg-gray-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">CloudWatch Logs</h1>
          <p className="mt-1 text-sm text-gray-500">Browse and analyze your AWS CloudWatch logs</p>
        </div>

        <div className="flex flex-col lg:flex-row">
          {/* Log Groups Sidebar */}
          <div className="w-full lg:w-64 border-r border-gray-200 bg-gray-50">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">Log Groups</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {logGroups?.map((g) => (
                <button
                  key={g}
                  onClick={() => { setSelectedLogGroup(g); setSelectedLogStream(''); }}
                  className={`w-full text-left px-4 py-3 text-sm transition-colors duration-200 ${
                    selectedLogGroup === g
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'
                  }`}
                >
                  <div className="font-medium truncate">{g}</div>
                </button>
              ))}
              {logGroups?.length === 0 && (
                <div className="p-4 text-center text-sm text-gray-500">
                  No log groups found
                </div>
              )}
            </div>
          </div>

          {/* Log Streams Sidebar */}
          <div className="w-full lg:w-48 border-r border-gray-200 bg-gray-50">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">Log Streams</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {logStreams?.map((s) => (
                <button
                  key={s}
                  onClick={() => setSelectedLogStream(s)}
                  className={`w-full text-left px-4 py-3 text-sm transition-colors duration-200 ${
                    selectedLogStream === s
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'
                  }`}
                >
                  <div className="font-medium truncate">{s}</div>
                </button>
              ))}
              {logStreams?.length === 0 && selectedLogGroup && (
                <div className="p-4 text-center text-sm text-gray-500">
                  No streams found
                </div>
              )}
            </div>
          </div>

          {/* Log Events Panel */}
          <div className="flex-1 p-4">
            {selectedLogStream && logEvents?.length > 0 ? (
              <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700">
                    Log Events ({logEvents.length})
                  </h3>
                  <span className="text-xs text-gray-500">
                    {selectedLogGroup} / {selectedLogStream}
                  </span>
                </div>
                
                <div className="divide-y divide-gray-100 max-h-[600px] overflow-auto">
                  {logEvents?.map((event: any, index: number) => (
                    <div key={index} className="p-3 hover:bg-gray-100 transition-colors duration-200">
                      <div className="flex items-start gap-2">
                        <span className="text-xs text-gray-400 whitespace-nowrap">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </span>
                        <div className="flex-1 min-w-0">
                          <pre className="text-xs text-gray-700 whitespace-pre-wrap break-all">
                            {event.message || event.eventId}
                          </pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : selectedLogStream && logEvents?.length === 0 ? (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 002 2h2a2 2 0 002-2" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-gray-900">No events found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This log stream contains no events.
                </p>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 002 2h2a2 2 0 002-2" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-gray-900">Select a stream</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose a log group and then a log stream to view events.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
