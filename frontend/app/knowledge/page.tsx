"use client";

import DashboardLayout from "@/components/dashboard-layout";
import DeepResearch from "@/components/deep-research";
import { FileUploader } from "@/components/file-uploader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function KnowledgePage() {
    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h2 className="text-3xl font-bold font-heading tracking-tight">Base de Conocimiento</h2>
                    <p className="text-muted-foreground mt-2">
                        Administra y amplía lo que el Agente sabe. Sube archivos manuales o sincroniza con Brandfolder.
                    </p>
                </div>

                <Tabs defaultValue="upload" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 lg:w-[400px]">
                        <TabsTrigger value="upload">Subida Directa</TabsTrigger>
                        <TabsTrigger value="research">Investigación Profunda</TabsTrigger>
                    </TabsList>

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

                    <TabsContent value="research" className="mt-6">
                        <DeepResearch />
                    </TabsContent>
                </Tabs>
            </div>
        </DashboardLayout>
    );
}
