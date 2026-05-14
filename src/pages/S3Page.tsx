import { useState } from 'react'
import { useS3Buckets, useS3Objects } from '../hooks/useS3'

export default function S3Page() {
  const [selected, setSelected] = useState('')
  const { data: buckets, isLoading } = useS3Buckets()
  const { data: objects } = useS3Objects(selected)

  if (isLoading) return (
    <div className="flex items-center justify-center h-96 bg-gray-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">S3 Buckets</h1>
          <p className="mt-1 text-sm text-gray-500">Select a bucket to view its objects</p>
        </div>

        <div className="flex flex-col lg:flex-row">
          {/* Bucket selection sidebar */}
          <div className="w-full lg:w-64 border-r border-gray-200 bg-gray-50">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-sm font-semibold text-gray-700">Buckets</h3>
            </div>
            <div className="divide-y divide-gray-100">
              {buckets?.map((b) => (
                <button
                  key={b.Name}
                  onClick={() => setSelected(b.Name)}
                  className={`w-full text-left px-4 py-3 text-sm transition-colors duration-200 ${
                    selected === b.Name
                      ? 'bg-blue-50 text-blue-700 border-l-4 border-blue-500'
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 border-l-4 border-transparent'
                  }`}
                >
                  <div className="font-medium truncate">{b.Name}</div>
                  <div className="text-xs text-gray-400 mt-1">
                    {b.Region || 'us-east-1'}
                  </div>
                </button>
              ))}
              {buckets?.length === 0 && (
                <div className="p-4 text-center text-sm text-gray-500">
                  No buckets found
                </div>
              )}
            </div>
          </div>

          {/* Objects list */}
          <div className="flex-1 p-6">
            {selected && objects?.length > 0 ? (
              <div className="space-y-2">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-700">
                    Objects ({objects.length})
                  </h3>
                  <span className="text-xs text-gray-500">
                    Total: {objects.reduce((sum, o) => sum + Number(o.Size), 0)} bytes
                  </span>
                </div>
                {objects.map((o) => (
                  <div
                    key={o.Key}
                    className="flex items-center justify-between py-2 px-3 rounded hover:bg-gray-50 transition-colors duration-200 border border-gray-100"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {o.Key}
                      </div>
                      <div className="text-xs text-gray-400">
                        {new Date(o.LastModified).toLocaleString()}
                      </div>
                    </div>
                    <div className="ml-4 text-right">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                        {Number(o.Size).toLocaleString()} B
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : selected && objects?.length === 0 ? (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H7a2 2 0 00-2 2z" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-gray-900">No objects found</h3>
                <p className="mt-1 text-sm text-gray-500">
                  This bucket is empty or has no objects.
                </p>
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                  <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                </div>
                <h3 className="text-sm font-medium text-gray-900">Select a bucket</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Choose a bucket from the list on the left to view its objects.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
