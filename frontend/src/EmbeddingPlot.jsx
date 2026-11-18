import { useMemo } from 'react'
import Plot from 'react-plotly.js'

export default function EmbeddingPlot({ results }) {
    const plotData = useMemo(() => {
        if (!results || results.length === 0) return null

        // We only have the searched vector if user searched.
        // Assuming each result has a 'vector' from backend
        // Since vectors are typically 384d (all-MiniLM-L6-v2)
        // We do simple pseudorandom 2D projection based on vectors for visualization

        const x = []
        const y = []
        const texts = []
        const colors = []
        const sizes = []

        results.forEach((r) => {
            // Use standard deviation / simple projection of the high-dimensional array
            const vec = r.vector
            if (vec && vec.length > 0) {
                // Simple 2D projection using first two components 
                // Not a real PCA but good enough for visual demo
                const valX = vec[0]
                const valY = vec[1]

                x.push(valX * 100)
                y.push(valY * 100)
                texts.push(`${r.text.substring(0, 30)}...`)
                colors.push(r.similarity)
                sizes.push(r.similarity * 20 + 5) // Scale based on similarity
            }
        })

        if (x.length === 0) return null

        return [
            {
                x,
                y,
                mode: 'markers+text',
                type: 'scatter',
                marker: {
                    size: sizes,
                    color: colors,
                    colorscale: 'Viridis',
                    showscale: true,
                    colorbar: { title: 'Similarity' }
                },
                text: texts,
                textposition: 'top center',
                hoverinfo: 'text'
            }
        ]
    }, [results])

    return (
        <div className="flex flex-col h-full bg-slate-900">
            <div className="p-6 border-b border-slate-800 bg-slate-800/20">
                <h3 className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
                    Embedding 2D Projection
                </h3>
                <p className="text-slate-400 text-sm mt-1">
                    Visualizing the returned documents in vector space based on the first two dimensions
                </p>
            </div>

            <div className="flex-1 min-h-[500px] relative p-4 bg-slate-950/50">
                {!results?.length ? (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                        Search for documents to see their vector positions.
                    </div>
                ) : !plotData ? (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                        Vector data missing.
                    </div>
                ) : (
                    <Plot
                        data={plotData}
                        layout={{
                            autosize: true,
                            margin: { t: 40, r: 40, b: 40, l: 40 },
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            font: { color: '#94a3b8' },
                            xaxis: {
                                showgrid: true,
                                gridcolor: 'rgba(51, 65, 85, 0.5)',
                                zeroline: true,
                                zerolinecolor: 'rgba(99, 102, 241, 0.5)'
                            },
                            yaxis: {
                                showgrid: true,
                                gridcolor: 'rgba(51, 65, 85, 0.5)',
                                zeroline: true,
                                zerolinecolor: 'rgba(99, 102, 241, 0.5)'
                            },
                            hovermode: 'closest'
                        }}
                        useResizeHandler={true}
                        style={{ width: '100%', height: '100%' }}
                        config={{ displayModeBar: false, responsive: true }}
                    />
                )}
            </div>
        </div>
    )
}
