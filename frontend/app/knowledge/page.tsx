"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Search, Database, Download, Cloud, Loader2, CheckCircle, AlertTriangle } from "lucide-react";
import { api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { motion, AnimatePresence } from "framer-motion";

export default function KnowledgePage() {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isIngesting, setIsIngesting] = useState(false);
    const [ingestStatus, setIngestStatus] = useState<string | null>(null);
    const { t } = useLanguage();

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query) return;
        setIsLoading(true);
        try {
            const response = await api.post("/brandfolder/search", { query });
            setResults(response.data.results);
        } catch (error) {
            console.error("Search failed", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleIngest = async () => {
        setIsIngesting(true);
        setIngestStatus("Initializing ingestion protocol...");
        try {
            // In a real scenario, we might pass specific parameters
            const response = await api.post("/brandfolder/ingest", { topic: query || undefined, max_assets: 10 });
            setIngestStatus(`Success: Indexed ${response.data.indexed} assets.`);
        } catch (error) {
            setIngestStatus("Error: Ingestion failed.");
        } finally {
            setIsIngesting(false);
            // Clear status after 5 seconds
            setTimeout(() => setIngestStatus(null), 5000);
        }
    };

    return (
        <DashboardLayout>
            <div className="space-y-8">
                <div>
                    <h2 className="text-3xl font-bold font-heading">{t.knowledge.title}</h2>
                    <p className="text-muted-foreground">{t.knowledge.subtitle}</p>
                </div>

                <div className="grid gap-6 md:grid-cols-3">
                    {/* Ingest Card */}
                    <Card className="md:col-span-1 bg-primary/5 border-primary/20">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Cloud className="h-5 w-5 text-primary" />
                                {t.knowledge.dataIngestion}
                            </CardTitle>
                            <CardDescription>{t.knowledge.syncBrandfolder}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                <p className="text-sm text-muted-foreground">
                                    {t.knowledge.syncDescription}
                                </p>
                                <Button
                                    className="w-full"
                                    onClick={handleIngest}
                                    disabled={isIngesting}
                                    variant={ingestStatus?.startsWith("Error") ? "destructive" : "default"}
                                >
                                    {isIngesting ? (
                                        <>
                                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                            {t.knowledge.syncing}
                                        </>
                                    ) : (
                                        <>
                                            <Download className="mr-2 h-4 w-4" />
                                            {t.knowledge.runSync}
                                        </>
                                    )}
                                </Button>
                                <AnimatePresence>
                                    {ingestStatus && (
                                        <motion.div
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: "auto" }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className={`text-xs p-2 rounded border ${ingestStatus.startsWith("Error") ? "bg-destructive/10 text-destructive border-destructive/20" : "bg-green-500/10 text-green-500 border-green-500/20"}`}
                                        >
                                            {ingestStatus}
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Search Card */}
                    <Card className="md:col-span-2">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Database className="h-5 w-5 text-primary" />
                                {t.knowledge.assetExplorer}
                            </CardTitle>
                            <CardDescription>{t.knowledge.searchIndexed}</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <form onSubmit={handleSearch} className="flex gap-2 mb-6">
                                <Input
                                    placeholder={t.knowledge.searchPlaceholder}
                                    value={query}
                                    onChange={(e) => setQuery(e.target.value)}
                                />
                                <Button type="submit" disabled={isLoading}>
                                    {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                                </Button>
                            </form>

                            {results.length > 0 ? (
                                <div className="rounded-md border border-border">
                                    <div className="max-h-[300px] overflow-auto">
                                        <table className="w-full text-sm text-left">
                                            <thead className="text-xs text-muted-foreground uppercase bg-muted/50 sticky top-0">
                                                <tr>
                                                    <th className="px-4 py-3">Asset Name</th>
                                                    <th className="px-4 py-3">Type</th>
                                                    <th className="px-4 py-3 text-right">Action</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {results.map((item) => (
                                                    <tr key={item.id} className="border-b border-border hover:bg-muted/50 transition-colors">
                                                        <td className="px-4 py-3 font-medium">{item.name}</td>
                                                        <td className="px-4 py-3 text-muted-foreground">{item.extension || "N/A"}</td>
                                                        <td className="px-4 py-3 text-right">
                                                            <a href={item.url} target="_blank" rel="noreferrer" className="text-primary hover:underline text-xs">
                                                                View
                                                            </a>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-10 text-muted-foreground border border-dashed border-border rounded-lg">
                                    <Search className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                    <p>{t.knowledge.noResults}</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
