
"use client";

import DashboardLayout from "@/components/dashboard-layout";
import DeepResearch from "@/components/deep-research";
import { FileUploader } from "@/components/file-uploader";

export default function KnowledgePage() {
    return (
        <DashboardLayout>
            <div className="space-y-8">
                <section>
                    <h2 className="text-2xl font-bold font-heading mb-4">Gestión de Conocimiento</h2>
                    <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-2">
                        <FileUploader />
                        {/* You can add more widgets here like "Recent Uploads List" later */}
                    </div>
                </section>

                <section>
                    <DeepResearch />
                </section>
            </div>
        </DashboardLayout>
    );
}
