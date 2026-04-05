import { createClient } from "@/lib/supabase/server";
import { Sidebar } from "@/components/layout/sidebar";
import { Toaster } from "sonner";

export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="min-h-screen">
      <Sidebar userEmail={user?.email} />
      <main className="lg:pl-60">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pt-16 lg:pt-8">
          {children}
        </div>
      </main>
      <Toaster
        theme="dark"
        toastOptions={{
          style: {
            background: "#141414",
            border: "1px solid #1e1e1e",
            color: "#fafafa",
          },
        }}
      />
    </div>
  );
}
