"use client"

import type React from "react"

import { useState } from "react"
import { Upload, FileText, Loader2, ArrowLeft, Download } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"

export default function SummarizerPage() {
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [summary, setSummary] = useState("")
  const [error, setError] = useState("")

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.document",
      ]

      if (allowedTypes.includes(selectedFile.type)) {
        setFile(selectedFile)
        setError("")
      } else {
        setError("Please upload a PDF, Word document, or Google Docs file")
      }
    }
  }

  const handleSummarize = async () => {
    if (!file) return

    setIsProcessing(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("file", file)

      const response = await fetch("http://localhost:8000/api/upload-contract/", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to process document")
      }

      const data = await response.json()
      setSummary(data.summary)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process document. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const downloadSummary = () => {
    const blob = new Blob([summary], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${file?.name || "contract"}_summary.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Button variant="ghost" asChild className="mb-4">
            <Link href="/">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Contract Summarizer</h1>
          <p className="text-gray-600">Upload your contract document and get an AI-powered summary</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Upload className="w-5 h-5 mr-2" />
                Upload Contract
              </CardTitle>
              <CardDescription>Supported formats: PDF, Word (.doc, .docx), Google Docs</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                <input
                  type="file"
                  id="file-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileUpload}
                />
                <label htmlFor="file-upload" className="cursor-pointer">
                  <FileText className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-gray-600 mb-2">Click to upload or drag and drop</p>
                  <p className="text-sm text-gray-500">Maximum file size: 10MB</p>
                </label>
              </div>

              {file && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <p className="font-medium text-blue-900">Selected file:</p>
                  <p className="text-blue-700">{file.name}</p>
                  <p className="text-sm text-blue-600">Size: {(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button onClick={handleSummarize} disabled={!file || isProcessing} className="w-full" size="lg">
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4 mr-2" />
                    Generate Summary
                  </>
                )}
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Contract Summary
                {summary && (
                  <Button variant="outline" size="sm" onClick={downloadSummary}>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                )}
              </CardTitle>
              <CardDescription>AI-generated summary of your contract</CardDescription>
            </CardHeader>
            <CardContent>
              {summary ? (
                <div className="space-y-4">
                  <Textarea value={summary} readOnly className="min-h-[400px] resize-none" />
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Upload a contract to see the summary here</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
