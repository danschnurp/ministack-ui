import { useState } from 'react'
import { useSQSQueues, useSQSMessages } from '../hooks/useSQS'

export default function SQSPage() {
  const [selectedQueue, setSelectedQueue] = useState('')
  const { data: queues, isLoading } = useSQSQueues()
  const { data: messages } = useSQSMessages(selectedQueue)

  if (isLoading) return (
    <div className="flex items-center justify-center h-96 bg-gray-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">SQS Queues</h1>
          <p className="mt-1 text-sm text-gray-500">View and manage SQS message queues</p>
        </div>

        <div className="p-6">
          <div className="max-w-md mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Queue:
            </label>
            <select
              value={selectedQueue}
              onChange={(e) => setSelectedQueue(e.target.value)}
              className="w-full p-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">-- Select a Queue --</option>
              {queues?.map((queue) => (
                <option key={queue} value={queue}>
                  {queue}
                </option>
              ))}
            </select>
          </div>

          {selectedQueue && messages && (
            <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700 truncate max-w-[200px]">
                    {selectedQueue}
                  </h3>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                    {messages?.length || 0} messages
                  </span>
                </div>
              </div>
              
              <div className="divide-y divide-gray-100">
                {messages?.map((message, index) => (
                  <div key={index} className="p-4 hover:bg-gray-100 transition-colors duration-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-mono text-gray-500">
                        MessageId: {message.MessageId?.substring(0, 20)}...
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(message.ReceivedAt).toLocaleString()}
                      </span>
                    </div>
                    <div className="bg-white rounded p-3 border border-gray-200">
                      <pre className="text-xs text-gray-700 overflow-auto whitespace-pre-wrap">
                        {JSON.stringify(message.Body, null, 2)}
                      </pre>
                    </div>
                  </div>
                ))}
              </div>

              {messages?.length === 0 && (
                <div className="p-8 text-center">
                  <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-sm font-medium text-gray-900">No messages</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    This queue is currently empty.
                  </p>
                </div>
              )}
            </div>
          )}

          {!selectedQueue && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M4 12a8 8 0 018-8 8 8 0 018 8 8 8 0 01-8 8 8 8 0 01-8-8z" />
                </svg>
              </div>
              <h3 className="text-sm font-medium text-gray-900">Select a queue</h3>
              <p className="mt-1 text-sm text-gray-500">
                Choose a queue from the dropdown to view its messages.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
