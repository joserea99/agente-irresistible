"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { ArrowRight, Clock, CheckCircle, Library } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { useAuthStore, api } from "@/lib/store";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getDashboardConfig, DashboardConfig } from "@/lib/dashboard-config";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"; // For Role Switcher

export default function DashboardPage() {
    const { t } = useLanguage();
    const { user } = useAuthStore();
    const [knowledgeCount, setKnowledgeCount] = useState<string>("Loading...");
    const [recentDocs, setRecentDocs] = useState<any[]>([]);

    // Role Switcher State (for testing)
    const [previewRole, setPreviewRole] = useState<string>(user?.role || "member");

    // Get config based on previewRole directly
    const config = getDashboardConfig(previewRole);

    useEffect(() => {
        if (user?.role) {
            setPreviewRole(user.role);
        }
    }, [user?.role]);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const response = await api.get("/brandfolder/stats");
                // Format with commas
                const count = response.data.document_count;
                setKnowledgeCount(count.toLocaleString());

                // Get recent docs if available (fallback to empty array)
                if (response.data.recent_documents) {
                    setRecentDocs(response.data.recent_documents);
                }
            } catch (error) {
                console.error("Failed to fetch stats", error);
                setKnowledgeCount("0");
            }
        };

        fetchStats();
    }, []);

    // Merge dynamic data into config stats
    const stats = config.stats.map(stat => {
        if (stat.label === "Knowledge Base" || stat.label === "Brand Assets") {
            return { ...stat, value: knowledgeCount };
        }
        return stat;
    });

    return (
        <DashboardLayout>
            <div className="space-y-8">
                {/* Header Section */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-3xl font-bold font-heading tracking-tight">
                                {config.greeting(user?.full_name || "Leader")}
                            </h2>
                            {user?.role && (
                                <span className={`px-2 py-0.5 rounded text-xs font-mono uppercase border bg-slate-500/20 text-slate-400 border-slate-500/30`}>
                                    {user.role}
                                </span>
                            )}
                        </div>
                        <p className="text-muted-foreground">{t.dashboard.readyToProcess || "Your strategic intelligence hub is ready."}</p>
                    </div>

                    <div className="flex gap-2 items-center">
                        {/* Role Switcher for Demo */}
                        <div className="hidden md:block w-[180px]">
                            <Select value={previewRole} onValueChange={setPreviewRole}>
                                <SelectTrigger className="h-9 text-xs">
                                    <SelectValue placeholder="Preview Role" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="pastor_principal">Pastor Principal</SelectItem>
                                    <SelectItem value="kids_director">Kids Director</SelectItem>
                                    <SelectItem value="media_director">Media Director</SelectItem>
                                    <SelectItem value="member">Member (Default)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <Link href="/chat">
                            <Button>New Session <ArrowRight className="ml-2 h-4 w-4" /></Button>
                        </Link>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid gap-4 md:grid-cols-3">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <Card className="hover:shadow-md transition-all">
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">
                                        {stat.label}
                                    </CardTitle>
                                    <stat.icon className={`h-4 w-4 ${stat.color}`} />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{stat.value}</div>
                                    <p className="text-xs text-muted-foreground">{stat.desc}</p>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>

                {/* Main Content Grid */}
                <div className="grid gap-6 md:grid-cols-7">

                    {/* Left Column: Quick Actions & Recent Docs (4 cols) */}
                    <div className="md:col-span-4 space-y-6">

                        {/* Quick Actions */}
                        <div>
                            <h3 className="text-lg font-semibold mb-3">Quick Actions</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                {config.quickActions.map((action) => (
                                    <Link href={action.href} key={action.title}>
                                        <div className={`p-4 rounded-xl border ${action.color} hover:bg-opacity-20 transition-all cursor-pointer h-full flex flex-col justify-between`}>
                                            <action.icon className="h-6 w-6 mb-2" />
                                            <div>
                                                <div className="font-bold text-sm">{action.title}</div>
                                                <div className="text-xs opacity-70">{action.desc}</div>
                                            </div>
                                        </div>
                                    </Link>
                                ))}
                            </div>
                        </div>

                        {/* Recent Knowledge */}
                        <Card className="border-primary/10">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Library className="h-5 w-5 text-blue-500" />
                                    Latest Knowledge Assets
                                </CardTitle>
                                <CardDescription>Recently ingested from Brandfolder</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {recentDocs.length > 0 ? (
                                        recentDocs.map((doc, i) => (
                                            <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors border border-transparent hover:border-border">
                                                <div className="h-8 w-8 rounded bg-blue-500/10 flex items-center justify-center shrink-0">
                                                    <Clock className="h-4 w-4 text-blue-500" />
                                                </div>
                                                <div className="overflow-hidden">
                                                    <p className="text-sm font-medium truncate">{doc.title || "Untitled Asset"}</p>
                                                    <a href={doc.source} target="_blank" className="text-xs text-muted-foreground hover:text-primary hover:underline truncate block">
                                                        {doc.source || "No source link"}
                                                    </a>
                                                </div>
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-8 text-muted-foreground">
                                            <p>No recent documents found.</p>
                                            <Link href="/knowledge">
                                                <Button variant="link" className="text-xs">Go to Ingest</Button>
                                            </Link>
                                        </div>
                                    )}
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Link href="/knowledge" className="w-full">
                                    <Button variant="outline" className="w-full text-xs">View Knowledge Base</Button>
                                </Link>
                            </CardFooter>
                        </Card>
                    </div>

                    {/* Right Column: System Status & Directors (3 cols) */}
                    <div className="md:col-span-3 space-y-6">
                        {/* Directors Status */}
                        <Card>
                            <CardHeader>
                                <CardTitle>Active Directors</CardTitle>
                                <CardDescription>AI Personas ready to assist</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {[
                                        { name: "Pastor Principal", role: "Vision & Strategy", status: "Online", color: "bg-green-500" },
                                        { name: "Service Programming", role: "Services", status: "Busy", color: "bg-yellow-500" },
                                        { name: "Kids & NextGen", role: "Family Ministry", status: "Online", color: "bg-green-500" },
                                        { name: "Media Director", role: "Creative", status: "Online", color: "bg-pink-500" },
                                    ].map((director) => (
                                        <div key={director.name} className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="h-2 w-2 rounded-full bg-slate-200 dark:bg-slate-700" />
                                                <div>
                                                    <p className="text-sm font-medium">{director.name}</p>
                                                    <p className="text-xs text-muted-foreground">{director.role}</p>
                                                </div>
                                            </div>
                                            <div className={`px-2 py-0.5 rounded-full text-[10px] bg-opacity-10 ${director.color.replace('bg-', 'text-')} flex items-center gap-1`}>
                                                <div className={`h-1.5 w-1.5 rounded-full ${director.color}`} />
                                                {director.status}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        {/* System Status Updated */}
                        <Card className="bg-muted/30 border-none shadow-none">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-muted-foreground">System Health</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="flex flex-col">
                                        <span className="text-xs text-muted-foreground">Backend</span>
                                        <span className="text-sm font-medium text-green-600 flex items-center gap-1">
                                            <CheckCircle className="h-3 w-3" /> Operational
                                        </span>
                                    </div>
                                    <div className="flex flex-col">
                                        <span className="text-xs text-muted-foreground">Database</span>
                                        <span className="text-sm font-medium text-green-600 flex items-center gap-1">
                                            <CheckCircle className="h-3 w-3" /> Connected
                                        </span>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
