import Link from "next/link"
import { FileText, GitCompare, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">Contract Intelligence Suite</h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Streamline your contract management with AI-powered summarization and policy comparison tools
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-blue-500">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
                <FileText className="w-8 h-8 text-blue-600" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">Contract Summarizer</CardTitle>
              <CardDescription className="text-gray-600">
                Upload your contracts and get AI-powered summaries instantly
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-left space-y-2 mb-6 text-gray-600">
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-blue-500" />
                  Upload PDF, Word, or Google Docs
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-blue-500" />
                  AI-powered contract analysis
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-blue-500" />
                  Key terms and obligations extraction
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-blue-500" />
                  Instant summary generation
                </li>
              </ul>
              <Button asChild className="w-full" size="lg">
                <Link href="/summarizer">
                  Start Summarizing
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </CardContent>
          </Card>

          <Card className="group hover:shadow-xl transition-all duration-300 border-2 hover:border-green-500">
            <CardHeader className="text-center pb-4">
              <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
                <GitCompare className="w-8 h-8 text-green-600" />
              </div>
              <CardTitle className="text-2xl font-bold text-gray-900">Policy Comparison</CardTitle>
              <CardDescription className="text-gray-600">
                Compare contracts against your company policies
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <ul className="text-left space-y-2 mb-6 text-gray-600">
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-green-500" />
                  Upload contract and policy documents
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-green-500" />
                  AI-powered comparison analysis
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-green-500" />
                  Identify policy violations
                </li>
                <li className="flex items-center">
                  <ArrowRight className="w-4 h-4 mr-2 text-green-500" />
                  Compliance recommendations
                </li>
              </ul>
              <Button asChild className="w-full bg-green-600 hover:bg-green-700" size="lg">
                <Link href="/comparison">
                  Start Comparing
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="text-center mt-16">
          <p className="text-gray-500">Powered by Google Gemini AI • Secure • Fast • Reliable</p>
        </div>
      </div>
    </div>
  )
}
