"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Brain, Library } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";

export default function DashboardPage() {
    const { t } = useLanguage();

    const stats = [
        { label: t.dashboard.activeSession, value: "8", icon: Brain, color: "text-purple-500" },
        { label: t.dashboard.knowledgeBase, value: "1,240+", icon: Library, color: "text-blue-500" },
        { label: t.dashboard.recentActivity, value: "42", icon: Activity, color: "text-green-500" },
    ];

    return (
        <DashboardLayout>
            <div className="space-y-8">
                <div>
                    <h2 className="text-3xl font-bold font-heading tracking-tight">{t.dashboard.overview}</h2>
                    <p className="text-muted-foreground">{t.dashboard.readyToProcess}</p>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                    {stats.map((stat, i) => (
                        <motion.div
                            key={stat.label}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }}
                        >
                            <Card className="hover:shadow-lg transition-all hover:bg-card/50">
                                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                    <CardTitle className="text-sm font-medium">
                                        {stat.label}
                                    </CardTitle>
                                    <stat.icon className={`h-4 w-4 ${stat.color}`} />
                                </CardHeader>
                                <CardContent>
                                    <div className="text-2xl font-bold">{stat.value}</div>
                                    <p className="text-xs text-muted-foreground">
                                        +20.1% {t.dashboard.recentActivity.toLowerCase()}
                                    </p>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </div>

                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                    <Card className="col-span-4 border-primary/20 bg-gradient-to-br from-card to-card/50">
                        <CardHeader>
                            <CardTitle>{t.dashboard.recentActivity}</CardTitle>
                            <CardDescription>
                                {t.dashboard.readyToProcess}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-8">
                                {/* Mock Activity */}
                                {[1, 2, 3].map((_, i) => (
                                    <div className="flex items-center" key={i}>
                                        <div className="ml-4 space-y-1">
                                            <p className="text-sm font-medium leading-none">
                                                Strategy Session #{200 + i}
                                            </p>
                                            <p className="text-sm text-muted-foreground">
                                                Generated content for "Sunday Service Flow"
                                            </p>
                                        </div>
                                        <div className="ml-auto font-medium text-xs text-muted-foreground">
                                            {i * 15}m ago
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                    <Card className="col-span-3">
                        <CardHeader>
                            <CardTitle>{t.dashboard.systemStatus}</CardTitle>
                            <CardDescription>
                                {t.dashboard.operational}
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="space-y-4">
                                {[
                                    { label: "RAG Pipeline", status: t.dashboard.operational, color: "bg-green-500" },
                                    { label: "Brandfolder Sync", status: t.dashboard.systemOnline, color: "bg-yellow-500" },
                                    { label: "LLM Latency", status: "98ms", color: "bg-green-500" },
                                ].map((item) => (
                                    <div key={item.label} className="flex items-center justify-between">
                                        <span className="text-sm font-medium">{item.label}</span>
                                        <div className="flex items-center gap-2">
                                            <span className={`h-2 w-2 rounded-full ${item.color} animate-pulse`} />
                                            <span className="text-xs text-muted-foreground">{item.status}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
