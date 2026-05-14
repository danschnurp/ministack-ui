import { useState } from 'react'
import { useDynamoTables, useDynamoItems } from '../hooks/useDynamo'

export default function DynamoPage() {
  const [selectedTable, setSelectedTable] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const { data: tables, isLoading: tablesLoading } = useDynamoTables()
  const { data: items, isLoading: itemsLoading } = useDynamoItems(selectedTable)

  if (tablesLoading || itemsLoading) return (
    <div className="flex items-center justify-center h-96 bg-gray-50">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  )

  return (
    <div className="p-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">DynamoDB Tables</h1>
          <p className="mt-1 text-sm text-gray-500">Browse and search DynamoDB items</p>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Table selection */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Table:
              </label>
              <select
                value={selectedTable}
                onChange={(e) => setSelectedTable(e.target.value)}
                className="w-full p-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">-- Select a Table --</option>
                {tables?.map((table) => (
                  <option key={table} value={table}>
                    {table}
                  </option>
                ))}
              </select>
            </div>

            {/* Search input */}
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search (Optional):
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by key or value..."
                className="w-full p-2.5 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              {searchQuery && (
                <p className="mt-2 text-xs text-gray-500">
                  Showing {items?.length || 0} results for "{searchQuery}"
                </p>
              )}
            </div>
          </div>

          {/* Items grid */}
          {selectedTable && items && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {items.map((item, index) => (
                <div
                  key={index}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow duration-200"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-mono text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {Object.keys(item)[0]}
                    </span>
                    <span className="text-xs text-gray-400">
                      {Object.keys(item).length} attributes
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-2">
                    <strong>Attributes:</strong>
                  </div>
                  <pre className="mt-2 p-3 bg-gray-900 text-gray-100 rounded-md font-mono text-xs overflow-auto max-h-60">
                    {JSON.stringify(item, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}

          {!selectedTable && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </div>
              <h3 className="text-sm font-medium text-gray-900">Select a table</h3>
              <p className="mt-1 text-sm text-gray-500">
                Choose a table from the dropdown to view its items.
              </p>
            </div>
          )}

          {selectedTable && items?.length === 0 && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-3">
                <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-sm font-medium text-gray-900">No items found</h3>
              <p className="mt-1 text-sm text-gray-500">
                This table is empty or no items match your search.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
