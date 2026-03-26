"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ArrowRight, MessageSquare, Swords, CheckCircle, Trophy, Clock, Bot } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { useAuthStore, api } from "@/lib/store";
import { useState, useEffect } from "react";
import Link from "next/link";
import { getDashboardConfig } from "@/lib/dashboard-config";
import { formatDistanceToNow } from "date-fns";
import { es, enUS } from "date-fns/locale";

interface ChatSession {
    id: string;
    title: string;
    director: string;
    updated_at: string;
}

interface DojoCompletion {
    id: string;
    scenario_id: string;
    scenario_name: string;
    score: number;
    completed_at: string;
}

export default function DashboardPage() {
    const { t, language } = useLanguage();
    const { user } = useAuthStore();

    const [recentChats, setRecentChats] = useState<ChatSession[]>([]);
    const [dojoProgress, setDojoProgress] = useState<DojoCompletion[]>([]);
    const [isLoadingChats, setIsLoadingChats] = useState(true);
    const [isLoadingDojo, setIsLoadingDojo] = useState(true);

    const config = getDashboardConfig(user?.role || "member", t);
    const dateLocale = language === 'es' ? es : enUS;

    useEffect(() => {
        const fetchChats = async () => {
            try {
                const res = await api.get("/chat/history/current");
                setRecentChats((res.data || []).slice(0, 5));
            } catch (err) {
                console.error("Failed to fetch chat history", err);
            } finally {
                setIsLoadingChats(false);
            }
        };

        const fetchDojo = async () => {
            try {
                const res = await api.get("/dojo/progress");
                setDojoProgress((res.data.completions || []).slice(0, 5));
            } catch (err) {
                console.error("Failed to fetch dojo progress", err);
            } finally {
                setIsLoadingDojo(false);
            }
        };

        fetchChats();
        fetchDojo();
    }, []);

    return (
        <DashboardLayout>
            <div className="space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-3">
                            <h2 className="text-3xl font-bold font-heading tracking-tight">
                                {config.greeting(user?.full_name || "Leader")}
                            </h2>
                            {user?.role && (
                                <span className="px-2 py-0.5 rounded text-xs font-mono uppercase border bg-slate-500/20 text-slate-400 border-slate-500/30">
                                    {user.role.replace(/_/g, ' ')}
                                </span>
                            )}
                        </div>
                        <p className="text-muted-foreground mt-1">
                            {language === 'es' ? 'Tu centro de inteligencia estratégica.' : 'Your strategic intelligence hub.'}
                        </p>
                    </div>
                    <Link href="/chat">
                        <Button>{language === 'es' ? 'Nueva Conversación' : 'New Conversation'} <ArrowRight className="ml-2 h-4 w-4" /></Button>
                    </Link>
                </div>

                {/* Quick Actions */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Link href="/chat">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0 }}
                        >
                            <Card className="hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
                                <CardHeader className="flex flex-row items-center gap-4 pb-2">
                                    <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center">
                                        <MessageSquare className="h-6 w-6 text-primary" />
                                    </div>
                                    <div>
                                        <CardTitle className="text-base">{language === 'es' ? 'Agente Estratégico' : 'Strategic Agent'}</CardTitle>
                                        <CardDescription>{language === 'es' ? 'Conversa con tu consultor de IA' : 'Chat with your AI consultant'}</CardDescription>
                                    </div>
                                </CardHeader>
                            </Card>
                        </motion.div>
                    </Link>
                    <Link href="/dojo">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            <Card className="hover:shadow-md hover:border-primary/50 transition-all cursor-pointer h-full">
                                <CardHeader className="flex flex-row items-center gap-4 pb-2">
                                    <div className="h-12 w-12 rounded-xl bg-amber-500/10 flex items-center justify-center">
                                        <Swords className="h-6 w-6 text-amber-500" />
                                    </div>
                                    <div>
                                        <CardTitle className="text-base">{language === 'es' ? 'Leadership Dojo' : 'Leadership Dojo'}</CardTitle>
                                        <CardDescription>{language === 'es' ? 'Entrena tus habilidades de liderazgo' : 'Train your leadership skills'}</CardDescription>
                                    </div>
                                </CardHeader>
                            </Card>
                        </motion.div>
                    </Link>
                </div>

                {/* Content Grid */}
                <div className="grid gap-6 md:grid-cols-2">

                    {/* Recent Conversations */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                    >
                        <Card className="h-full">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <MessageSquare className="h-5 w-5 text-primary" />
                                    {language === 'es' ? 'Conversaciones Recientes' : 'Recent Conversations'}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {isLoadingChats ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="h-12 rounded-lg bg-muted/50 animate-pulse" />
                                        ))}
                                    </div>
                                ) : recentChats.length > 0 ? (
                                    <div className="space-y-2">
                                        {recentChats.map((session) => (
                                            <Link key={session.id} href={`/chat?session=${session.id}`}>
                                                <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group">
                                                    <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                                                        <Bot className="h-4 w-4 text-primary" />
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium truncate">{session.title}</p>
                                                        <div className="flex items-center gap-2">
                                                            {session.director && (
                                                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground capitalize">
                                                                    {session.director.replace(/_/g, ' ')}
                                                                </span>
                                                            )}
                                                            <span className="text-xs text-muted-foreground flex items-center gap-1">
                                                                <Clock className="h-3 w-3" />
                                                                {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true, locale: dateLocale })}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                                </div>
                                            </Link>
                                        ))}
                                        <Link href="/chat" className="block mt-2">
                                            <Button variant="ghost" className="w-full text-xs text-muted-foreground">
                                                {language === 'es' ? 'Ver todas las conversaciones' : 'View all conversations'} <ArrowRight className="ml-1 h-3 w-3" />
                                            </Button>
                                        </Link>
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <Bot className="h-10 w-10 mx-auto mb-2 opacity-20" />
                                        <p className="text-sm">{language === 'es' ? 'No hay conversaciones aún' : 'No conversations yet'}</p>
                                        <Link href="/chat">
                                            <Button variant="link" className="text-xs mt-1">
                                                {language === 'es' ? 'Iniciar primera conversación' : 'Start first conversation'}
                                            </Button>
                                        </Link>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Dojo Progress */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.3 }}
                    >
                        <Card className="h-full">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2 text-base">
                                    <Trophy className="h-5 w-5 text-amber-500" />
                                    {language === 'es' ? 'Progreso del Dojo' : 'Dojo Progress'}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                {isLoadingDojo ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3].map(i => (
                                            <div key={i} className="h-12 rounded-lg bg-muted/50 animate-pulse" />
                                        ))}
                                    </div>
                                ) : dojoProgress.length > 0 ? (
                                    <div className="space-y-2">
                                        {dojoProgress.map((item) => (
                                            <div key={item.id} className="flex items-center gap-3 p-3 rounded-lg bg-muted/30">
                                                <div className="h-8 w-8 rounded-full bg-amber-500/10 flex items-center justify-center shrink-0">
                                                    <CheckCircle className="h-4 w-4 text-amber-500" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium truncate">{item.scenario_name}</p>
                                                    <span className="text-xs text-muted-foreground">
                                                        {formatDistanceToNow(new Date(item.completed_at), { addSuffix: true, locale: dateLocale })}
                                                    </span>
                                                </div>
                                                {item.score > 0 && (
                                                    <span className={`text-sm font-bold px-2 py-0.5 rounded ${
                                                        item.score >= 8 ? 'text-green-500 bg-green-500/10' :
                                                        item.score >= 5 ? 'text-amber-500 bg-amber-500/10' :
                                                        'text-red-500 bg-red-500/10'
                                                    }`}>
                                                        {item.score}/10
                                                    </span>
                                                )}
                                            </div>
                                        ))}
                                        <Link href="/dojo" className="block mt-2">
                                            <Button variant="ghost" className="w-full text-xs text-muted-foreground">
                                                {language === 'es' ? 'Ir al Dojo' : 'Go to Dojo'} <ArrowRight className="ml-1 h-3 w-3" />
                                            </Button>
                                        </Link>
                                    </div>
                                ) : (
                                    <div className="text-center py-8 text-muted-foreground">
                                        <Swords className="h-10 w-10 mx-auto mb-2 opacity-20" />
                                        <p className="text-sm">{language === 'es' ? 'No has completado escenarios' : 'No completed scenarios'}</p>
                                        <Link href="/dojo">
                                            <Button variant="link" className="text-xs mt-1">
                                                {language === 'es' ? 'Practicar tu primer escenario' : 'Practice your first scenario'}
                                            </Button>
                                        </Link>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>

                {/* System Health - Admin Only */}
                {user?.role === 'admin' && (
                    <Card className="bg-muted/30 border-none shadow-none">
                        <CardHeader className="pb-2">
                            <CardTitle className="text-sm text-muted-foreground">{t.dashboard.systemHealth}</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="flex flex-col">
                                    <span className="text-xs text-muted-foreground">{t.dashboard.backend}</span>
                                    <span className="text-sm font-medium text-green-600 flex items-center gap-1">
                                        <CheckCircle className="h-3 w-3" /> {t.dashboard.operational}
                                    </span>
                                </div>
                                <div className="flex flex-col">
                                    <span className="text-xs text-muted-foreground">{t.dashboard.database}</span>
                                    <span className="text-sm font-medium text-green-600 flex items-center gap-1">
                                        <CheckCircle className="h-3 w-3" /> {t.dashboard.connected}
                                    </span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </DashboardLayout>
    );
}
