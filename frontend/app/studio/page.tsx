"use client";

import { useState, useEffect, useRef, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Markdown } from "@/components/ui/markdown";
import { api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import {
    BookOpen,
    Users,
    Heart,
    Clock,
    Share2,
    Sparkles,
    FileDown,
    Copy,
    Check,
    Search,
    Library,
    ArrowRight,
    Loader2,
    Printer,
    ExternalLink,
    Layers,
    Paperclip,
} from "lucide-react";

interface SundayPack {
    sermon: string;
    guide: string;
    kids: string;
    runsheet: string;
    social: string;
}

interface BrandfolderAsset {
    id: string;
    name: string;
    description: string;
    thumbnail_url?: string;
    tags?: string[];
    attachments?: {
        id: string;
        url: string;
        filename: string;
        mimetype: string;
    }[];
}

const CURATED_PRESETS = [
    {
        title: "Cómo no ser tu peor enemigo",
        series: "Decisiones Inteligentes",
        scripture: "Proverbios 27:12 / Efesios 5:15-17",
        topic: "Cómo tomar decisiones hoy que no saboteen nuestro futuro familiar, espiritual y financiero. La diferencia entre preguntar '¿tiene algo de malo?' y '¿qué es lo más sabio?'.",
    },
    {
        title: "Punto de Partida: Cuando la fe se vuelve difícil",
        series: "Punto de Partida",
        scripture: "Mateo 7:24-27",
        topic: "Para personas que crecieron con dudas o se alejaron de la iglesia por malas experiencias. Cómo reconstruir una fe auténtica basada en Jesús y no en reglas religiosas.",
    },
    {
        title: "Paz en medio del caos familiar",
        series: "Futuro Familiar",
        scripture: "Colosenses 3:12-15",
        topic: "Cómo manejar el conflicto en el matrimonio y con los hijos reemplazando la culpa y el orgullo por la gracia práctica durante la semana.",
    },
    {
        title: "Generosidad que transforma la ciudad",
        series: "Ricos en Buenas Obras",
        scripture: "1 Timoteo 6:17-19",
        topic: "Por qué dar y servir a nuestra comunidad rompe el poder del materialismo y refleja el corazón de Dios ante quienes no asisten a la iglesia.",
    },
];

const LIBRARY_CATEGORIES = [
    { label: "Series Destacadas", query: "series" },
    { label: "Matrimonio y Familia", query: "matrimonio" },
    { label: "Grupos Pequeños", query: "grupos" },
    { label: "Niños y Familia", query: "niños" },
    { label: "Jóvenes", query: "jóvenes" },
    { label: "Voluntarios", query: "voluntarios" },
    { label: "Bienvenida e Invitados", query: "invitados" },
    { label: "Generosidad e Impacto", query: "generosidad" },
];

function StudioContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { language } = useLanguage();
    const isEs = language === "es";

    const [activeWorkspaceTab, setActiveWorkspaceTab] = useState<string>("generator");

    // Pack Generator State
    const [topic, setTopic] = useState("");
    const [seriesName, setSeriesName] = useState("");
    const [scripture, setScripture] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [pack, setPack] = useState<SundayPack | null>(null);
    const [activeDeliverable, setActiveDeliverable] = useState<keyof SundayPack>("sermon");
    const [copiedKey, setCopiedKey] = useState<string | null>(null);
    const [isExportingDocx, setIsExportingDocx] = useState(false);
    const [isUploadingStudioDoc, setIsUploadingStudioDoc] = useState(false);
    const studioFileInputRef = useRef<HTMLInputElement>(null);

    const handleStudioFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        setIsUploadingStudioDoc(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await api.post("/chat/extract-document", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            const extracted = (res.data?.text || "").trim();
            if (extracted) {
                setTopic(extracted.slice(0, 6000));
                if (!seriesName.trim() && res.data?.filename) {
                    setSeriesName(res.data.filename.replace(/\.[^/.]+$/, ""));
                }
            }
        } catch (err: any) {
            console.error("Studio doc upload failed:", err);
            alert(err?.response?.data?.detail || "No se pudo leer el documento.");
        } finally {
            setIsUploadingStudioDoc(false);
            if (studioFileInputRef.current) studioFileInputRef.current.value = "";
        }
    };

    // Brandfolder Library State
    const [searchQuery, setSearchQuery] = useState("");
    const [isSearching, setIsSearching] = useState(false);
    const [assets, setAssets] = useState<BrandfolderAsset[]>([]);
    const [hasSearched, setHasSearched] = useState(false);

    // Initialize from query params if launched from Dashboard
    useEffect(() => {
        const qTopic = searchParams.get("topic");
        const qSeries = searchParams.get("series");
        const qScripture = searchParams.get("scripture");
        const qTab = searchParams.get("tab");

        if (qTab === "library") {
            setActiveWorkspaceTab("library");
            handleLibrarySearch("series");
        }
        if (qTopic) {
            setTopic(qTopic);
            if (qSeries) setSeriesName(qSeries);
            if (qScripture) setScripture(qScripture);
        }
    }, [searchParams]);

    const handleGeneratePack = async (overrideTopic?: string, overrideSeries?: string, overrideScripture?: string) => {
        const finalTopic = (overrideTopic ?? topic).trim();
        if (!finalTopic) return;

        setIsGenerating(true);
        try {
            const response = await api.post("/magic/sunday-pack", {
                topic: finalTopic,
                series_name: (overrideSeries ?? seriesName).trim() || undefined,
                scripture: (overrideScripture ?? scripture).trim() || undefined,
                language: language,
            });
            setPack(response.data.pack);
            setActiveDeliverable("sermon");
        } catch (err) {
            console.error("Failed to generate Sunday pack:", err);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleApplyPreset = (preset: typeof CURATED_PRESETS[0]) => {
        setTopic(preset.topic);
        setSeriesName(preset.series);
        setScripture(preset.scripture);
        handleGeneratePack(preset.topic, preset.series, preset.scripture);
    };

    const handleCopy = (key: keyof SundayPack) => {
        if (!pack) return;
        navigator.clipboard.writeText(pack[key]);
        setCopiedKey(key);
        setTimeout(() => setCopiedKey(null), 2000);
    };

    const handleExportDocx = async (key?: keyof SundayPack) => {
        if (!pack) return;
        setIsExportingDocx(true);
        try {
            const labels: Record<keyof SundayPack, string> = {
                sermon: "Bosquejo de Predicación",
                guide: "Guía de Grupos Pequeños",
                kids: "Lección de Niños y Familia",
                runsheet: "Orden del Servicio (Run Sheet)",
                social: "Pack Digital y WhatsApp",
            };

            const historyPayload = key
                ? [{ role: "assistant", content: `# ${labels[key]}\n\n${pack[key]}` }]
                : (Object.keys(labels) as (keyof SundayPack)[]).map((k) => ({
                      role: "assistant",
                      content: `# ${labels[k]}\n\n${pack[k]}`,
                  }));

            const docTitle = seriesName
                ? `${seriesName} - ${key ? labels[key] : "Pack Dominical Completo"}`
                : `Pack Dominical - ${key ? labels[key] : topic.slice(0, 40)}`;

            const response = await api.post(
                "/chat/export",
                {
                    history: historyPayload,
                    title: docTitle,
                },
                { responseType: "blob" }
            );

            const blob = new Blob([response.data], {
                type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            const dateStr = new Date().toISOString().slice(0, 10);
            link.setAttribute("download", `Pack-Dominical-${dateStr}.docx`);
            document.body.appendChild(link);
            link.click();
            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);
        } catch (err) {
            console.error("Error exporting DOCX:", err);
        } finally {
            setIsExportingDocx(false);
        }
    };

    const handleLibrarySearch = async (q?: string) => {
        const targetQuery = (q ?? searchQuery).trim();
        if (!targetQuery) return;
        if (q) setSearchQuery(q);

        setIsSearching(true);
        setHasSearched(true);
        try {
            const res = await api.post("/brandfolder/search", { query: targetQuery });
            setAssets(res.data.results || []);
        } catch (err) {
            console.error("Brandfolder search failed:", err);
            setAssets([]);
        } finally {
            setIsSearching(false);
        }
    };

    const stripHtml = (html: string) => {
        if (!html) return "";
        return html.replace(/<[^>]*>?/gm, " ").replace(/\s+/g, " ").trim();
    };

    const handleAdaptAssetToSunday = (asset: BrandfolderAsset) => {
        const cleanDesc = stripHtml(asset.description);
        const combinedTopic = `${asset.name}. ${cleanDesc}`.slice(0, 600);
        setSeriesName(asset.name);
        setTopic(combinedTopic);
        setActiveWorkspaceTab("generator");
        handleGeneratePack(combinedTopic, asset.name, "");
    };

    const DELIVERABLE_TABS: { key: keyof SundayPack; label: string; subtitle: string; icon: any }[] = [
        {
            key: "sermon",
            label: isEs ? "1. Bosquejo de Predicación" : "1. Sermon Outline",
            subtitle: isEs ? "Mapa Narrativo (YO-NOSOTROS-DIOS-TÚ-NOSOTROS)" : "5-Movement Map (ME-WE-GOD-YOU-WE)",
            icon: BookOpen,
        },
        {
            key: "guide",
            label: isEs ? "2. Guía de Grupos" : "2. Small Group Guide",
            subtitle: isEs ? "Rompehielo + 4 Preguntas Abiertas + Reto" : "Icebreaker + 4 Open Questions + Challenge",
            icon: Users,
        },
        {
            key: "kids",
            label: isEs ? "3. Niños y Familia" : "3. Kids & Family",
            subtitle: isEs ? "Lección Infantil + Conexión con Padres" : "Kids Lesson + Parent Connection",
            icon: Heart,
        },
        {
            key: "runsheet",
            label: isEs ? "4. Orden del Servicio" : "4. Service Run Sheet",
            subtitle: isEs ? "Minuto a Minuto (70m) + Guiones del Host" : "Minute-by-Minute (70m) + Host Scripts",
            icon: Clock,
        },
        {
            key: "social",
            label: isEs ? "5. Redes y WhatsApp" : "5. Social & WhatsApp",
            subtitle: isEs ? "Reel + Carrusel + Difusión de Viernes" : "Reel + Carousel + Friday Broadcast",
            icon: Share2,
        },
    ];

    return (
        <DashboardLayout>
            <div className="space-y-6 pb-12">
                {/* Editorial Header */}
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-border pb-5">
                    <div>
                        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary mb-1">
                            <Layers className="h-3.5 w-3.5" />
                            {isEs ? "Recursos y Materiales en 1 Clic" : "1-Click Ministry Resources"}
                        </div>
                        <h1 className="text-2xl md:text-3xl font-bold font-heading text-foreground">
                            {isEs ? "Prepara tu Semana en Minutos" : "Prepare Your Week in Minutes"}
                        </h1>
                        <p className="text-sm text-muted-foreground mt-1 max-w-2xl">
                            {isEs
                                ? "Transforma una idea, documento o serie de la Biblioteca Irresistible Agent en los 5 materiales listos para tus grupos, equipos y servicio."
                                : "Transform a topic, document, or series from the Irresistible Agent Library into the 5 operational materials for your groups, teams, and service."}
                        </p>
                    </div>

                    <Tabs
                        value={activeWorkspaceTab}
                        onValueChange={(v) => {
                            setActiveWorkspaceTab(v);
                            if (v === "library" && !hasSearched) {
                                handleLibrarySearch("series");
                            }
                        }}
                        className="w-full md:w-auto"
                    >
                        <TabsList className="h-10 bg-secondary/80 p-1 w-full md:w-auto grid grid-cols-2 md:inline-flex">
                            <TabsTrigger value="generator" className="gap-1.5 text-xs font-semibold px-2.5 sm:px-4">
                                <Sparkles className="h-3.5 w-3.5 shrink-0" />
                                <span className="truncate">{isEs ? "Generador Semanal" : "Weekly Generator"}</span>
                            </TabsTrigger>
                            <TabsTrigger value="library" className="gap-1.5 text-xs font-semibold px-2.5 sm:px-4">
                                <Library className="h-3.5 w-3.5 shrink-0" />
                                <span className="truncate">{isEs ? "Biblioteca (1,821)" : "Library (1,821)"}</span>
                            </TabsTrigger>
                        </TabsList>
                    </Tabs>
                </div>

                {activeWorkspaceTab === "generator" ? (
                    <div className="space-y-8">
                        {/* Input Studio Box */}
                        <Card className="border-border shadow-xs bg-card">
                            <CardHeader className="pb-4">
                                <CardTitle className="text-lg font-heading">
                                    {isEs ? "¿De qué trata el mensaje de este domingo?" : "What is this Sunday's message about?"}
                                </CardTitle>
                                <CardDescription>
                                    {isEs
                                        ? "Escribe tu idea central, pega tus notas preliminares o elige una de las series probadas debajo."
                                        : "Write your main idea, paste your rough notes, or choose a proven series preset below."}
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-foreground/80">
                                            {isEs ? "Nombre de la Serie (Opcional)" : "Series Name (Optional)"}
                                        </label>
                                        <Input
                                            value={seriesName}
                                            onChange={(e) => setSeriesName(e.target.value)}
                                            placeholder={isEs ? "Ej. Decisiones que Importan / Futuro Familiar" : "e.g., Better Decisions, Fewer Regrets"}
                                            className="bg-background"
                                        />
                                    </div>
                                    <div className="space-y-1.5">
                                        <label className="text-xs font-semibold text-foreground/80">
                                            {isEs ? "Pasaje Bíblico Central (Opcional)" : "Key Scripture (Optional)"}
                                        </label>
                                        <Input
                                            value={scripture}
                                            onChange={(e) => setScripture(e.target.value)}
                                            placeholder={isEs ? "Ej. Mateo 11:28-30 / Efesios 4:32" : "e.g., Matthew 11:28-30"}
                                            className="bg-background"
                                        />
                                    </div>
                                </div>

                                <div className="space-y-2">
                                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                                        <label className="text-xs font-semibold text-foreground/80">
                                            {isEs ? "Tema, Tensión Humana o Bosquejo Preliminar *" : "Topic, Human Tension, or Draft Notes *"}
                                        </label>
                                        <input
                                            ref={studioFileInputRef}
                                            type="file"
                                            accept=".pdf,.docx,.pptx,.txt,.md"
                                            onChange={handleStudioFileUpload}
                                            className="hidden"
                                        />
                                        <Button
                                            type="button"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => studioFileInputRef.current?.click()}
                                            disabled={isUploadingStudioDoc || isGenerating}
                                            className="h-8 sm:h-7 w-full sm:w-auto text-xs gap-1.5"
                                        >
                                            {isUploadingStudioDoc ? (
                                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                            ) : (
                                                <Paperclip className="h-3.5 w-3.5" />
                                            )}
                                            {isEs ? "Subir Bosquejo (.docx, .pdf, .pptx)" : "Upload Draft (.docx, .pdf, .pptx)"}
                                        </Button>
                                    </div>
                                    <textarea
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        rows={4}
                                        placeholder={
                                            isEs
                                                ? "Ej. Cómo perdonar a alguien de tu familia cuando sientes que no lo merece, y por qué el rencor nos ata al pasado..."
                                                : "e.g., How to forgive a family member when it feels unfair..."
                                        }
                                        className="w-full rounded-lg border border-input bg-background px-3.5 py-2.5 text-sm shadow-2xs focus:outline-none focus:ring-2 focus:ring-ring"
                                    />
                                </div>

                                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
                                    <div className="flex flex-wrap items-center gap-1.5">
                                        <span className="text-xs font-medium text-muted-foreground mr-1">
                                            {isEs ? "Series listas:" : "Quick presets:"}
                                        </span>
                                        {CURATED_PRESETS.map((preset) => (
                                            <button
                                                key={preset.title}
                                                type="button"
                                                onClick={() => handleApplyPreset(preset)}
                                                disabled={isGenerating}
                                                className="text-xs px-2.5 py-1 rounded-full border border-border bg-secondary/50 hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-colors font-medium"
                                            >
                                                {preset.title}
                                            </button>
                                        ))}
                                    </div>

                                    <Button
                                        size="lg"
                                        onClick={() => handleGeneratePack()}
                                        disabled={isGenerating || !topic.trim()}
                                        className="w-full sm:w-auto shrink-0 font-semibold shadow-sm gap-2"
                                    >
                                        {isGenerating ? (
                                            <>
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                {isEs ? "Produciendo los 5 documentos..." : "Producing 5 documents..."}
                                            </>
                                        ) : (
                                            <>
                                                <Sparkles className="h-4 w-4" />
                                                {isEs ? "Producir Pack Dominical Completo" : "Produce Complete Sunday Pack"}
                                            </>
                                        )}
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>

                        {/* Loading Skeleton when generating */}
                        {isGenerating && (
                            <Card className="border-primary/20 bg-card p-8 text-center space-y-4">
                                <div className="h-12 w-12 rounded-2xl bg-primary/10 text-primary flex items-center justify-center mx-auto">
                                    <Loader2 className="h-6 w-6 animate-spin" />
                                </div>
                                <div className="space-y-1 max-w-md mx-auto">
                                    <h3 className="font-heading font-bold text-base">
                                        {isEs
                                            ? "Tu equipo ministerial está redactando los materiales de este domingo..."
                                            : "Your ministry team is drafting this Sunday's materials..."}
                                    </h3>
                                    <p className="text-xs text-muted-foreground">
                                        {isEs
                                            ? "Generando simultáneamente: Bosquejo de 5 Movimientos, Guía de Grupos Pequeños, Lección de Niños y Familia, Orden del Servicio (70m) y Pack de WhatsApp/Redes."
                                            : "Simultaneously generating Sermon Outline, Small Group Guide, Kids Lesson, 70m Run Sheet, and Social Pack."}
                                    </p>
                                </div>
                            </Card>
                        )}

                        {/* Editorial Document Canvas */}
                        {pack && !isGenerating && (
                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6 items-start">
                                {/* Left Deliverable Selector (Horizontal scrollable strip on mobile, vertical list on desktop) */}
                                <div className="lg:col-span-4 space-y-2 min-w-0">
                                    <div className="px-1 pb-1 flex items-center justify-between">
                                        <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                                            {isEs ? "Entregables de la Semana (5)" : "Weekly Deliverables (5)"}
                                        </span>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleExportDocx()}
                                            disabled={isExportingDocx}
                                            className="h-7 text-xs gap-1.5"
                                        >
                                            <FileDown className="h-3.5 w-3.5" />
                                            {isEs ? "Descargar Todo (.docx)" : "Download All (.docx)"}
                                        </Button>
                                    </div>

                                    <div className="flex lg:flex-col gap-2 overflow-x-auto pb-1 lg:pb-0 no-scrollbar">
                                        {DELIVERABLE_TABS.map((item) => {
                                            const Icon = item.icon;
                                            const isSelected = activeDeliverable === item.key;
                                            return (
                                                <button
                                                    key={item.key}
                                                    onClick={() => setActiveDeliverable(item.key)}
                                                    className={`shrink-0 lg:w-full text-left p-2.5 lg:p-3.5 rounded-xl border transition-all flex items-center lg:items-start gap-2.5 lg:gap-3.5 ${
                                                        isSelected
                                                            ? "bg-card border-primary shadow-xs ring-1 ring-primary/20"
                                                            : "bg-card/60 border-border hover:bg-card hover:border-border/90"
                                                    }`}
                                                >
                                                    <div
                                                        className={`h-8 w-8 lg:h-9 lg:w-9 rounded-lg flex items-center justify-center shrink-0 lg:mt-0.5 ${
                                                            isSelected
                                                                ? "bg-primary text-primary-foreground"
                                                                : "bg-secondary text-muted-foreground"
                                                        }`}
                                                    >
                                                        <Icon className="h-4 w-4" />
                                                    </div>
                                                    <div className="min-w-0 flex-1">
                                                        <p className={`text-xs lg:text-sm font-semibold whitespace-nowrap lg:whitespace-normal ${isSelected ? "text-primary" : "text-foreground"}`}>
                                                            {item.label}
                                                        </p>
                                                        <p className="hidden lg:block text-xs text-muted-foreground truncate mt-0.5">
                                                            {item.subtitle}
                                                        </p>
                                                    </div>
                                                </button>
                                            );
                                        })}
                                    </div>
                                </div>

                                {/* Right Document Sheet (Canvas) */}
                                <div className="lg:col-span-8">
                                    <Card className="border-border shadow-sm bg-card overflow-hidden">
                                        <div className="px-6 py-4 border-b border-border bg-secondary/30 flex flex-wrap items-center justify-between gap-3">
                                            <div>
                                                <Badge variant="secondary" className="text-[11px] font-semibold mb-1">
                                                    {seriesName || (isEs ? "Documento Oficial del Domingo" : "Official Sunday Document")}
                                                </Badge>
                                                <h2 className="text-lg font-bold font-heading text-foreground">
                                                    {DELIVERABLE_TABS.find((d) => d.key === activeDeliverable)?.label}
                                                </h2>
                                            </div>

                                            <div className="flex items-center gap-2">
                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleCopy(activeDeliverable)}
                                                    className="h-8 text-xs gap-1.5"
                                                >
                                                    {copiedKey === activeDeliverable ? (
                                                        <>
                                                            <Check className="h-3.5 w-3.5 text-green-600" />
                                                            {isEs ? "¡Copiado!" : "Copied!"}
                                                        </>
                                                    ) : (
                                                        <>
                                                            <Copy className="h-3.5 w-3.5" />
                                                            {isEs ? "Copiar Texto" : "Copy Text"}
                                                        </>
                                                    )}
                                                </Button>

                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => handleExportDocx(activeDeliverable)}
                                                    disabled={isExportingDocx}
                                                    className="h-8 text-xs gap-1.5"
                                                >
                                                    <FileDown className="h-3.5 w-3.5" />
                                                    Word (.docx)
                                                </Button>

                                                <Button
                                                    variant="outline"
                                                    size="sm"
                                                    onClick={() => window.print()}
                                                    className="h-8 text-xs gap-1.5 hidden sm:inline-flex"
                                                >
                                                    <Printer className="h-3.5 w-3.5" />
                                                    PDF / Imprimir
                                                </Button>
                                            </div>
                                        </div>

                                        <CardContent className="p-6 md:p-8 max-w-none prose prose-stone dark:prose-invert">
                                            <Markdown>{pack[activeDeliverable]}</Markdown>
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    /* TAB 2: BRANDFOLDER ICN CATALOG FOR ALL USERS */
                    <div className="space-y-6">
                        <Card className="border-border bg-card shadow-xs">
                            <CardContent className="pt-6 space-y-4">
                                <div className="flex flex-col sm:flex-row gap-2">
                                    <div className="relative flex-1">
                                        <Search className="h-4 w-4 text-muted-foreground absolute left-3.5 top-1/2 -translate-y-1/2" />
                                        <Input
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleLibrarySearch()}
                                            placeholder={
                                                isEs
                                                    ? "Busca en los 1,821 recursos de la Biblioteca Irresistible Agent (ej. Matrimonio, Niños, Grupos, Ansiedad, Navidad)..."
                                                    : "Search 1,821 Irresistible Agent Library resources..."
                                            }
                                            className="pl-10 bg-background h-11"
                                        />
                                    </div>
                                    <Button
                                        size="lg"
                                        onClick={() => handleLibrarySearch()}
                                        disabled={isSearching}
                                        className="h-11 px-6 font-semibold"
                                    >
                                        {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : isEs ? "Buscar Recursos" : "Search Assets"}
                                    </Button>
                                </div>

                                <div className="flex flex-wrap items-center gap-1.5">
                                    <span className="text-xs font-medium text-muted-foreground mr-1">
                                        {isEs ? "Categorías rápidas:" : "Categories:"}
                                    </span>
                                    {LIBRARY_CATEGORIES.map((cat) => (
                                        <button
                                            key={cat.label}
                                            type="button"
                                            onClick={() => handleLibrarySearch(cat.query)}
                                            className="text-xs px-3 py-1 rounded-full border border-border bg-secondary/60 hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-colors font-medium"
                                        >
                                            {cat.label}
                                        </button>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>

                        {isSearching ? (
                            <div className="py-16 text-center space-y-3">
                                <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
                                <p className="text-sm text-muted-foreground">
                                    {isEs ? "Consultando la Biblioteca de Recursos Irresistible Agent..." : "Searching Irresistible Agent Library..."}
                                </p>
                            </div>
                        ) : assets.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                                {assets.map((asset) => {
                                    const cleanDescription = stripHtml(asset.description);
                                    return (
                                        <Card key={asset.id} className="border-border bg-card flex flex-col justify-between overflow-hidden hover:border-primary/40 transition-all shadow-xs">
                                            <div>
                                                {asset.thumbnail_url && (
                                                    <div className="h-40 w-full bg-secondary overflow-hidden border-b border-border relative">
                                                        {/* eslint-disable-next-line @next/next/no-img-element */}
                                                        <img
                                                            src={asset.thumbnail_url}
                                                            alt={asset.name}
                                                            className="w-full h-full object-cover"
                                                            loading="lazy"
                                                        />
                                                    </div>
                                                )}
                                                <CardHeader className="pb-2">
                                                    <CardTitle className="text-base font-heading line-clamp-2 leading-snug">
                                                        {asset.name}
                                                    </CardTitle>
                                                </CardHeader>
                                                <CardContent className="pb-4">
                                                    <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                                                        {cleanDescription || (isEs ? "Recurso de la Biblioteca Irresistible Agent." : "Irresistible Agent Library resource.")}
                                                    </p>
                                                    {asset.attachments && asset.attachments.length > 0 && (
                                                        <div className="mt-3 pt-3 border-t border-border/60 flex flex-wrap gap-1.5">
                                                            {asset.attachments.slice(0, 3).map((att) => (
                                                                <a
                                                                    key={att.id}
                                                                    href={att.url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded bg-secondary text-secondary-foreground hover:bg-primary/15 hover:text-primary transition-colors truncate max-w-[180px]"
                                                                >
                                                                    <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                                                                    <span className="truncate">{att.filename}</span>
                                                                </a>
                                                            ))}
                                                        </div>
                                                    )}
                                                </CardContent>
                                            </div>

                                            <div className="px-6 pb-5 pt-2">
                                                <Button
                                                    variant="default"
                                                    size="sm"
                                                    onClick={() => handleAdaptAssetToSunday(asset)}
                                                    className="w-full text-xs font-semibold gap-1.5"
                                                >
                                                    <Sparkles className="h-3.5 w-3.5" />
                                                    {isEs ? "Traducir y Crear Pack Dominical" : "Translate & Create Sunday Pack"}
                                                    <ArrowRight className="h-3.5 w-3.5 ml-auto" />
                                                </Button>
                                            </div>
                                        </Card>
                                    );
                                })}
                            </div>
                        ) : (
                            hasSearched && (
                                <Card className="p-12 text-center border-dashed">
                                    <p className="text-sm text-muted-foreground">
                                        {isEs
                                            ? "No se encontraron recursos con ese término. Prueba con una de las categorías rápidas arriba."
                                            : "No resources found. Try one of the quick categories above."}
                                    </p>
                                </Card>
                            )
                        )}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}

export default function StudioPage() {
    return (
        <Suspense fallback={<div className="p-12 text-center text-sm text-muted-foreground">Cargando Estudio Dominical...</div>}>
            <StudioContent />
        </Suspense>
    );
}
