import SiteShell from "@/components/SiteShell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { getApiBase, liveFetchInit } from "@/lib/apiBase";
import { useState } from "react";

const INDUSTRIES = [
  "Hospitality (Hotels/Resorts)",
  "Healthcare (Hospitals/Clinics)",
  "Logistics/Warehousing",
  "Food Service/Restaurants",
  "Airports/Transportation",
  "Retail",
  "Manufacturing",
  "Real Estate/Facilities",
  "New",
];

const INDUSTRY_BENCHMARKS: Record<string, { avgCost: number; avgPayback: number; adoptionRate: number }> = {
  "Hospitality (Hotels/Resorts)": { avgCost: 28000, avgPayback: 8.5, adoptionRate: 42 },
  "Healthcare (Hospitals/Clinics)": { avgCost: 35000, avgPayback: 9.2, adoptionRate: 38 },
  "Logistics/Warehousing": { avgCost: 45000, avgPayback: 7.1, adoptionRate: 61 },
  "Food Service/Restaurants": { avgCost: 22000, avgPayback: 11.3, adoptionRate: 28 },
  "Airports/Transportation": { avgCost: 38000, avgPayback: 8.8, adoptionRate: 45 },
  Retail: { avgCost: 25000, avgPayback: 10.2, adoptionRate: 31 },
  Manufacturing: { avgCost: 52000, avgPayback: 6.5, adoptionRate: 67 },
  "Real Estate/Facilities": { avgCost: 30000, avgPayback: 9.5, adoptionRate: 35 },
  New: { avgCost: 30000, avgPayback: 9.0, adoptionRate: 40 },
};

type Results = {
  robotCost: number;
  annualLaborReplaced: number;
  annualMaintenance: number;
  annualSavings: number;
  paybackMonths: number;
  roi1Year: number;
  roi3Year: number;
  totalSavings3Year: number;
  industry: string;
  benchmark: (typeof INDUSTRY_BENCHMARKS)[string] | null;
};

export default function RoiCalculator() {
  const [robotType, setRobotType] = useState("");
  const [robotCost, setRobotCost] = useState("");
  const [industry, setIndustry] = useState("");
  const [laborMode, setLaborMode] = useState<"hourly" | "annual">("hourly");
  const [hoursPerDay, setHoursPerDay] = useState("");
  const [hourlyWage, setHourlyWage] = useState("");
  const [annualLaborCost, setAnnualLaborCost] = useState("");
  const [results, setResults] = useState<Results | null>(null);

  function calculateROI() {
    const cost = parseFloat(robotCost);
    if (!cost || cost <= 0) return;

    let annualLabor = 0;
    if (laborMode === "hourly") {
      const hours = parseFloat(hoursPerDay) || 0;
      const wage = parseFloat(hourlyWage) || 0;
      annualLabor = hours * wage * 365;
    } else {
      annualLabor = parseFloat(annualLaborCost) || 0;
    }
    if (annualLabor <= 0) return;

    const annualMaintenance = cost * 0.1;
    const annualSavings = annualLabor - annualMaintenance;
    const paybackMonths = (cost / annualSavings) * 12;
    const roi1Year = ((annualSavings - cost) / cost) * 100;
    const roi3Year = (((annualSavings * 3) - cost) / cost) * 100;
    const totalSavings3Year = annualSavings * 3 - cost;
    const benchmark = industry ? INDUSTRY_BENCHMARKS[industry] ?? null : null;

    setResults({
      robotCost: cost,
      annualLaborReplaced: annualLabor,
      annualMaintenance,
      annualSavings,
      paybackMonths,
      roi1Year,
      roi3Year,
      totalSavings3Year,
      industry,
      benchmark,
    });

    void fetch(`${getApiBase()}/api/track/roi-calculation`, {
      ...liveFetchInit({
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          robot_type: robotType,
          robot_cost: cost,
          industry,
          payback_months: paybackMonths,
          annual_savings: annualSavings,
        }),
      }),
    }).catch(() => {});
  }

  return (
    <SiteShell>
      <div className="container py-8 md:py-10 max-w-2xl space-y-8">
        <div>
          <h1
            className="text-3xl md:text-4xl font-extrabold text-gray-900 tracking-tight"
            style={{ fontFamily: "'Plus Jakarta Sans', system-ui, sans-serif" }}
          >
            ROI calculator
          </h1>
          <p className="text-gray-600 mt-1 text-sm">
            Same payback math as the legacy tool: labor replaced minus maintenance, then simple ROI at 1 and 3 years.
          </p>
        </div>

        <Card className="border-gray-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Inputs</CardTitle>
            <CardDescription>Maintenance modeled at 10% of robot cost per year.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>Robot type (optional)</Label>
              <Input value={robotType} onChange={(e) => setRobotType(e.target.value)} placeholder="e.g. AMR fleet" />
            </div>
            <div className="space-y-2">
              <Label>Robot cost (USD)</Label>
              <Input value={robotCost} onChange={(e) => setRobotCost(e.target.value)} type="number" min={0} />
            </div>
            <div className="space-y-2">
              <Label>Industry (benchmarks)</Label>
              <Select value={industry || undefined} onValueChange={setIndustry}>
                <SelectTrigger>
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map((i) => (
                    <SelectItem key={i} value={i}>
                      {i}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Labor basis</Label>
              <Select value={laborMode} onValueChange={(v) => setLaborMode(v as "hourly" | "annual")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="hourly">Hourly wage × hours/day</SelectItem>
                  <SelectItem value="annual">Annual labor cost</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {laborMode === "hourly" ? (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-2">
                  <Label>Hours / day</Label>
                  <Input value={hoursPerDay} onChange={(e) => setHoursPerDay(e.target.value)} type="number" />
                </div>
                <div className="space-y-2">
                  <Label>Hourly wage (USD)</Label>
                  <Input value={hourlyWage} onChange={(e) => setHourlyWage(e.target.value)} type="number" />
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Annual labor replaced (USD)</Label>
                <Input value={annualLaborCost} onChange={(e) => setAnnualLaborCost(e.target.value)} type="number" />
              </div>
            )}
            <Button type="button" onClick={calculateROI} style={{ backgroundColor: "oklch(0.527 0.154 162.5)" }}>
              Calculate
            </Button>
          </CardContent>
        </Card>

        {results ? (
          <Card className="border-emerald-100 bg-emerald-50/40 shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Results</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm text-gray-800">
              <p>
                <strong>Payback:</strong> {results.paybackMonths.toFixed(1)} months
              </p>
              <p>
                <strong>Annual savings (after maintenance):</strong> ${Math.round(results.annualSavings).toLocaleString()}
              </p>
              <p>
                <strong>1-year ROI:</strong> {results.roi1Year.toFixed(1)}%
              </p>
              <p>
                <strong>3-year ROI:</strong> {results.roi3Year.toFixed(1)}% — net ${Math.round(results.totalSavings3Year).toLocaleString()}
              </p>
              {results.benchmark ? (
                <p className="text-xs text-gray-600 pt-2 border-t border-emerald-200/80">
                  Benchmark for {results.industry || "vertical"}: typical hardware ~${results.benchmark.avgCost.toLocaleString()}, avg
                  payback ~{results.benchmark.avgPayback} mo, adoption ~{results.benchmark.adoptionRate}%.
                </p>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </div>
    </SiteShell>
  );
}
