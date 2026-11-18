import { useState, useEffect } from 'react'
import axios from 'axios'

import SearchBar from './SearchBar'
import Results from './Results'
import UploadDataset from './UploadDataset'
import GraphVisualization from './GraphVisualization'
import EmbeddingPlot from './EmbeddingPlot'

// Prefer IPv4 loopback to avoid some Windows setups resolving `localhost` to IPv6 (`::1`)
// while the backend binds only on IPv4.
const API_URL = 'http://127.0.0.1:8002'

function App() {
  const [stats, setStats] = useState(null)
  const [results, setResults] = useState([])
  const [queryLatency, setQueryLatency] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('search') // search, graph, plot

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_URL}/stats`)
      setStats(res.data)
    } catch (err) {
      console.error("Failed to fetch stats", err)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  const handleSearch = async (query, k) => {
    setLoading(true)
    setError(null)
    try {
      const res = await axios.post(`${API_URL}/search`, { query, k })
      if (res.data.error) {
        setError(res.data.error)
        setResults([])
        setQueryLatency(0)
      } else {
        setResults(res.data.results || [])
        setQueryLatency(res.data.latency || 0)
      }
    } catch (err) {
      console.error("Search failed", err)
      setError('Search failed: ' + err.message)
      setResults([])
      setQueryLatency(0)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = () => {
    fetchStats()
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20">
              V
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
              VectorSearch HNSW
            </h1>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('search')}
              className={`px-4 py-2 rounded-md transition-all ${activeTab === 'search' ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-600/30' : 'hover:bg-slate-800 text-slate-400 border border-transparent'}`}
            >
              Search
            </button>
            <button
              onClick={() => setActiveTab('graph')}
              className={`px-4 py-2 rounded-md transition-all ${activeTab === 'graph' ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-600/30' : 'hover:bg-slate-800 text-slate-400 border border-transparent'}`}
            >
              HNSW Graph
            </button>
            <button
              onClick={() => setActiveTab('plot')}
              className={`px-4 py-2 rounded-md transition-all ${activeTab === 'plot' ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-600/30' : 'hover:bg-slate-800 text-slate-400 border border-transparent'}`}
            >
              Embeddings
            </button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">

          {/* Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-xl">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-400" viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                  <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                </svg>
                Index Stats
              </h2>
              {stats ? (
                <div className="space-y-3">
                  <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg">
                    <span className="text-slate-400 text-sm">Total Vectors</span>
                    <span className="font-mono text-indigo-400 font-bold">{stats.total_vectors}</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg">
                    <span className="text-slate-400 text-sm">Graph Layers</span>
                    <span className="font-mono text-purple-400 font-bold">{stats.graph_layers}</span>
                  </div>
                  <div className="flex justify-between items-center bg-slate-800/50 p-3 rounded-lg">
                    <span className="text-slate-400 text-sm">Avg Connections</span>
                    <span className="font-mono text-pink-400 font-bold">{stats.average_connections}</span>
                  </div>
                </div>
              ) : (
                <div className="animate-pulse flex space-x-4">
                  <div className="flex-1 space-y-4 py-1">
                    <div className="h-10 bg-slate-800 rounded"></div>
                    <div className="h-10 bg-slate-800 rounded"></div>
                    <div className="h-10 bg-slate-800 rounded"></div>
                  </div>
                </div>
              )}
            </div>

            <UploadDataset onUploadSuccess={handleUploadSuccess} />
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-3">
            <div className="bg-slate-900 rounded-xl border border-slate-800 shadow-xl overflow-hidden min-h-[600px]">
              {activeTab === 'search' && (
                <div className="p-6 h-full flex flex-col">
                  <div className="mb-8">
                    <SearchBar onSearch={handleSearch} loading={loading} />
                  </div>

                  <div className="flex-grow">
                    {loading ? (
                      <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                        <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin mb-4"></div>
                        <p>Searching through vector space...</p>
                      </div>
                    ) : (
                      <>
                        {error && (
                          <div className="mb-4 p-3 text-sm text-red-400 bg-red-900/30 rounded-lg border border-red-900">
                            {error}
                          </div>
                        )}
                        <Results results={results} latency={queryLatency} />
                      </>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'graph' && (
                <div className="h-full">
                  <GraphVisualization stats={stats} />
                </div>
              )}

              {activeTab === 'plot' && (
                <div className="h-full">
                  <EmbeddingPlot results={results} />
                </div>
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}

export default App
