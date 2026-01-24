import { fetchPollutionDataAction, fetchStatesAction } from "@/lib/actions";
import { Header } from "@/components/dashboard/Header";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Factory, Wind } from "lucide-react";

export async function generateStaticParams() {
  const states = await fetchStatesAction();
  const params = [];
  for (const state of states) {
    const data = await fetchPollutionDataAction(state);
    for (const item of data) {
      params.push({
        year: item.year.toString(),
      });
    }
  }
  // Remove duplicates
  return [...new Map(params.map(p => [p.year, p])).values()];
}

export default async function YearPage({ 
  params,
  searchParams,
}: { 
  params: Promise<{ year: string }>,
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { year } = await params;
  const resolvedParams = await searchParams;
  const currentState = (resolvedParams.state as string) || "Delhi";
  
  const [data, allStates] = await Promise.all([
    fetchPollutionDataAction(currentState),
    fetchStatesAction()
  ]);
  
  const yearData = data.find((item) => item.year.toString() === year);

  if (!yearData) {
    notFound();
  }

  const prevYear = data.find(d => d.year === yearData.year - 1);

  const getChange = (current: number, previous?: number) => {
    if (!previous) return null;
    const diff = current - previous;
    const percent = ((diff / previous) * 100).toFixed(1);
    return { diff: diff > 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1), percent };
  };

  return (
    <div className="min-h-screen bg-background">
      <Header states={allStates} currentState={currentState} />
      <main className="container mx-auto p-4 space-y-8">
        <div className="flex items-center gap-4">
          <Link href={`/dashboard?state=${currentState}`}>
            <Button variant="outline" size="icon">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h2 className="text-3xl font-bold tracking-tight">Environmental Data for {year} in {currentState}</h2>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* PM 2.5 Card */}
          <Card className="border-primary/20 shadow-lg hover:shadow-xl transition-all">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">PM 2.5</CardTitle>
                <CardDescription>Particulate Matter (µg/m³)</CardDescription>
              </div>
              <Factory className="h-8 w-8 text-primary opacity-70" />
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-foreground">{yearData.pm25}</div>
              {prevYear && (
                <p className="text-sm text-muted-foreground mt-2">
                  {getChange(yearData.pm25, prevYear.pm25)?.diff} from {prevYear.year}
                </p>
              )}
            </CardContent>
          </Card>

          {/* AOD Card */}
          <Card className="border-primary/20 shadow-lg hover:shadow-xl transition-all">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-lg">Aerosol Optical Depth</CardTitle>
                <CardDescription>AOD Levels</CardDescription>
              </div>
              <Wind className="h-8 w-8 text-primary opacity-70" />
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-foreground">{yearData.aod}</div>
              {prevYear && (
                <p className="text-sm text-muted-foreground mt-2">
                  {getChange(yearData.aod, prevYear.aod)?.diff} from {prevYear.year}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
