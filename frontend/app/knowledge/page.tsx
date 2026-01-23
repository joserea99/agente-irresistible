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

                <div className="grid gap-6 md:grid-cols-2">
                    {/* Ingest Card - Now more prominent for "Explanation" */}
                    <Card className="md:col-span-1 border-primary/20 shadow-md">
                        <CardHeader className="bg-primary/5 pb-4">
                            <CardTitle className="flex items-center gap-2 text-xl">
                                <Cloud className="h-6 w-6 text-primary" />
                                {t.knowledge.dataIngestion || "Expand Knowledge Base"}
                            </CardTitle>
                            <CardDescription>
                                Import new content from Brandfolder into the AI brain
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="pt-6 space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                                    Topic to Ingest (Optional)
                                </label>
                                <div className="flex gap-2">
                                    <Input
                                        placeholder="e.g., Leadership, Vision, Kids"
                                        id="ingest-topic"
                                    />
                                    <Button
                                        onClick={() => {
                                            const topic = (document.getElementById("ingest-topic") as HTMLInputElement).value;
                                            setQuery(topic); // Keep sync for feedback
                                            handleIngest();
                                        }}
                                        disabled={isIngesting}
                                        className="min-w-[100px]"
                                    >
                                        {isIngesting ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <>
                                                <Download className="mr-2 h-4 w-4" />
                                                Ingest
                                            </>
                                        )}
                                    </Button>
                                </div>
                                <p className="text-xs text-muted-foreground mt-2">
                                    Leave empty to ingest the most recent assets from all folders.
                                </p>
                            </div>

                            <div className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
                                <p className="font-semibold mb-1">How it works:</p>
                                <ul className="list-disc pl-4 space-y-1">
                                    <li>Connects to Irresistible Church Network Brandfolder</li>
                                    <li>Downloads assets matching your topic</li>
                                    <li>Processes text from descriptions and attachments</li>
                                    <li>Stores knowledge for the directors to use</li>
                                </ul>
                            </div>

                            <AnimatePresence>
                                {ingestStatus && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: "auto" }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className={`text-sm p-3 rounded-md border ${ingestStatus.startsWith("Error") ? "bg-destructive/10 text-destructive border-destructive/20" : "bg-green-500/10 text-green-500 border-green-500/20"}`}
                                    >
                                        <div className="flex items-center gap-2">
                                            {ingestStatus.startsWith("Error") ? (
                                                <AlertTriangle className="h-4 w-4" />
                                            ) : (
                                                <CheckCircle className="h-4 w-4" />
                                            )}
                                            {ingestStatus}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </CardContent>
                    </Card>

                    {/* Search Card */}
                    <Card className="md:col-span-1 border-border shadow-sm">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-xl">
                                <Database className="h-6 w-6 text-primary" />
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
                                    className="bg-background"
                                />
                                <Button type="submit" disabled={isLoading} variant="secondary">
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
                                                        <td className="px-4 py-3 font-medium truncate max-w-[200px]" title={item.name}>{item.name}</td>
                                                        <td className="px-4 py-3 text-muted-foreground">{item.extension || "N/A"}</td>
                                                        <td className="px-4 py-3 text-right">
                                                            <a href={item.url} target="_blank" rel="noreferrer" className="text-primary hover:underline text-xs bg-primary/10 px-2 py-1 rounded">
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
                                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg bg-muted/20">
                                    <Search className="h-10 w-10 mx-auto mb-3 opacity-30" />
                                    <p>{t.knowledge.noResults}</p>
                                    <p className="text-xs mt-1 opacity-70">Try searching for 'Leadership' or 'Vision'</p>
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
