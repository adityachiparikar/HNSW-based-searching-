import { useState } from 'react'

export default function SearchBar({ onSearch, loading }) {
    const [query, setQuery] = useState('')
    const [k, setK] = useState(20)

    const handleSubmit = (e) => {
        e.preventDefault()
        if (query.trim()) {
            const limit = Math.min(100, Math.max(1, Number.parseInt(k, 10) || 20))
            setK(limit)
            onSearch(query.trim(), limit)
        }
    }

    return (
        <form onSubmit={handleSubmit} className="relative group">
            <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <svg aria-hidden="true" className="w-5 h-5 text-indigo-400 group-focus-within:text-purple-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                </svg>
            </div>

            <div className="flex bg-slate-800 rounded-xl overflow-hidden shadow-inner shadow-black/20 focus-within:ring-2 ring-indigo-500/50 transition-all duration-300 group-hover:bg-slate-800/80">
                <input
                    type="search"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="block w-full p-4 pl-12 text-sm text-white bg-transparent outline-none placeholder-slate-400"
                    placeholder="Search by keyword or key..."
                    required
                />

                <div className="flex items-center space-x-2 border-l border-slate-700 pl-3 pr-2">
                    <label htmlFor="k-value" className="text-xs text-slate-400 uppercase tracking-widest hidden sm:block">Limit</label>
                    <input
                        id="k-value"
                        type="number"
                        min="1"
                        max="100"
                    value={k}
                    onChange={(e) => setK(e.target.value)}
                        className="w-16 bg-slate-900 border border-slate-700 text-white text-sm rounded-md focus:ring-indigo-500 focus:border-indigo-500 block p-2 text-center"
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="text-white absolute right-2.5 bottom-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 font-medium rounded-lg text-sm px-6 py-2 transition-all transform active:scale-95 disabled:opacity-75 disabled:cursor-not-allowed shadow-[0_0_15px_rgba(99,102,241,0.5)]"
                >
                    {loading ? 'Searching' : 'Search'}
                </button>
            </div>
        </form>
    )
}
