"use client"

import type React from "react"

import { useState } from "react"
import { GitCompare, Loader2, ArrowLeft, Download, FileText, Shield } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"

export default function ComparisonPage() {
  const [contractFile, setContractFile] = useState<File | null>(null)
  const [policyFile, setPolicyFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [comparison, setComparison] = useState("")
  const [error, setError] = useState("")

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>, type: "contract" | "policy") => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.google-apps.document",
      ]

      if (allowedTypes.includes(selectedFile.type)) {
        if (type === "contract") {
          setContractFile(selectedFile)
        } else {
          setPolicyFile(selectedFile)
        }
        setError("")
      } else {
        setError("Please upload a PDF, Word document, or Google Docs file")
      }
    }
  }

  const handleCompare = async () => {
    if (!contractFile || !policyFile) return

    setIsProcessing(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("contract", contractFile)
      formData.append("policy", policyFile)

      const response = await fetch("/api/compare", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        throw new Error("Failed to process documents")
      }

      const data = await response.json()
      setComparison(data.comparison)
    } catch (err) {
      setError("Failed to process documents. Please try again.")
    } finally {
      setIsProcessing(false)
    }
  }

  const downloadComparison = () => {
    const blob = new Blob([comparison], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `policy_comparison_${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <Button variant="ghost" asChild className="mb-4">
            <Link href="/">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Link>
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Policy Comparison</h1>
          <p className="text-gray-600">Compare contracts against your company policies to ensure compliance</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <FileText className="w-5 h-5 mr-2 text-blue-600" />
                Contract Document
              </CardTitle>
              <CardDescription>Upload the contract to analyze</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                <input
                  type="file"
                  id="contract-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => handleFileUpload(e, "contract")}
                />
                <label htmlFor="contract-upload" className="cursor-pointer">
                  <FileText className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">Upload Contract</p>
                </label>
              </div>

              {contractFile && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="font-medium text-blue-900 text-sm">Contract:</p>
                  <p className="text-blue-700 text-sm truncate">{contractFile.name}</p>
                  <Badge variant="secondary" className="mt-1">
                    {(contractFile.size / 1024 / 1024).toFixed(2)} MB
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Shield className="w-5 h-5 mr-2 text-green-600" />
                Policy Document
              </CardTitle>
              <CardDescription>Upload your company policy</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-green-400 transition-colors">
                <input
                  type="file"
                  id="policy-upload"
                  className="hidden"
                  accept=".pdf,.doc,.docx"
                  onChange={(e) => handleFileUpload(e, "policy")}
                />
                <label htmlFor="policy-upload" className="cursor-pointer">
                  <Shield className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">Upload Policy</p>
                </label>
              </div>

              {policyFile && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <p className="font-medium text-green-900 text-sm">Policy:</p>
                  <p className="text-green-700 text-sm truncate">{policyFile.name}</p>
                  <Badge variant="secondary" className="mt-1">
                    {(policyFile.size / 1024 / 1024).toFixed(2)} MB
                  </Badge>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
              <CardDescription>Compare documents for compliance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <Button
                onClick={handleCompare}
                disabled={!contractFile || !policyFile || isProcessing}
                className="w-full bg-green-600 hover:bg-green-700"
                size="lg"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Comparing...
                  </>
                ) : (
                  <>
                    <GitCompare className="w-4 h-4 mr-2" />
                    Compare Documents
                  </>
                )}
              </Button>

              {comparison && (
                <Button variant="outline" onClick={downloadComparison} className="w-full bg-transparent">
                  <Download className="w-4 h-4 mr-2" />
                  Download Report
                </Button>
              )}
            </CardContent>
          </Card>
        </div>

        {comparison && (
          <Card className="mt-8">
            <CardHeader>
              <CardTitle className="flex items-center">
                <GitCompare className="w-5 h-5 mr-2" />
                Comparison Analysis
              </CardTitle>
              <CardDescription>AI-powered policy compliance analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea value={comparison} readOnly className="min-h-[400px] resize-none" />
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
