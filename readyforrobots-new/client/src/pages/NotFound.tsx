import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, Home } from "lucide-react";
import { useLocation } from "wouter";
import Header from "@/components/Header";
import SiteFooter from "@/components/layout/SiteFooter";

export default function NotFound() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Header />
      <main className="flex-1 flex items-center justify-center px-4 pt-24 pb-16">
        <Card className="w-full max-w-lg shadow-sm border border-gray-200 bg-white">
          <CardContent className="pt-8 pb-8 text-center">
            <div className="flex justify-center mb-6">
              <div className="relative">
                <div className="absolute inset-0 bg-emerald-100 rounded-full animate-pulse" />
                <AlertCircle className="relative h-16 w-16 text-emerald-600" />
              </div>
            </div>

            <h1 className="font-display text-4xl font-bold text-gray-900 mb-2">
              404
            </h1>
            <h2 className="text-xl font-semibold text-gray-700 mb-4">
              Page Not Found
            </h2>
            <p className="text-gray-600 mb-8 leading-relaxed">
              Sorry, the page you are looking for doesn&apos;t exist.
              <br />
              It may have been moved or deleted.
            </p>

            <Button
              onClick={() => setLocation("/")}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-xl"
            >
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Button>
          </CardContent>
        </Card>
      </main>
      <SiteFooter />
    </div>
  );
}
