import { useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export default function App() {
  const [step, setStep] = useState(0)
  const [token, setToken] = useState('')
  const [qrCode, setQrCode] = useState('')
  const [documents, setDocuments] = useState([])
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const steps = ['Home', 'QR Code', 'Documents', 'Extract', 'Results']

  const generateQR = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${API_URL}/qr/generate`)
      setToken(response.data.token)
      setQrCode(response.data.qr_code)
      setStep(1)
    } catch (err) {
      setError('Failed to generate QR code: ' + (err.response?.data?.detail || err.message))
    }
    setLoading(false)
  }

  const retrieveDocuments = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${API_URL}/retrieval/documents?token=${token}`)
      setDocuments(response.data.documents)
      setStep(2)
    } catch (err) {
      setError('Failed to retrieve documents: ' + (err.response?.data?.detail || err.message))
    }
    setLoading(false)
  }

  const extractData = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${API_URL}/extraction/extract?token=${token}`, {
        documents: documents.map(d => ({
          id: d.id,
          type: d.type,
          content: d.content,
          source: d.source
        }))
      })
      setStep(3)
    } catch (err) {
      setError('Failed to extract data: ' + (err.response?.data?.detail || err.message))
    }
    setLoading(false)
  }

  const analyzeFindings = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await axios.post(`${API_URL}/reconciliation/analyze?token=${token}`, {
        documents: documents.map(d => ({
          id: d.id,
          type: d.type,
          content: d.content,
          source: d.source
        }))
      })
      setFindings(response.data.findings)
      setStep(4)
    } catch (err) {
      setError('Failed to analyze findings: ' + (err.response?.data?.detail || err.message))
    }
    setLoading(false)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-indigo-600 mb-4">Billopsy</h1>
          <div className="flex gap-2">
            {steps.map((s, i) => (
              <button
                key={i}
                onClick={() => setStep(i)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  step === i
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {i + 1}. {s}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        {/* Step 0: Home */}
        {step === 0 && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-3xl font-bold mb-4 text-gray-800">Healthcare Bill Reconciliation</h2>
            <p className="text-gray-600 mb-6 text-lg">
              Analyze your hospital bills for discrepancies and undocumented charges.
            </p>
            <button
              onClick={generateQR}
              disabled={loading}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Generating...' : 'Start Analysis'}
            </button>
          </div>
        )}

        {/* Step 1: QR Code */}
        {step === 1 && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">QR Code Generated</h2>
            {qrCode && (
              <img
                src={`data:image/png;base64,${qrCode}`}
                alt="QR Code"
                className="mx-auto mb-4 w-64 h-64 border-2 border-indigo-600"
              />
            )}
            <p className="text-gray-600 mb-6">Token: {token.substring(0, 20)}...</p>
            <button
              onClick={retrieveDocuments}
              disabled={loading}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Retrieving...' : 'Retrieve Documents'}
            </button>
          </div>
        )}

        {/* Step 2: Documents */}
        {step === 2 && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Documents Retrieved</h2>
            <div className="space-y-4 mb-6">
              {documents.map(doc => (
                <div key={doc.id} className="border-l-4 border-indigo-600 p-4 bg-indigo-50 rounded">
                  <h3 className="font-semibold text-lg">{doc.type}</h3>
                  <p className="text-gray-600">Source: {doc.source}</p>
                  <p className="text-sm text-gray-500 mt-2">{doc.content.substring(0, 150)}...</p>
                </div>
              ))}
            </div>
            <button
              onClick={extractData}
              disabled={loading}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Extracting...' : 'Extract Data'}
            </button>
          </div>
        )}

        {/* Step 3: Extract */}
        {step === 3 && (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <h2 className="text-2xl font-bold mb-4">Data Extracted</h2>
            <p className="text-gray-600 mb-6">
              Successfully extracted information from {documents.length} documents.
            </p>
            <button
              onClick={analyzeFindings}
              disabled={loading}
              className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 disabled:opacity-50"
            >
              {loading ? 'Analyzing...' : 'Analyze Findings'}
            </button>
          </div>
        )}

        {/* Step 4: Results */}
        {step === 4 && (
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>
            {findings.length > 0 ? (
              <div className="space-y-4">
                {findings.map((finding, i) => (
                  <div
                    key={i}
                    className={`border-l-4 p-4 rounded ${
                      finding.severity === 'High'
                        ? 'border-red-600 bg-red-50'
                        : finding.severity === 'Medium'
                        ? 'border-yellow-600 bg-yellow-50'
                        : 'border-green-600 bg-green-50'
                    }`}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{finding.category}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        finding.severity === 'High'
                          ? 'bg-red-200 text-red-800'
                          : finding.severity === 'Medium'
                          ? 'bg-yellow-200 text-yellow-800'
                          : 'bg-green-200 text-green-800'
                      }`}>
                        {finding.severity}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-2">{finding.description}</p>
                    <p className="text-sm text-gray-600 mb-2">
                      <strong>Evidence:</strong> {finding.evidence}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Question:</strong> {finding.suggested_question}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-600">No findings to display.</p>
            )}
            <button
              onClick={() => setStep(0)}
              className="mt-6 bg-gray-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-gray-700"
            >
              Start New Analysis
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
