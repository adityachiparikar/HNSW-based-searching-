import { useState } from 'react'
import axios from 'axios'

// Prefer IPv4 loopback to avoid some Windows setups resolving `localhost` to IPv6 (`::1`)
// while the backend binds only on IPv4.
const API_URL = 'http://127.0.0.1:8002'

export default function UploadDataset({ onUploadSuccess }) {
    const [file, setFile] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [success, setSuccess] = useState(null)

    const handleFileChange = (e) => {
        setFile(e.target.files[0])
        setError(null)
        setSuccess(null)
    }

    const handleUpload = async (e) => {
        e.preventDefault()
        if (!file) return

        setLoading(true)
        setError(null)
        setSuccess(null)

        const formData = new FormData()
        formData.append('file', file)

        try {
            const res = await axios.post(`${API_URL}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
            if (res.data.error) {
                setError(res.data.error)
            } else {
                setSuccess(res.data.message)
                setFile(null)
                onUploadSuccess()
            }
        } catch (err) {
            setError('Upload failed: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    const loadSampleData = async () => {
        setLoading(true)
        setError(null)
        setSuccess(null)

        try {
            const res = await axios.post(`${API_URL}/sample_data`)
            setSuccess(res.data.message)
            onUploadSuccess()
        } catch (err) {
            setError('Failed to load sample data: ' + err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800 shadow-xl">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-indigo-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
                Dataset Upload
            </h2>

            <form onSubmit={handleUpload} className="space-y-4">
                <div>
                    <label className="block text-sm font-medium text-slate-400 mb-2">
                        Upload JSON or CSV file
                    </label>
                    <div className="flex items-center justify-center w-full">
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-slate-700 border-dashed rounded-lg cursor-pointer bg-slate-800/50 hover:bg-slate-800 hover:border-indigo-500/50 transition-all">
                            <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                <svg className="w-8 h-8 mb-3 text-indigo-400/80" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                                </svg>
                                <p className="mb-2 text-sm text-slate-400">
                                    <span className="font-semibold text-indigo-400">Click to upload</span> or drag and drop
                                </p>
                                <p className="text-xs text-slate-500">JSON or CSV (max. 10MB)</p>
                                {file && <p className="mt-2 text-xs font-semibold text-emerald-400">{file.name}</p>}
                            </div>
                            <input type="file" className="hidden" accept=".json,.csv" onChange={handleFileChange} />
                        </label>
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={!file || loading}
                    className="w-full text-white bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-700 disabled:text-slate-400 disabled:cursor-not-allowed font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-colors"
                >
                    {loading ? 'Loading Dataset...' : 'Upload Dataset'}
                </button>
            </form>

            <div className="relative flex items-center py-5">
                <div className="flex-grow border-t border-slate-700"></div>
                <span className="flex-shrink-0 mx-4 text-slate-500 text-xs text-uppercase">or</span>
                <div className="flex-grow border-t border-slate-700"></div>
            </div>

            <button
                onClick={loadSampleData}
                disabled={loading}
                className="w-full text-indigo-300 border border-indigo-600 hover:bg-indigo-600 hover:text-white disabled:bg-transparent disabled:text-slate-400 disabled:border-slate-700 disabled:cursor-not-allowed font-medium rounded-lg text-sm px-5 py-2.5 text-center transition-all bg-indigo-600/10"
            >
                Load Sample Data
            </button>

            {error && (
                <div className="mt-4 p-3 text-sm text-red-400 bg-red-900/30 rounded-lg border border-red-900 overflow-hidden break-words">
                    {error}
                </div>
            )}

            {success && (
                <div className="mt-4 p-3 text-sm text-emerald-400 bg-emerald-900/30 rounded-lg border border-emerald-900">
                    {success}
                </div>
            )}
        </div>
    )
}
