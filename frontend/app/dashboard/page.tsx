"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
    ArrowRight,
    Swords,
    CheckCircle,
    Trophy,
    Clock,
    BookOpen,
    Users,
    Library,
    Sparkles,
    Heart,
    Share2,
} from "lucide-react";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuthStore, api } from "@/lib/store";
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
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
    const { language } = useLanguage();
    const { user } = useAuthStore();
    const router = useRouter();
    const isEs = language === "es";

    const [sundayTopic, setSundayTopic] = useState("");
    const [recentChats, setRecentChats] = useState<ChatSession[]>([]);
    const [dojoProgress, setDojoProgress] = useState<DojoCompletion[]>([]);
    const [isLoadingChats, setIsLoadingChats] = useState(true);
    const [isLoadingDojo, setIsLoadingDojo] = useState(true);

    const dateLocale = isEs ? es : enUS;

    useEffect(() => {
        const fetchChats = async () => {
            try {
                const res = await api.get("/chat/history/current");
                const list = Array.isArray(res.data) ? res.data : (res.data?.sessions || []);
                setRecentChats(list.slice(0, 5));
            } catch (err) {
                console.warn("Failed to fetch chat history", err);
            } finally {
                setIsLoadingChats(false);
            }
        };

        const fetchDojo = async () => {
            try {
                const res = await api.get("/dojo/progress");
                setDojoProgress((res.data.completions || []).slice(0, 5));
            } catch (err) {
                console.warn("Failed to fetch dojo progress", err);
            } finally {
                setIsLoadingDojo(false);
            }
        };

        fetchChats();
        fetchDojo();
    }, []);

    const handleLaunchStudio = (e: React.FormEvent) => {
        e.preventDefault();
        if (!sundayTopic.trim()) {
            router.push("/studio");
            return;
        }
        router.push(`/studio?topic=${encodeURIComponent(sundayTopic.trim())}`);
    };

    return (
        <DashboardLayout>
            <div className="space-y-8 pb-10">
                {/* Executive Welcome Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div className="flex items-center gap-2.5">
                            <h1 className="text-2xl md:text-3xl font-bold font-heading tracking-tight text-foreground">
                                {isEs ? `Hola, ${user?.full_name || "Líder"}` : `Welcome, ${user?.full_name || "Leader"}`}
                            </h1>
                            {user?.role && (
                                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold capitalize bg-primary/12 text-primary border border-primary/20">
                                    {user.role.replace(/_/g, " ")}
                                </span>
                            )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                            {isEs
                                ? "Centro de producción dominical, estrategia ministerial y formación de equipos."
                                : "Sunday production hub, ministry strategy, and team training."}
                        </p>
                    </div>
                    <div className="grid grid-cols-2 sm:flex items-center gap-2 w-full md:w-auto">
                        <Link href="/studio?tab=library" className="w-full sm:w-auto">
                            <Button variant="outline" size="sm" className="w-full sm:w-auto gap-1.5 font-medium text-xs sm:text-sm px-2.5 sm:px-3">
                                <Library className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-primary shrink-0" />
                                <span className="truncate">{isEs ? "Biblioteca (1,812)" : "Library (1,812)"}</span>
                            </Button>
                        </Link>
                        <Link href="/studio" className="w-full sm:w-auto">
                            <Button size="sm" className="w-full sm:w-auto gap-1.5 font-semibold text-xs sm:text-sm px-2.5 sm:px-3">
                                <Sparkles className="h-3.5 w-3.5 sm:h-4 sm:w-4 shrink-0" />
                                <span className="truncate">{isEs ? "Prepara tu Semana" : "Prepare Your Week"}</span>
                            </Button>
                        </Link>
                    </div>
                </div>

                {/* HERO: Weekly Production Engine Box */}
                <Card className="border-primary/25 bg-gradient-to-br from-card via-card to-primary/5 shadow-sm overflow-hidden">
                    <CardContent className="p-6 md:p-8 space-y-5">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="space-y-1.5 max-w-2xl">
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-primary/12 text-primary">
                                    <Sparkles className="h-3.5 w-3.5" />
                                    {isEs ? "Prepara tu Semana en 1 Clic" : "Prepare Your Week in 1 Click"}
                                </div>
                                <h2 className="text-xl md:text-2xl font-bold font-heading text-foreground">
                                    {isEs ? "¿De qué trata el mensaje de este domingo?" : "What is this Sunday's message about?"}
                                </h2>
                                <p className="text-sm text-muted-foreground">
                                    {isEs
                                        ? "Escribe el tema o pasaje bíblico y genera al instante las 5 piezas operativas listas para tu equipo."
                                        : "Enter your topic or scripture and instantly generate all 5 operational pieces for your team."}
                                </p>
                            </div>
                        </div>

                        <form onSubmit={handleLaunchStudio} className="flex flex-col sm:flex-row gap-2.5">
                            <Input
                                value={sundayTopic}
                                onChange={(e) => setSundayTopic(e.target.value)}
                                placeholder={
                                    isEs
                                        ? "Ej. Cómo superar la ansiedad financiera en la familia (Mateo 6:25-34)..."
                                        : "e.g., Overcoming financial anxiety in the family (Matthew 6:25-34)..."
                                }
                                className="h-12 bg-background text-sm flex-1 border-border"
                            />
                            <Button type="submit" size="lg" className="h-12 px-6 font-semibold gap-2 shrink-0">
                                {isEs ? "Producir Pack del Domingo" : "Produce Sunday Pack"}
                                <ArrowRight className="h-4 w-4" />
                            </Button>
                        </form>

                        {/* 5 Deliverables Preview Pills */}
                        <div className="pt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                            <span className="font-semibold text-foreground/80">
                                {isEs ? "Incluye:" : "Includes:"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/70 text-foreground/90 font-medium">
                                <BookOpen className="h-3.5 w-3.5 text-primary" />
                                {isEs ? "Bosquejo (5 Movimientos)" : "Sermon Outline"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/70 text-foreground/90 font-medium">
                                <Users className="h-3.5 w-3.5 text-primary" />
                                {isEs ? "Guía de Grupos Pequeños" : "Small Group Guide"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/70 text-foreground/90 font-medium">
                                <Heart className="h-3.5 w-3.5 text-primary" />
                                {isEs ? "Lección Niños y Familia" : "Kids & Family Lesson"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/70 text-foreground/90 font-medium">
                                <Clock className="h-3.5 w-3.5 text-primary" />
                                {isEs ? "Orden de Servicio (70m)" : "Service Run Sheet (70m)"}
                            </span>
                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-secondary/70 text-foreground/90 font-medium">
                                <Share2 className="h-3.5 w-3.5 text-primary" />
                                {isEs ? "Redes + WhatsApp" : "Social + WhatsApp"}
                            </span>
                        </div>
                    </CardContent>
                </Card>

                {/* Core Workspaces Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    <Link href="/studio?tab=library" className="block group">
                        <Card className="h-full border-border bg-card hover:border-primary/40 transition-all shadow-2xs">
                            <CardHeader>
                                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                    <Library className="h-5 w-5" />
                                </div>
                                <CardTitle className="text-base font-heading flex items-center justify-between">
                                    {isEs ? "Biblioteca de Series y Recursos" : "Series & Resource Library"}
                                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                                </CardTitle>
                                <CardDescription className="text-xs leading-relaxed">
                                    {isEs
                                        ? "Explora los 1,821 recursos de la Biblioteca Irresistible Agent y adáptalos al español en 1 clic."
                                        : "Browse 1,821 resources in the Irresistible Agent Library and adapt them in 1 click."}
                                </CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/chat" className="block group">
                        <Card className="h-full border-border bg-card hover:border-primary/40 transition-all shadow-2xs">
                            <CardHeader>
                                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                    <Users className="h-5 w-5" />
                                </div>
                                <CardTitle className="text-base font-heading flex items-center justify-between">
                                    {isEs ? "Consulta con los Especialistas" : "Ask the Specialists"}
                                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                                </CardTitle>
                                <CardDescription className="text-xs leading-relaxed">
                                    {isEs
                                        ? "Claridad y guía práctica para pastores, directores, líderes de grupos, niños, jóvenes, anfitriones y producción."
                                        : "Clarity and practical guidance for pastors, directors, group leaders, kids, youth, hosts, and production."}
                                </CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>

                    <Link href="/dojo" className="block group">
                        <Card className="h-full border-border bg-card hover:border-primary/40 transition-all shadow-2xs">
                            <CardHeader>
                                <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary flex items-center justify-center mb-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors">
                                    <Swords className="h-5 w-5" />
                                </div>
                                <CardTitle className="text-base font-heading flex items-center justify-between">
                                    {isEs ? "Entrenamiento de Líderes" : "Leadership Training"}
                                    <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-0.5 transition-all" />
                                </CardTitle>
                                <CardDescription className="text-xs leading-relaxed">
                                    {isEs
                                        ? "Practica conversaciones reales de tu área (padres, miembros de grupo, invitados o voluntarios) y recibe retroalimentación."
                                        : "Practice real conversations from your ministry area and receive immediate coaching."}
                                </CardDescription>
                            </CardHeader>
                        </Card>
                    </Link>
                </div>

                {/* Area-Specific Clarity & Training Hub for Leaders in Any Area */}
                <Card className="border-border bg-card shadow-2xs">
                    <CardHeader className="pb-3">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <div>
                                <CardTitle className="text-base font-heading">
                                    {isEs
                                        ? "Claridad y Entrenamiento por Área Ministerial"
                                        : "Clarity & Training by Ministry Area"}
                                </CardTitle>
                                <CardDescription className="text-xs">
                                    {isEs
                                        ? "Para pastores, directores, líderes de grupo y voluntarios: entra directo al especialista de tu área para resolver dudas o entrenar a tu equipo."
                                        : "For pastors, directors, group leaders, and volunteers: jump straight into your ministry specialist."}
                                </CardDescription>
                            </div>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                            {[
                                {
                                    title: isEs ? "Líderes de Grupos Pequeños" : "Small Group Leaders",
                                    desc: isEs ? "Cómo guiar la charla, cuidar personas y facilitar el grupo" : "Facilitate discussions and care for your group",
                                    director: "Adultos (Grupos)",
                                },
                                {
                                    title: isEs ? "Líderes y Maestros de Niños" : "Kids Leaders & Teachers",
                                    desc: isEs ? "Ministerio familiar, seguridad infantil y trato con padres" : "Family ministry, child safety, and parent connection",
                                    director: "Niños (NextGen)",
                                },
                                {
                                    title: isEs ? "Líderes de Jóvenes y Mentores" : "Youth Leaders & Mentors",
                                    desc: isEs ? "Conectar con adolescentes, dinámicas y fe relevante" : "Connect with students and lead youth groups",
                                    director: "Estudiantes",
                                },
                                {
                                    title: isEs ? "Atención al Invitado y Anfitriones" : "Guest Services & Hosts",
                                    desc: isEs ? "Primera impresión desde el estacionamiento hasta el auditorio" : "First impressions from parking lot to auditorium",
                                    director: "Servicios a Invitados",
                                },
                                {
                                    title: isEs ? "Producción, Audio y Creativos" : "Production, Audio & Media",
                                    desc: isEs ? "Excelencia técnica, escaleta de 70m y cero distracciones" : "Technical excellence and distraction-free services",
                                    director: "Media (Creativos)",
                                },
                                {
                                    title: isEs ? "Pastores y Dirección General" : "Pastors & Ministry Directors",
                                    desc: isEs ? "Visión, predicación, cultura de equipo y principios estratégicos" : "Vision, preaching, team culture, and strategic principles",
                                    director: "Pastor Principal",
                                },
                            ].map((item) => (
                                <Link
                                    key={item.director}
                                    href={`/chat?director=${encodeURIComponent(item.director)}`}
                                    className="group p-3.5 rounded-xl border border-border bg-secondary/30 hover:bg-secondary/70 hover:border-primary/40 transition-all flex items-start justify-between gap-2"
                                >
                                    <div className="space-y-1">
                                        <p className="text-xs font-bold text-foreground group-hover:text-primary transition-colors">
                                            {item.title}
                                        </p>
                                        <p className="text-[11px] text-muted-foreground leading-snug">
                                            {item.desc}
                                        </p>
                                    </div>
                                    <ArrowRight className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary shrink-0 mt-0.5" />
                                </Link>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Recent Activity Columns */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Recent Director Sessions */}
                    <Card className="bg-card border-border shadow-2xs">
                        <CardHeader className="pb-3">
                            <CardTitle className="flex items-center gap-2 text-base font-heading">
                                <Clock className="h-4 w-4 text-primary" />
                                {isEs ? "Consultas Estratégicas Recientes" : "Recent Director Consultations"}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {isLoadingChats ? (
                                <p className="text-xs text-muted-foreground py-4">
                                    {isEs ? "Cargando sesiones..." : "Loading sessions..."}
                                </p>
                            ) : recentChats.length === 0 ? (
                                <div className="text-center py-6 space-y-2">
                                    <p className="text-xs text-muted-foreground">
                                        {isEs ? "Aún no tienes sesiones guardadas." : "No saved sessions yet."}
                                    </p>
                                    <Link href="/chat">
                                        <Button variant="outline" size="sm" className="text-xs">
                                            {isEs ? "Consultar a un Especialista" : "Ask a Specialist"}
                                        </Button>
                                    </Link>
                                </div>
                            ) : (
                                <div className="space-y-2.5">
                                    {recentChats.map((chat) => (
                                        <Link href="/chat" key={chat.id} className="block">
                                            <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 hover:bg-secondary transition-colors border border-border/60">
                                                <div className="min-w-0 flex-1 pr-3">
                                                    <p className="font-medium text-xs text-foreground truncate">{chat.title}</p>
                                                    <p className="text-[11px] text-muted-foreground mt-0.5">{chat.director}</p>
                                                </div>
                                                <span className="text-[11px] text-muted-foreground shrink-0">
                                                    {chat.updated_at &&
                                                        formatDistanceToNow(new Date(chat.updated_at), {
                                                            addSuffix: true,
                                                            locale: dateLocale,
                                                        })}
                                                </span>
                                            </div>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>

                    {/* Dojo Progress */}
                    <Card className="bg-card border-border shadow-2xs">
                        <CardHeader className="pb-3">
                            <CardTitle className="flex items-center gap-2 text-base font-heading">
                                <Trophy className="h-4 w-4 text-primary" />
                                {isEs ? "Entrenamientos Completados" : "Completed Leadership Trainings"}
                            </CardTitle>
                        </CardHeader>
                        <CardContent>
                            {isLoadingDojo ? (
                                <p className="text-xs text-muted-foreground py-4">
                                    {isEs ? "Cargando entrenamientos..." : "Loading trainings..."}
                                </p>
                            ) : dojoProgress.length === 0 ? (
                                <div className="text-center py-6 space-y-2">
                                    <p className="text-xs text-muted-foreground">
                                        {isEs
                                            ? "Aún no has completado simulaciones con tu equipo."
                                            : "No simulations completed yet."}
                                    </p>
                                    <Link href="/dojo">
                                        <Button variant="outline" size="sm" className="text-xs">
                                            {isEs ? "Practicar un Escenario" : "Practice a Scenario"}
                                        </Button>
                                    </Link>
                                </div>
                            ) : (
                                <div className="space-y-2.5">
                                    {dojoProgress.map((comp) => (
                                        <div
                                            key={comp.id}
                                            className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/60"
                                        >
                                            <div className="flex items-center gap-2.5 min-w-0">
                                                <CheckCircle className="h-4 w-4 text-green-600 shrink-0" />
                                                <div className="min-w-0">
                                                    <p className="font-medium text-xs text-foreground truncate">{comp.scenario_name}</p>
                                                    <p className="text-[11px] text-muted-foreground">
                                                        {comp.completed_at &&
                                                            formatDistanceToNow(new Date(comp.completed_at), {
                                                                addSuffix: true,
                                                                locale: dateLocale,
                                                            })}
                                                    </p>
                                                </div>
                                            </div>
                                            <span className="px-2 py-0.5 rounded-md font-bold text-xs bg-primary/12 text-primary">
                                                {comp.score}/10
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
