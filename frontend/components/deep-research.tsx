
"use client";

import { useState, useEffect } from "react";
import { useAuthStore, api } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, Play, FileText, CheckCircle, Video, Music } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function DeepResearch() {
    const { user } = useAuthStore();
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(false);
    const [view, setView] = useState<'search' | 'proposal' | 'executing' | 'history'>('search');
    const [session, setSession] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);

    useEffect(() => {
        if (user) fetchHistory();
    }, [user]);

    const fetchHistory = async () => {
        try {
            const res = await api.get(`/brandfolder/research/history?username=${user?.username}`);
            setHistory(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    const startResearch = async () => {
        if (!query.trim()) return;
        setLoading(true);
        try {
            const res = await api.post("/brandfolder/research/start", {
                query,
                username: user?.username
            });
            setSession(res.data);
            setView('proposal');
        } catch (err) {
            alert("Failed to start research");
        } finally {
            setLoading(false);
        }
    };

    const executeResearch = async () => {
        if (!session) return;
        setLoading(true);
        try {
            await api.post(`/brandfolder/research/${session.session_id}/execute`);
            setView('executing');
            pollStatus();
        } catch (err) {
            alert("Failed to execute");
            setLoading(false);
        }
    };

    const pollStatus = async () => {
        const interval = setInterval(async () => {
            try {
                const res = await api.get(`/brandfolder/research/${session.session_id}`);
                setSession(res.data);
                if (res.data.status === 'completed') {
                    clearInterval(interval);
                    setLoading(false);
                    fetchHistory();
                }
            } catch (err) {
                console.error(err);
            }
        }, 2000);
    };

    // --- UI COMPONENTS ---

    if (view === 'search') {
        return (
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="text-center space-y-4">
                    <h1 className="text-4xl font-bold font-heading bg-gradient-to-r from-primary to-purple-400 bg-clip-text text-transparent">
                        Deep Research Agent
                    </h1>
                    <p className="text-muted-foreground text-lg">
                        I will scan your Brandfolder, map key themes, and deeply analyze every asset.
                    </p>
                </div>

                <Card className="bg-slate-900/50 border-slate-800 backdrop-blur-sm p-6">
                    <div className="flex gap-4">
                        <Input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="What do you want to learn about? (e.g., 'Sermones sobre el voluntariado')"
                            className="text-lg py-6 bg-slate-950/50 border-slate-700"
                        />
                        <Button
                            onClick={startResearch}
                            disabled={loading}
                            size="lg"
                            className="bg-primary hover:bg-primary/90 text-lg px-8"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : <Search />}
                        </Button>
                    </div>
                </Card>

                {history.length > 0 && (
                    <div className="space-y-4">
                        <h3 className="text-xl font-semibold opacity-80">Research History</h3>
                        <div className="grid gap-3 md:grid-cols-2">
                            {history.map((h) => (
                                <Card key={h.id} className="hover:bg-slate-800/50 transition-colors cursor-pointer border-slate-800"
                                    onClick={() => { setSession(h); setView(h.status === 'completed' ? 'executing' : 'proposal'); }}>
                                    <div className="p-4 flex justify-between items-center">
                                        <div>
                                            <p className="font-medium">{h.query}</p>
                                            <p className="text-xs text-muted-foreground">{new Date(h.created_at).toLocaleDateString()}</p>
                                        </div>
                                        <Badge variant={h.status === 'completed' ? 'default' : 'secondary'}>
                                            {h.status}
                                        </Badge>
                                    </div>
                                </Card>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        );
    }

    if (view === 'proposal') {
        return (
            <div className="max-w-3xl mx-auto space-y-6">
                <Button variant="ghost" onClick={() => setView('search')}>← Back</Button>

                <Card className="border-primary/20 bg-slate-900/80">
                    <CardHeader>
                        <CardTitle className="text-2xl">Research Proposal: "{session.query}"</CardTitle>
                        <CardDescription>I have scanned your Brandfolder and found the following:</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="p-4 bg-primary/10 rounded-lg text-primary-foreground">
                            <p className="text-lg">{session.summary}</p>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-4 bg-slate-950 rounded border border-slate-800 text-center">
                                <p className="text-3xl font-bold">{session.asset_count}</p>
                                <p className="text-sm text-muted-foreground">Assets Found</p>
                            </div>
                            <div className="p-4 bg-slate-950 rounded border border-slate-800 text-center">
                                <p className="text-3xl font-bold">~{session.assets?.filter((a: any) => a.type === 'video').length * 2 || 1}</p>
                                <p className="text-sm text-muted-foreground">Est. Minutes to Process</p>
                            </div>
                        </div>

                        <div>
                            <h3 className="font-semibold mb-2">Assets identified for transcription:</h3>
                            <div className="max-h-60 overflow-y-auto space-y-2 pr-2">
                                {session.assets?.map((a: any) => (
                                    <div key={a.id} className="flex items-center gap-3 p-2 rounded bg-slate-800/50 text-sm">
                                        {a.type === 'video' ? <Video size={16} className="text-blue-400" /> :
                                            a.type === 'audio' ? <Music size={16} className="text-pink-400" /> :
                                                <FileText size={16} className="text-slate-400" />}
                                        <span className="truncate flex-1">{a.name}</span>
                                        <Badge variant="outline">{a.type}</Badge>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </CardContent>
                    <CardFooter className="flex justify-end gap-3">
                        <Button variant="outline" onClick={() => setView('search')}>Cancel</Button>
                        <Button onClick={executeResearch} disabled={loading} className="bg-green-600 hover:bg-green-700">
                            {loading ? <Loader2 className="animate-spin mr-2" /> : <Play className="mr-2" size={16} />}
                            Begin Deep Research
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    if (view === 'executing') {
        const completed = session.assets?.filter((a: any) => a.status === 'indexed').length || 0;
        const total = session.assets?.length || 0;
        const progress = total > 0 ? (completed / total) * 100 : 0;
        const isDone = session.status === 'completed';

        return (
            <div className="max-w-3xl mx-auto space-y-8 text-center pt-10">
                <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                    {isDone ? (
                        <CheckCircle className="h-20 w-20 text-green-500 mx-auto mb-6" />
                    ) : (
                        <Loader2 className="h-20 w-20 text-primary animate-spin mx-auto mb-6" />
                    )}

                    <h2 className="text-3xl font-bold mb-2">
                        {isDone ? "Research Complete" : "Executing Deep Research..."}
                    </h2>
                    <p className="text-muted-foreground text-lg mb-8">
                        {isDone ? "All assets have been transcribed and indexed." : "I am watching videos, listening to audio, and reading documents."}
                    </p>

                    {/* Progress Bar */}
                    <div className="w-full bg-slate-800 rounded-full h-4 overflow-hidden mb-2">
                        <div
                            className="bg-primary h-full transition-all duration-500"
                            style={{ width: `${progress}%` }}
                        />
                    </div>
                    <p className="text-sm text-muted-foreground">{completed} / {total} Assets Processed</p>
                </motion.div>

                {isDone && (
                    <div className="flex justify-center gap-4">
                        <Button variant="outline" onClick={() => setView('search')}>Start New Research</Button>
                        <Button onClick={() => window.location.href = '/chat'}>Go to Chat & Ask</Button>
                    </div>
                )}

                <div className="text-left mt-8 max-h-60 overflow-y-auto bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                    {session.assets?.map((a: any) => (
                        <div key={a.id} className="flex justify-between py-2 border-b border-slate-800/50 last:border-0">
                            <span className="text-sm opacity-80">{a.name}</span>
                            {a.status === 'pending' && <span className="text-xs text-slate-500">Pending...</span>}
                            {a.status === 'indexed' && <span className="text-xs text-green-400 font-medium">Done</span>}
                            {a.status === 'error' && <span className="text-xs text-red-400">Error</span>}
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    return null;
}
