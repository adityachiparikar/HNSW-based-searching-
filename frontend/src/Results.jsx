export default function Results({ results, latency }) {
    const fieldEntries = (fields = {}) => {
        const preferred = ['brand', 'make', 'manufacturer', 'model', 'engine', 'engine_type', 'engine type', 'price', 'msrp', 'category']
        return Object.entries(fields)
            .filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '')
            .sort(([a], [b]) => {
                const ai = preferred.indexOf(a.toLowerCase())
                const bi = preferred.indexOf(b.toLowerCase())
                return (ai === -1 ? preferred.length : ai) - (bi === -1 ? preferred.length : bi)
            })
            .slice(0, 6)
    }

    const fieldLabel = (key) => key.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase())

    if (!results || results.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500 text-center">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-16 h-16 mb-4 opacity-50">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
                <p className="text-lg">No results to display.</p>
                <p className="text-sm mt-1">Try uploading a dataset or using sample data.</p>
            </div>
        )
    }

    return (
        <div className="animate-fade-in-up">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400">
                    Search Results
                </h3>

                {latency > 0 && (
                    <div className="text-sm bg-slate-800/80 px-3 py-1.5 rounded-full text-slate-400 border border-slate-700/50 flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-emerald-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                        </svg>
                        Latency: <span className="text-emerald-400 font-mono">{latency.toFixed(2)} ms</span>
                    </div>
                )}
            </div>

            <div className="space-y-4">
                {results.map((result, idx) => (
                    <div
                        key={idx}
                        className="group relative bg-slate-800/40 hover:bg-slate-800 border border-slate-700/50 hover:border-indigo-500/30 p-5 rounded-xl transition-all duration-300 shadow-sm hover:shadow-indigo-500/10"
                        style={{ animationDelay: `${idx * 50}ms` }}
                    >
                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/0 via-indigo-500/0 to-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl"></div>

                        <div className="relative flex justify-between items-start">
                            <div className="flex-1 pr-4">
                                <p className="text-lg font-medium text-slate-100 group-hover:text-indigo-200 transition-colors">
                                    {result.text}
                                </p>
                                {fieldEntries(result.fields).length > 0 && (
                                    <div className="mt-3 flex flex-wrap gap-2">
                                        {fieldEntries(result.fields).map(([key, value]) => (
                                            <span
                                                key={key}
                                                className="text-xs bg-slate-900/80 border border-slate-700 px-2 py-1 rounded text-slate-300"
                                            >
                                                <span className="text-slate-500">{fieldLabel(key)}:</span> {value}
                                            </span>
                                        ))}
                                    </div>
                                )}
                                <div className="mt-2 flex items-center gap-3">
                                    <span className="text-xs bg-slate-900 border border-slate-700 px-2 py-1 rounded text-slate-400 font-mono">
                                        ID: {result.id}
                                    </span>
                                    <span className="text-xs text-slate-500 font-mono">
                                        Score Dist: {result.distance.toFixed(4)}
                                    </span>
                                    {typeof result.semantic_similarity === 'number' && (
                                        <span className="text-xs text-slate-500 font-mono">
                                            Semantic: {result.semantic_similarity.toFixed(4)}
                                        </span>
                                    )}
                                    {typeof result.exact_boost === 'number' && result.exact_boost > 0 && (
                                        <span className="text-xs text-emerald-400 font-mono">
                                            Boost: +{result.exact_boost.toFixed(2)}
                                        </span>
                                    )}
                                </div>
                                {result.match_reasons?.length > 0 && (
                                    <div className="mt-3 flex flex-wrap gap-2">
                                        {result.match_reasons.map((reason) => (
                                            <span
                                                key={reason}
                                                className="text-xs bg-emerald-500/10 border border-emerald-500/30 px-2 py-1 rounded text-emerald-300"
                                            >
                                                {reason}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="flex flex-col items-end">
                                <div className="text-sm font-semibold text-indigo-400 mb-1">
                                    Hybrid Match
                                </div>
                                <div className="flex items-center gap-2">
                                    <div className="w-16 h-2 bg-slate-900 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                                            style={{ width: `${Math.min(100, Math.max(0, result.similarity) * 100)}%` }}
                                        ></div>
                                    </div>
                                    <span className="font-mono text-purple-300 font-bold w-12 text-right">
                                        {result.similarity.toFixed(4)}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}
