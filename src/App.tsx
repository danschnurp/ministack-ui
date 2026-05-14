import { useState } from 'react'
import S3Page from './pages/S3Page'
import DynamoPage from './pages/DynamoPage'
import SQSPage from './pages/SQSPage'
import CloudWatchPage from './pages/CloudWatchPage'

const PAGES: Record<string, JSX.Element> = {
  S3: <S3Page />, 
  DynamoDB: <DynamoPage />, 
  SQS: <SQSPage />,
  CloudWatch: <CloudWatchPage />
}

export default function App() {
  const [page, setPage] = useState('S3')
  
  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <h1 className="text-xl font-bold text-gray-900">
                  <span className="text-blue-600">AWS</span> MiniStack UI
                </h1>
              </div>
              <div className="hidden md:ml-6 md:flex md:space-x-2">
                {Object.keys(PAGES).map((p) => (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200 ${
                      page === p
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Mobile menu button */}
            <div className="flex items-center md:hidden">
              <button
                type="button"
                className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100"
              >
                <svg
                  className="w-6 h-6"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M4 6h16M4 12h16M4 18h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {Object.keys(PAGES).find((k) => PAGES[k] === PAGES[page])} Console
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Manage your AWS services from a single interface
            </p>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            {PAGES[page]}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-500">
              © 2024 AWS MiniStack UI - A demonstration of AWS service management
            </p>
            <div className="flex items-center space-x-4 mt-2 md:mt-0">
              <span className="text-xs text-gray-400">Built with React & Tailwind CSS</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
