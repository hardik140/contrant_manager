import { Loader2 } from "lucide-react"

interface LoadingSpinnerProps {
  message?: string
}

export function LoadingSpinner({ message = "Processing..." }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8">
      <Loader2 className="w-8 h-8 animate-spin text-blue-600 mb-4" />
      <p className="text-gray-600">{message}</p>
    </div>
  )
}
