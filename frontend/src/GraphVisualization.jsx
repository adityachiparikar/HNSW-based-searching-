import { useState, useMemo } from 'react'
import Plot from 'react-plotly.js'

export default function GraphVisualization({ stats }) {
    const [activeLayer, setActiveLayer] = useState(0)

    // Compute graph data for Plotly
    const plotData = useMemo(() => {
        if (!stats || !stats.graph_structure || stats.graph_structure.length === 0) return null

        const layerData = stats.graph_structure.find(l => l.layer === activeLayer) || stats.graph_structure[0]

        if (!layerData || layerData.nodes.length === 0) return null

        // Generate random 2D positions for nodes to visualize structure (since we don't return vectors in stats)
        // To make it look consistent, we use pseudo-random based on node ID
        const positions = {}
        layerData.nodes.forEach((node) => {
            // Simple pseudo-random distribution
            const r = (Math.sin(node * node * 123.456) * 10000 % 1)
            const r2 = (Math.cos(node * node * 123.456) * 10000 % 1)

            positions[node] = {
                x: r * 10,
                y: r2 * 10
            }
        })

        const node_x = []
        const node_y = []
        const text_labels = []

        layerData.nodes.forEach(node => {
            node_x.push(positions[node].x)
            node_y.push(positions[node].y)
            text_labels.push(`Node ID: ${node}`)
        })

        const edge_x = []
        const edge_y = []

        layerData.edges.forEach(([source, target]) => {
            if (positions[source] && positions[target]) {
                edge_x.push(positions[source].x, positions[target].x, null)
                edge_y.push(positions[source].y, positions[target].y, null)
            }
        })

        return [
            {
                x: edge_x,
                y: edge_y,
                mode: 'lines',
                type: 'scatter',
                line: { color: 'rgba(99, 102, 241, 0.3)', width: 1 },
                hoverinfo: 'none'
            },
            {
                x: node_x,
                y: node_y,
                mode: 'markers+text',
                type: 'scatter',
                marker: {
                    size: 10,
                    color: layerData.layer === 0 ? '#ec4899' : '#8b5cf6', // Pink for base layer, purple for higher
                    line: { color: '#ffffff', width: 1 }
                },
                text: text_labels,
                textposition: 'top center',
                hoverinfo: 'text'
            }
        ]
    }, [stats, activeLayer])

    return (
        <div className="flex flex-col h-full">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-800/20">
                <div>
                    <h3 className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-slate-100 to-slate-400">
                        HNSW Graph Structure
                    </h3>
                    <p className="text-slate-400 text-sm mt-1">Hierarchical Navigable Small World</p>
                </div>

                {stats && stats.graph_structure && (
                    <div className="flex gap-2">
                        {stats.graph_structure.map(layer => (
                            <button
                                key={layer.layer}
                                onClick={() => setActiveLayer(layer.layer)}
                                className={`px-3 py-1 rounded text-sm transition-colors ${activeLayer === layer.layer
                                        ? 'bg-indigo-600 text-white'
                                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                                    }`}
                            >
                                Layer {layer.layer}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="flex-1 min-h-[500px] relative p-4">
                {!stats?.graph_structure?.length ? (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                        No graph data available. Upload dataset first.
                    </div>
                ) : !plotData ? (
                    <div className="absolute inset-0 flex items-center justify-center text-slate-500">
                        No nodes in this layer.
                    </div>
                ) : (
                    <Plot
                        data={plotData}
                        layout={{
                            autosize: true,
                            margin: { t: 0, r: 0, b: 0, l: 0 },
                            paper_bgcolor: 'transparent',
                            plot_bgcolor: 'transparent',
                            xaxis: { showgrid: false, zeroline: false, showticklabels: false },
                            yaxis: { showgrid: false, zeroline: false, showticklabels: false },
                            showlegend: false,
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
