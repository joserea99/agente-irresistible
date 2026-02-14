"use client";

import DashboardLayout from "@/components/dashboard-layout";
import DeepResearch from "@/components/deep-research";
import { FileUploader } from "@/components/file-uploader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

import { useAuthStore } from "@/lib/store";

export default function KnowledgePage() {
    const { user } = useAuthStore();
    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h2 className="text-3xl font-bold font-heading tracking-tight">Base de Conocimiento</h2>
                    <p className="text-muted-foreground mt-2">
                        Administra y amplía lo que el Agente sabe. Sube archivos manuales o sincroniza con la Red Global.
                    </p>
                </div>

                <Tabs defaultValue="research" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
                        <TabsTrigger value="research">Investigación Profunda</TabsTrigger>
                        {user?.role === 'admin' && (
                            <TabsTrigger value="upload">Subida Directa (Admin)</TabsTrigger>
                        )}
                    </TabsList>

                    {user?.role === 'admin' && (
                        <TabsContent value="upload" className="mt-6">
                            <div className="grid gap-6">
                                <Card>
                                    <CardHeader>
                                        <CardTitle>Cargar Archivos</CardTitle>
                                        <CardDescription>
                                            Sube PDFs, audios o videos. El agente los procesará y aprenderá de ellos automáticamente.
                                        </CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <FileUploader />
                                    </CardContent>
                                </Card>
                            </div>
                        </TabsContent>
                    )}

                    <TabsContent value="research" className="mt-6">
                        <DeepResearch />
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
