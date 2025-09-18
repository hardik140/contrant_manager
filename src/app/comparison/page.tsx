"use client"

import { useEffect, useState } from "react"
import { GitCompare, Loader2, ArrowLeft, Download, FileText, Shield, AlertTriangle, CheckCircle } from "lucide-react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"

const PolicyCategories = {
  COMPANIES_ACT: "companies_act",
  BANKING: "banking",
  DATA_PROTECTION: "data_protection",
  EMPLOYMENT: "employment",
  REGULATORY: "regulatory"
} as const;

type PolicyCategory = typeof PolicyCategories[keyof typeof PolicyCategories];

interface Policy {
  id: string
  name: string
  category: PolicyCategory
  description: string
  file_path: string
  metadata?: {
    jurisdiction?: string
    last_updated?: string
    key_areas?: string[]
    regulators?: string[]
    frameworks?: string[]
    scope?: string
    status?: "Pending" | "Active"
    note?: string
  }
}

// Helper function to format category names
const formatCategoryName = (category: PolicyCategory): string => {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

interface ComparisonResult {
  compliance_analysis: {
    compliance_summary: string
    violations: Array<{
      policy_clause: string
      violation: string
      suggested_fix: string
    }>
  }
  analysis_metrics: {
    text_metrics: {
      contract: {
        original_length: number
        normalized_length?: number
        characters_cleaned?: number
        dates_standardized?: number
      }
      policy: {
        original_length: number
        normalized_length?: number
        characters_cleaned?: number
        dates_standardized?: number
      }
    }
    semantic_similarity: {
      overall_similarity: number
      matching_sections: Array<{
        policy_text: string
        contract_text: string
        similarity_score: number
      }>
    }
  }
  full_report?: string  // New field for the detailed report
}

export default function ComparisonPage() {
  const [contractFile, setContractFile] = useState<File | null>(null)
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null)
  const [availablePolicies, setAvailablePolicies] = useState<Policy[]>([])
  const [isProcessing, setIsProcessing] = useState(false)
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null)
  const [error, setError] = useState("")
  const [activeTab, setActiveTab] = useState("comparison")

  const [isLoadingPolicies, setIsLoadingPolicies] = useState(true);

  useEffect(() => {
    // Fetch available policies when component mounts
    const fetchPolicies = async () => {
      try {
        setIsLoadingPolicies(true);
        setError("");
        
        const response = await fetch("http://localhost:8000/api/policies/", {
          method: "GET",
          headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
          },
          cache: "no-cache",
        });

        if (!response.ok) {
          let errorMessage = "Failed to fetch policies";
          try {
            const errorData = await response.json();
            errorMessage = errorData.detail || errorMessage;
          } catch (e) {
            console.error("Error parsing error response:", e);
          }
          throw new Error(errorMessage);
        }
        
        const data = await response.json();
        if (!data || !data.policies) {
          console.error("Invalid response format:", data);
          throw new Error("Invalid response format from server");
        }
        
        // Validate and normalize policies
        const validPolicies = data.policies.filter((policy: Policy) => {
          // Ensure the policy has a valid category that matches our enum
          return Object.values(PolicyCategories).includes(policy.category);
        });

        // Use a Map to deduplicate policies by ID
        const uniquePolicies = new Map();
        validPolicies.forEach((policy: Policy) => {
          if (!uniquePolicies.has(policy.id)) {
            uniquePolicies.set(policy.id, policy);
          }
        });
        
        setAvailablePolicies(Array.from(uniquePolicies.values()));
        setError("");
      } catch (err) {
        console.error("Policy fetch error:", err);
        setError("Failed to load available policies. Please try again later.")
      } finally {
        setIsLoadingPolicies(false)
      }
    }
    fetchPolicies()
  }, [])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      const allowedTypes = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ]

      if (allowedTypes.includes(selectedFile.type)) {
        setContractFile(selectedFile)
        setError("")
      } else {
        setError("Please upload a PDF or Word document")
      }
    }
  }

  const handleCompare = async () => {
    if (!contractFile || !selectedPolicy) {
      setError("Please select both a contract file and a policy")
      return
    }

    setIsProcessing(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("contract", contractFile)
      formData.append("policy_id", selectedPolicy.id)

      const response = await fetch("http://localhost:8000/api/compare/", {
        method: "POST",
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to process documents")
      }

      const data = await response.json()
      setComparisonResult(data.comparison)
      setActiveTab("comparison")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process documents")
    } finally {
      setIsProcessing(false)
    }
  }

  const downloadResults = () => {
    if (!comparisonResult) return

    const content = JSON.stringify(comparisonResult, null, 2)
    const blob = new Blob([content], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `compliance_analysis_${Date.now()}.json`
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
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">Policy Compliance Check</h1>
          <p className="text-gray-600">Compare contracts against standard policies to ensure compliance</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Input Section */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Upload Documents</CardTitle>
                <CardDescription>Select a contract and policy to compare</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Contract Upload */}
                <div>
                  <label className="block text-sm font-medium mb-2">Contract Document</label>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() => document.getElementById("contract-upload")?.click()}
                    >
                      <FileText className="w-4 h-4 mr-2" />
                      Select Contract
                    </Button>
                    {contractFile && (
                      <Badge variant="secondary">{contractFile.name}</Badge>
                    )}
                  </div>
                  <input
                    id="contract-upload"
                    type="file"
                    className="hidden"
                    accept=".pdf,.doc,.docx"
                    onChange={handleFileUpload}
                  />
                </div>

                {/* Policy Selection */}
                <div className="space-y-4">
                  <label className="block text-sm font-medium">Select Compliance Policy</label>
                  
                  {isLoadingPolicies ? (
                    <div className="py-8 flex flex-col items-center space-y-2">
                      <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                      <p className="text-sm text-gray-500">Loading available policies...</p>
                    </div>
                  ) : error ? (
                    <Alert variant="destructive">
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  ) : availablePolicies.length === 0 ? (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>No policies available at the moment.</AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-4">
                      {Object.values(PolicyCategories).map((category) => {
                        // Filter policies by exact category match
                        const policies = availablePolicies.filter(p => p.category === category);
                        if (policies.length === 0) return null;

                        return (
                          <div key={`category-${category}`} className="space-y-2">
                            <h3 className="text-lg font-medium text-gray-900">
                              {category.split('_').map(word => 
                                word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
                              ).join(' ')}
                            </h3>
                            <div className="grid grid-cols-1 gap-2">
                              {policies.map((policy) => (
                                <Button
                                  key={policy.id}
                                  variant={selectedPolicy?.id === policy.id ? "default" : "outline"}
                                  className="w-full justify-start h-auto p-4"
                                  onClick={() => setSelectedPolicy(policy)}
                                >
                                  <div className="flex flex-col items-start text-left w-full">
                                    <div className="flex items-center justify-between w-full mb-1">
                                      <span className="font-medium">{policy.name}</span>
                                      {policy.metadata?.status === 'Pending' ? (
                                        <Badge variant="secondary">Pending</Badge>
                                      ) : (
                                        <Badge>{policy.metadata?.jurisdiction || 'General'}</Badge>
                                      )}
                                    </div>
                                    <span className="text-sm text-gray-500">
                                      {policy.metadata?.status === 'Pending'
                                        ? policy.metadata.note || 'This policy will be available soon'
                                        : policy.description}
                                    </span>
                                    {policy.metadata?.key_areas && (
                                      <div className="flex flex-wrap gap-1 mt-2">
                                        {policy.metadata.key_areas.map((area) => (
                                          <Badge key={area} variant="secondary">
                                            {area}
                                          </Badge>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </Button>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Selected Policy Details */}
                  {selectedPolicy && (
                    <div className="mt-4 p-4 bg-gray-50 rounded-lg space-y-2">
                      <h4 className="font-medium text-sm">Selected Policy Details</h4>
                      {selectedPolicy.metadata?.key_areas && (
                        <div className="flex flex-wrap gap-1">
                          {selectedPolicy.metadata.key_areas.map((area) => (
                            <Badge key={area} variant="secondary">
                              {area}
                            </Badge>
                          ))}
                        </div>
                      )}
                      {selectedPolicy.metadata?.last_updated && (
                        <p className="text-xs text-gray-500">
                          Last Updated: {selectedPolicy.metadata.last_updated}
                        </p>
                      )}
                    </div>
                  )}
                </div>

                {/* Compare Button */}
                <Button
                  className="w-full"
                  onClick={handleCompare}
                  disabled={isProcessing || !contractFile || !selectedPolicy}
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <GitCompare className="w-4 h-4 mr-2" />
                      Compare Documents
                    </>
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {comparisonResult && (
              <Card>
                <CardHeader className="flex-row items-center justify-between">
                  <div>
                    <CardTitle>Analysis Results</CardTitle>
                    <CardDescription>
                      Compliance check completed
                    </CardDescription>
                  </div>
                  <Button variant="outline" onClick={downloadResults}>
                    <Download className="w-4 h-4 mr-2" />
                    Download Report
                  </Button>
                </CardHeader>
                <CardContent>
                  <Tabs value={activeTab} onValueChange={setActiveTab}>
                    <TabsList className="grid w-full grid-cols-3">
                      <TabsTrigger value="comparison">Comparison</TabsTrigger>
                      <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
                      <TabsTrigger value="full-report">Full Report</TabsTrigger>
                    </TabsList>

                    {/* Comparison Tab */}
                    <TabsContent value="comparison">
                      <div className="space-y-4">
                        <Alert>
                          <CheckCircle className="h-4 w-4" />
                          <AlertDescription>
                            {comparisonResult?.compliance_analysis?.compliance_summary || 
                             "Analysis complete. See full report for details."}
                          </AlertDescription>
                        </Alert>

                        <div className="space-y-2">
                          <h3 className="text-lg font-semibold">Similarity Metrics</h3>
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <p className="text-sm font-medium">Overall Similarity</p>
                              <p className="text-2xl font-bold">
                                {Math.round((comparisonResult?.analysis_metrics?.semantic_similarity?.overall_similarity || 0) * 100)}%
                              </p>
                            </div>
                            <div>
                              <p className="text-sm font-medium">Matching Sections</p>
                              <p className="text-2xl font-bold">
                                {comparisonResult?.analysis_metrics?.semantic_similarity?.matching_sections?.length || 0}
                              </p>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TabsContent>

                    {/* Suggestions Tab */}
                    <TabsContent value="suggestions">
                      <div className="space-y-4">
                        {comparisonResult?.compliance_analysis?.violations?.map((violation, index) => (
                          <Card key={index}>
                            <CardHeader>
                              <CardTitle className="text-base">Policy Requirement</CardTitle>
                              <CardDescription>{violation.policy_clause}</CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                              <div>
                                <h4 className="font-medium mb-1">Issue</h4>
                                <p className="text-sm text-red-600">{violation.violation}</p>
                              </div>
                              <div>
                                <h4 className="font-medium mb-1">Suggested Fix</h4>
                                <p className="text-sm text-green-600">{violation.suggested_fix}</p>
                              </div>
                            </CardContent>
                          </Card>
                        ))}

                        {(!comparisonResult?.compliance_analysis?.violations || comparisonResult.compliance_analysis.violations.length === 0) && (
                          <Alert>
                            <CheckCircle className="h-4 w-4 text-green-500" />
                            <AlertDescription>
                              No compliance violations found. The contract appears to be fully compliant with the selected policy.
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    </TabsContent>

                    {/* Full Report Tab */}
                    <TabsContent value="full-report">
                      <div className="space-y-4">
                        <Alert>
                          <FileText className="h-4 w-4" />
                          <AlertDescription>
                            Full analysis report from AI
                          </AlertDescription>
                        </Alert>
                        <div className="p-4 bg-gray-50 rounded-md whitespace-pre-wrap font-mono text-sm">
                          {comparisonResult.full_report || "Detailed report not available"}
                        </div>
                      </div>
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
