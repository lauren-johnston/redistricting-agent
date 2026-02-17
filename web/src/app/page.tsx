import { getSupabase, Submission } from "@/lib/supabase";
import { Dashboard } from "@/components/Dashboard";

export const dynamic = "force-dynamic";

async function getSubmissions(): Promise<Submission[]> {
  const { data, error } = await getSupabase()
    .from("submissions")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) {
    console.error("Error fetching submissions:", error);
    return [];
  }

  return data as Submission[];
}

export default async function Home() {
  const submissions = await getSubmissions();

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Redistricting Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Community of Interest submissions collected via voice agent
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-50 text-blue-700">
                {submissions.length} submission{submissions.length !== 1 ? "s" : ""}
              </span>
            </div>
          </div>
        </div>
      </header>
      <Dashboard submissions={submissions} />
    </main>
  );
}
