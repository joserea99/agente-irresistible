"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
    Send,
    User,
    Loader2,
    FileDown,
    Users,
    Clock,
    Volume2,
    StopCircle,
    Sparkles,
    BookOpen,
    Copy,
    Check,
    X,
    Paperclip,
    FileText,
} from "lucide-react";
import { useAuthStore, api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { motion, AnimatePresence } from "framer-motion";
import { ChatHistorySidebar } from "@/components/chat-history";
import { MicButton } from "@/components/ui/mic-button";
import { Markdown } from "@/components/ui/markdown";
import { useSpeechToText } from "@/hooks/use-speech-to-text";
import { useTextToSpeech } from "@/hooks/use-text-to-speech";
import { useRouter } from "next/navigation";

interface Director {
    id: string;
    name: string;
    key: string;
}

interface AttachedDoc {
    filename: string;
    text: string;
    char_count: number;
    brandfolder_matches: { name: string; description: string; url: string }[];
}

const DIRECTOR_SUBTITLES: Record<string, string> = {
    "Pastor Principal": "Visión, Predicación y Claridad de Liderazgo",
    "Comunicador": "Estrategia Digital, Redes e Invitación",
    "Programación de Servicio": "Producción Dominical, Escaleta y Experiencia",
    "Niños (NextGen)": "Para Líderes, Maestros y Directores de Ministerio Infantil y Familiar",
    "Estudiantes": "Para Líderes de Jóvenes, Mentores y Pastoral Juvenil",
    "Adultos (Grupos)": "Para Líderes de Grupos Pequeños y Discipulado",
    "Servicios Ministeriales": "Operaciones, Voluntarios, Finanzas y Logística",
    "Media (Creativos)": "Para Equipos de Audio, Video, Luces y Diseño",
    "Filosofía y Modelo": "Principios Estratégicos y Cultura Ministerial",
    "Servicios a Invitados": "Para Anfitriones, Atención al Invitado y Estacionamiento",
    "Be Rich": "Para Líderes de Generosidad e Impacto Comunitario",
};

const STARTER_PROMPTS: Record<string, string[]> = {
    "Pastor Principal": [
        "Ayúdame a definir 'el Win' (la victoria) para que cada líder de mi equipo tenga claridad.",
        "Dame una estructura de mensaje YO-NOSOTROS-DIOS-TÚ-NOSOTROS sobre cómo superar el temor.",
        "¿Cómo manejo la resistencia o el cansancio del equipo ante un cambio importante?",
        "¿Cómo entreno a nuevos líderes sin sobrecargar a los voluntarios actuales?",
    ],
    "Adultos (Grupos)": [
        "Soy líder de grupo pequeño: ¿cómo logro que todos participen y nadie monopolice la charla?",
        "¿Cómo acompaño a alguien de mi grupo que está pasando por una crisis familiar?",
        "Explícame los 5 principios prácticos para cuidar y pastorear mi grupo esta semana.",
        "Plan paso a paso para lanzar nuevos grupos pequeños e integrar a personas nuevas.",
    ],
    "Niños (NextGen)": [
        "Soy líder/maestro de niños: ¿cómo conecto con los padres en los 60 segundos de entrega y recogida?",
        "¿Qué hago si un niño nuevo llora o no quiere integrarse a la actividad del salón?",
        "Entréname en los 5 Estándares de Oro de seguridad infantil para mi equipo.",
        "¿Cómo explicamos la alianza entre iglesia y familia de forma sencilla a nuevos voluntarios?",
    ],
    "Estudiantes": [
        "Soy líder de grupo de jóvenes: ¿cómo rompo el hielo con adolescentes que no quieren hablar?",
        "¿Cómo respondo cuando un adolescente me confía una duda difícil sobre su fe o familia?",
        "Ideas prácticas para que los chicos inviten a sus amigos del colegio este mes.",
        "Diseña un plan de entrenamiento rápido para nuevos líderes juveniles.",
    ],
    "Servicios a Invitados": [
        "Soy anfitrión de bienvenida: ¿cómo hago sentir en casa a alguien que llega solo por primera vez?",
        "¿Cuáles son los errores que debemos evitar en el lobby y estacionamiento los domingos?",
        "Dame una charla de 5 minutos (huddle) para inspirar a mi equipo de anfitriones antes del servicio.",
        "¿Cómo guiamos a una familia nueva hacia el área de niños sin que se sientan perdidos?",
    ],
    "Programación de Servicio": [
        "¿Cuál es 'el Win' de cada voluntario y líder durante los 70 minutos del servicio dominical?",
        "Diseña una escaleta (Run Sheet) fluida donde las transiciones no distraigan al visitante.",
        "¿Cómo damos retroalimentación constructiva al equipo después del servicio del domingo?",
        "Guion de bienvenida de 2 minutos enfocado en quienes nos visitan por primera vez.",
    ],
    "Media (Creativos)": [
        "Soy voluntario de audio/proyección/luces: ¿cómo preparo mi área para que haya cero distracciones?",
        "¿Qué protocolo seguimos cuando falla una pantalla o micrófono en pleno servicio?",
        "¿Cómo entrenamos a nuevos voluntarios técnicos desde cero sin abrumarlos?",
        "Checklist de excelencia técnica 45 minutos antes de abrir puertas.",
    ],
    "Comunicador": [
        "Crea 5 ideas de contenido digital pensadas para personas que no asisten a la iglesia.",
        "Escribe un mensaje de seguimiento cálido para quienes nos visitaron por primera vez este domingo.",
        "¿Cómo entrenamos a los líderes para comunicar anuncios con claridad en menos de 60 segundos?",
        "Estrategia de invitación por WhatsApp para que la congregación invite a sus amigos.",
    ],
    "Servicios Ministeriales": [
        "¿Cómo organizamos roles y turnos de voluntarios para evitar el agotamiento (burnout)?",
        "Plantilla para planificar un evento ministerial con claridad de responsables y presupuesto.",
        "¿Cómo tener una conversación saludable con un líder que no está cumpliendo sus compromisos?",
        "Checklist operativo de apertura y cierre de instalaciones el domingo.",
    ],
    "Filosofía y Modelo": [
        "Explícame las 7 Prácticas Estratégicas aplicadas a mi área de liderazgo.",
        "¿Qué significa 'pensar en pasos, no en programas' para mí como líder?",
        "¿Cómo le explico a un voluntario nuevo por qué diseñamos nuestros ambientes para el visitante?",
        "Ayúdame a evaluar si mi área está enfocada en 'círculos' o solo en 'filas'.",
    ],
    "Be Rich": [
        "¿Cómo inspiro a mi grupo pequeño a participar juntos en un proyecto de servicio comunitario?",
        "Explícame los 3 pilares de Generosidad (Dar, Servir, Amar) de forma práctica para mi equipo.",
        "Ideas de proyectos de impacto local donde familias enteras puedan servir juntas.",
        "¿Cómo comunicamos generosidad sin que la gente sienta que la iglesia solo pide dinero?",
    ],
};

const DEFAULT_PROMPTS = [
    "¿Qué haría a nuestra iglesia relevante para quienes no asisten a ninguna iglesia?",
    "Explícame las 7 Prácticas Estratégicas con pasos concretos para mi área.",
    "Ayúdame a definir 'el win' (la victoria) para mi área de ministerio este trimestre.",
];

function getDirectorInitials(name: string): string {
    const clean = name.replace(/\(.*\)/, "").trim();
    const parts = clean.split(/\s+/);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return clean.slice(0, 2).toUpperCase();
}

export default function ChatPage() {
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [directors, setDirectors] = useState<Director[]>([]);
    const [selectedDirector, setSelectedDirector] = useState<string>("Pastor Principal");
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [showHistory, setShowHistory] = useState(false);
    const [collaborateMode, setCollaborateMode] = useState(false);
    const [deepThinking, setDeepThinking] = useState(false);
    const [consultedDirectors, setConsultedDirectors] = useState<string[]>([]);
    const [canvasContent, setCanvasContent] = useState<string | null>(null);
    const [copiedCanvas, setCopiedCanvas] = useState(false);
    const [attachedDoc, setAttachedDoc] = useState<AttachedDoc | null>(null);
    const [isUploadingDoc, setIsUploadingDoc] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { user } = useAuthStore();
    const { language } = useLanguage();
    const router = useRouter();
    const isEs = language === "es";

    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    }, [input]);

    useEffect(() => {
        if (typeof window !== "undefined") {
            const params = new URLSearchParams(window.location.search);
            const qDirector = params.get("director");
            if (qDirector && DIRECTOR_SUBTITLES[qDirector]) {
                setSelectedDirector(qDirector);
                return;
            }
        }
        if (user && user.role) {
            const ROLE_TO_PERSONA_MAP: Record<string, string> = {
                admin: "Pastor Principal",
                pastor_principal: "Pastor Principal",
                kids_director: "Niños (NextGen)",
                students_director: "Estudiantes",
                adults_director: "Adultos (Grupos)",
                media_director: "Media (Creativos)",
                service_director: "Programación de Servicio",
                operations_director: "Servicios Ministeriales",
                philosophy_director: "Filosofía y Modelo",
                be_rich_director: "Be Rich",
            };

            if (ROLE_TO_PERSONA_MAP[user.role]) {
                setSelectedDirector(ROLE_TO_PERSONA_MAP[user.role]);
            }
        }
    }, [user]);

    const handleVoiceResult = useCallback((text: string) => {
        setInput((prev) => prev + (prev && !prev.endsWith(" ") ? " " : "") + text);
    }, []);

    const { isListening, startListening, stopListening, hasSupport: hasMicSupport } = useSpeechToText({
        onResult: handleVoiceResult,
        language: language === "es" ? "es-US" : "en-US",
    });

    const { speak, stop: stopSpeaking, isSpeaking } = useTextToSpeech();

    useEffect(() => {
        const fetchDirectors = async () => {
            try {
                const response = await api.get("/chat/directors");
                setDirectors(response.data.directors);
            } catch (error) {
                console.error("Error fetching directors:", error);
            }
        };
        fetchDirectors();
    }, []);

    useEffect(() => {
        if (!currentSessionId) {
            setMessages([]);
            return;
        }

        const loadSession = async () => {
            setIsLoading(true);
            try {
                const response = await api.get(`/chat/session/${currentSessionId}`);
                setMessages(response.data.messages);
            } catch (error) {
                console.error("Error loading session:", error);
            } finally {
                setIsLoading(false);
            }
        };
        loadSession();
    }, [currentSessionId]);

    useEffect(() => {
        if (chatContainerRef.current) {
            chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
        }
    }, [messages, isLoading]);

    const streamChat = async (trimmed: string) => {
        const token = useAuthStore.getState().token;
        const baseURL = api.defaults.baseURL || "";

        const res = await fetch(`${baseURL}/chat/stream`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({
                message: trimmed,
                session_id: currentSessionId,
                director: selectedDirector,
                rag_enabled: true,
                deep_thinking: deepThinking,
            }),
        });

        if (!res.ok || !res.body) {
            throw new Error(`Stream failed: ${res.status}`);
        }

        const newSessionId = res.headers.get("X-Session-Id");

        setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let acc = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            acc += decoder.decode(value, { stream: true });
            setMessages((prev) => {
                const copy = [...prev];
                copy[copy.length - 1] = { role: "assistant", content: acc };
                return copy;
            });
        }

        if (newSessionId && newSessionId !== currentSessionId) {
            setCurrentSessionId(newSessionId);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploadingDoc(true);
        try {
            const formData = new FormData();
            formData.append("file", file);
            const res = await api.post("/chat/extract-document", formData, {
                headers: { "Content-Type": "multipart/form-data" },
            });
            setAttachedDoc(res.data);
            setDeepThinking(true);
        } catch (err: any) {
            console.error("Document upload failed:", err);
            alert(
                err?.response?.data?.detail ||
                    "No se pudo leer el documento. Sube un archivo .pdf, .docx, .pptx, .txt o .md"
            );
        } finally {
            setIsUploadingDoc(false);
            if (fileInputRef.current) fileInputRef.current.value = "";
        }
    };

    const submitMessage = async (text: string) => {
        const rawInput = text.trim();
        if ((!rawInput && !attachedDoc) || isLoading) return;

        const userInstruction =
            rawInput ||
            "Analiza este documento a la luz del conocimiento, principios y recursos de la Biblioteca Irresistible Agent. Señala sus fortalezas, áreas de mejora y recomendaciones prácticas.";

        const displayMessage = attachedDoc
            ? `📄 **Documento adjunto:** \`${attachedDoc.filename}\`\n\n${userInstruction}`
            : userInstruction;

        let backendPayloadMessage = userInstruction;
        if (attachedDoc) {
            const bfContext =
                attachedDoc.brandfolder_matches && attachedDoc.brandfolder_matches.length > 0
                    ? "\n\n### RECURSOS RELACIONADOS EN LA BIBLIOTECA IRRESISTIBLE AGENT:\n" +
                      attachedDoc.brandfolder_matches
                          .map((m) => `- **${m.name}**: ${m.description} (${m.url})`)
                          .join("\n")
                    : "";

            backendPayloadMessage = `${userInstruction}

---
### DOCUMENTO ADJUNTO POR EL USUARIO (${attachedDoc.filename}):
${attachedDoc.text}
${bfContext}
---
Por favor analiza el documento anterior a la luz de nuestra filosofía ministerial y los recursos de la Biblioteca Irresistible Agent.`;
        }

        setMessages((prev) => [...prev, { role: "user", content: displayMessage }]);
        setInput("");
        setAttachedDoc(null);
        setIsLoading(true);
        setConsultedDirectors([]);

        try {
            if (collaborateMode) {
                const response = await api.post("/chat/consult", {
                    message: backendPayloadMessage,
                    session_id: currentSessionId,
                    primary_director: selectedDirector,
                    auto_collaborate: true,
                    rag_enabled: true,
                });

                const consulted = (response.data.consulted_directors || [])
                    .filter((d: { status: string }) => d.status === "success")
                    .map((d: { director: string }) => d.director);
                setConsultedDirectors(consulted);

                if (response.data.session_id && response.data.session_id !== currentSessionId) {
                    setCurrentSessionId(response.data.session_id);
                }
                setMessages((prev) => [...prev, { role: "assistant", content: response.data.message }]);
            } else {
                await streamChat(backendPayloadMessage);
            }
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "⚠️ No se pudo conectar con el servidor en este momento. Por favor intenta de nuevo.",
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        submitMessage(input);
    };

    const handleNewChat = () => {
        setCurrentSessionId(null);
        setMessages([]);
        setShowHistory(false);
    };

    const handleSelectSession = (id: string) => {
        setCurrentSessionId(id);
        setShowHistory(false);
    };

    const handleExportConversation = async () => {
        try {
            const response = await api.post(
                "/chat/export",
                {
                    history: messages,
                    title: `Sesión Estratégica - ${selectedDirector}`,
                },
                {
                    responseType: "blob",
                }
            );

            const blob = new Blob([response.data], {
                type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            });

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;

            const cleanDirector = selectedDirector.replace(/[^a-z0-9]/gi, "-");
            const timestamp = new Date().toISOString().slice(0, 10);
            link.setAttribute("download", `Sesion-${cleanDirector}-${timestamp}.docx`);

            document.body.appendChild(link);
            link.click();

            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);
        } catch (error) {
            console.error("Export error:", error);
        }
    };

    const directorInitials = getDirectorInitials(selectedDirector);

    return (
        <DashboardLayout>
            <div className="flex h-[calc(100dvh-7.75rem)] md:h-[calc(100dvh-4rem)] gap-0 md:gap-4 items-stretch relative">
                {showHistory && (
                    <div
                        className="fixed inset-0 bg-black/40 z-30 md:hidden"
                        onClick={() => setShowHistory(false)}
                    />
                )}

                {/* History Sidebar */}
                <div
                    className={`
                    fixed top-0 left-0 h-full w-72 z-40
                    transition-transform duration-200 ease-in-out
                    ${showHistory ? "translate-x-0" : "-translate-x-full"}
                    md:relative md:translate-x-0 md:w-60 md:z-auto md:h-auto md:top-auto md:left-auto md:shrink-0
                    flex flex-col
                    ${!showHistory ? "max-md:pointer-events-none" : ""}
                `}
                >
                    <ChatHistorySidebar
                        currentSessionId={currentSessionId}
                        onSelectSession={handleSelectSession}
                        onNewChat={handleNewChat}
                        className="rounded-xl border border-border bg-card shadow-xs h-full"
                    />
                </div>

                {/* Main Consultation Area */}
                <div className="flex-1 flex flex-col min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2.5">
                        {/* Row 1 on mobile: History toggle + Specialist Selector + Export */}
                        <div className="flex items-center gap-2 w-full sm:w-auto">
                            <Button
                                variant="outline"
                                size="icon"
                                className="md:hidden shrink-0 h-9 w-9"
                                onClick={() => setShowHistory(!showHistory)}
                                title="Historial de conversaciones"
                            >
                                <Clock className="h-4 w-4" />
                            </Button>

                            <Select value={selectedDirector} onValueChange={setSelectedDirector}>
                                <SelectTrigger className="flex-1 sm:w-[250px] md:w-[270px] sm:flex-none h-9 bg-card font-medium text-xs sm:text-sm">
                                    <Users className="h-4 w-4 mr-1.5 text-primary shrink-0" />
                                    <SelectValue placeholder="Selecciona un especialista" />
                                </SelectTrigger>
                                <SelectContent>
                                    {directors.map((director) => (
                                        <SelectItem key={director.id} value={director.key}>
                                            {director.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            {messages.length > 0 && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleExportConversation}
                                    title="Exportar a Word (.docx)"
                                    className="sm:hidden shrink-0 h-9 px-2.5 gap-1 text-xs"
                                >
                                    <FileDown className="h-3.5 w-3.5" />
                                    <span>.docx</span>
                                </Button>
                            )}
                        </div>

                        {/* Row 2 on mobile / Right side on desktop: Mode & Document Actions */}
                        <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 sm:pb-0 no-scrollbar">
                            <Button
                                variant={deepThinking ? "default" : "outline"}
                                size="sm"
                                onClick={() => setDeepThinking(!deepThinking)}
                                title={
                                    deepThinking
                                        ? "Razonamiento profundo activo (diagnóstico pastoral + plan escalonado)"
                                        : "Activar razonamiento profundo para casos complejos o crisis"
                                }
                                className="shrink-0 h-8 sm:h-9 px-2.5 sm:px-3 gap-1.5 text-[11px] sm:text-xs font-medium"
                            >
                                <Sparkles className="h-3.5 w-3.5" />
                                <span>{isEs ? "Análisis Profundo" : "Deep Analysis"}</span>
                            </Button>

                            <Button
                                variant={collaborateMode ? "default" : "outline"}
                                size="sm"
                                onClick={() => setCollaborateMode(!collaborateMode)}
                                title={
                                    collaborateMode
                                        ? "Modo Consejo de Especialistas activado"
                                        : "Consultar a varios especialistas a la vez"
                                }
                                className="shrink-0 h-8 sm:h-9 px-2.5 sm:px-3 gap-1.5 text-[11px] sm:text-xs font-medium"
                            >
                                <Users className="h-3.5 w-3.5" />
                                <span>{isEs ? "Reunir Consejo" : "Council Mode"}</span>
                            </Button>

                            <Button
                                variant={attachedDoc ? "default" : "outline"}
                                size="sm"
                                onClick={() => fileInputRef.current?.click()}
                                disabled={isUploadingDoc}
                                title="Subir un documento (.pdf, .docx, .pptx, .txt) para analizarlo con la Biblioteca Irresistible Agent"
                                className="shrink-0 h-8 sm:h-9 px-2.5 sm:px-3 gap-1.5 text-[11px] sm:text-xs font-medium"
                            >
                                {isUploadingDoc ? (
                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                ) : (
                                    <Paperclip className="h-3.5 w-3.5" />
                                )}
                                <span>{isEs ? "Analizar Doc" : "Analyze Doc"}</span>
                            </Button>

                            {messages.length > 0 && (
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleExportConversation}
                                    title="Exportar a Word (.docx)"
                                    className="hidden sm:inline-flex shrink-0 h-9 gap-1.5 text-xs"
                                >
                                    <FileDown className="h-3.5 w-3.5" />
                                    <span className="hidden md:inline">Exportar (.docx)</span>
                                </Button>
                            )}
                        </div>
                    </div>

                    <div className="flex-1 flex gap-4 min-h-0">
                        {/* Conversation Sheet */}
                        <Card className="flex-1 flex flex-col overflow-hidden border-border bg-card shadow-xs relative">
                            <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-3.5 sm:p-5 md:p-6">
                                <div className="space-y-4 sm:space-y-5 max-w-3xl mx-auto">
                                    {messages.length === 0 && (
                                        <div className="py-3 sm:py-6 md:py-8 px-1 sm:px-2">
                                            {/* Quick Ministry Area Selector for Leaders & Volunteers */}
                                            <div className="mb-4 sm:mb-6 text-center">
                                                <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground block mb-2">
                                                    {isEs ? "¿En qué área sirves o lideras hoy?" : "Which ministry area are you leading today?"}
                                                </span>
                                                <div className="flex sm:flex-wrap items-center sm:justify-center gap-1.5 max-w-2xl mx-auto overflow-x-auto pb-1 sm:pb-0 no-scrollbar">
                                                    {[
                                                        { label: "Grupos Pequeños", key: "Adultos (Grupos)" },
                                                        { label: "Niños y Familia", key: "Niños (NextGen)" },
                                                        { label: "Jóvenes", key: "Estudiantes" },
                                                        { label: "Atención al Invitado / Anfitriones", key: "Servicios a Invitados" },
                                                        { label: "Producción y Media", key: "Media (Creativos)" },
                                                        { label: "Servicio Dominical", key: "Programación de Servicio" },
                                                        { label: "Pastor / Dirección", key: "Pastor Principal" },
                                                        { label: "Generosidad e Impacto", key: "Be Rich" },
                                                    ].map((area) => (
                                                        <button
                                                            key={area.key}
                                                            type="button"
                                                            onClick={() => setSelectedDirector(area.key)}
                                                            className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                                                                selectedDirector === area.key
                                                                    ? "bg-primary text-primary-foreground border-primary shadow-2xs"
                                                                    : "bg-secondary/50 text-foreground/80 border-border hover:border-primary/40 hover:text-foreground"
                                                            }`}
                                                        >
                                                            {area.label}
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="text-center mb-4 sm:mb-6">
                                                <div className="h-11 w-11 sm:h-14 sm:w-14 mx-auto mb-2.5 rounded-2xl bg-primary/12 text-primary flex items-center justify-center font-heading font-bold text-base sm:text-lg border border-primary/20">
                                                    {directorInitials}
                                                </div>
                                                <h2 className="text-lg sm:text-xl font-bold font-heading text-foreground">
                                                    {selectedDirector}
                                                </h2>
                                                <p className="text-xs font-medium text-primary mt-0.5">
                                                    {DIRECTOR_SUBTITLES[selectedDirector] || "Especialista Ministerial"}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-1.5 max-w-md mx-auto leading-relaxed">
                                                    {isEs
                                                        ? "Claridad y entrenamiento práctico para pastores, directores, líderes de área y voluntarios. Elige una pregunta o plantea tu situación:"
                                                        : "Clarity and practical coaching for pastors, directors, area leaders, and volunteers. Choose a prompt or ask your question:"}
                                                </p>
                                            </div>
                                            <div className="grid gap-2 max-w-2xl mx-auto sm:grid-cols-2">
                                                {(STARTER_PROMPTS[selectedDirector] || DEFAULT_PROMPTS).map((prompt) => (
                                                    <button
                                                        key={prompt}
                                                        onClick={() => submitMessage(prompt)}
                                                        className="text-left text-xs leading-relaxed rounded-xl border border-border bg-secondary/40 hover:bg-secondary hover:border-primary/40 transition-all px-3.5 py-3 text-foreground font-medium"
                                                    >
                                                        {prompt}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <AnimatePresence initial={false}>
                                        {messages.map((m, i) => (
                                            <motion.div
                                                key={i}
                                                initial={{ opacity: 0, y: 8 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className={`flex items-start gap-3.5 ${
                                                    m.role === "user" ? "flex-row-reverse" : "flex-row"
                                                }`}
                                            >
                                                <div
                                                    className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${
                                                        m.role === "user"
                                                            ? "bg-foreground text-background"
                                                            : "bg-primary/15 text-primary border border-primary/20"
                                                    }`}
                                                >
                                                    {m.role === "user" ? <User className="h-4 w-4" /> : directorInitials}
                                                </div>

                                                <div className="flex flex-col gap-1.5 max-w-[88%] sm:max-w-[82%]">
                                                    {m.role === "assistant" && (
                                                        <span className="text-[11px] font-semibold text-muted-foreground">
                                                            {selectedDirector}
                                                        </span>
                                                    )}
                                                    <div
                                                        className={`rounded-xl px-4 py-3.5 text-sm leading-relaxed ${
                                                            m.role === "user"
                                                                ? "bg-primary text-primary-foreground whitespace-pre-wrap"
                                                                : "bg-secondary/50 border border-border/70 text-foreground"
                                                        }`}
                                                    >
                                                        {m.role === "user" ? m.content : <Markdown>{m.content}</Markdown>}
                                                    </div>

                                                    {m.role === "assistant" && m.content && (
                                                        <div className="flex items-center gap-2 flex-wrap pt-0.5">
                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-6 px-2 text-[11px] text-muted-foreground hover:text-foreground gap-1"
                                                                onClick={() => setCanvasContent(m.content)}
                                                            >
                                                                <BookOpen className="h-3 w-3" />
                                                                {isEs ? "Abrir en Lienzo" : "Open in Canvas"}
                                                            </Button>

                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-6 px-2 text-[11px] text-primary hover:text-primary gap-1"
                                                                onClick={() =>
                                                                    router.push(
                                                                        `/studio?topic=${encodeURIComponent(
                                                                            m.content.slice(0, 350)
                                                                        )}`
                                                                    )
                                                                }
                                                            >
                                                                <Sparkles className="h-3 w-3" />
                                                                {isEs ? "Llevar a Prepara tu Semana" : "Send to Prepare Your Week"}
                                                            </Button>

                                                            <Button
                                                                variant="ghost"
                                                                size="sm"
                                                                className="h-6 w-6 p-0 rounded-full hover:bg-muted-foreground/10"
                                                                onClick={() =>
                                                                    isSpeaking
                                                                        ? stopSpeaking()
                                                                        : speak(m.content, language === "es" ? "es-US" : "en-US")
                                                                }
                                                                title="Leer en voz alta"
                                                            >
                                                                {isSpeaking ? (
                                                                    <StopCircle className="h-3 w-3" />
                                                                ) : (
                                                                    <Volume2 className="h-3 w-3 opacity-60 hover:opacity-100" />
                                                                )}
                                                            </Button>

                                                            {i === messages.length - 1 && consultedDirectors.length > 0 && (
                                                                <div className="flex items-center gap-1 flex-wrap">
                                                                    {consultedDirectors.map((d) => (
                                                                        <span
                                                                            key={d}
                                                                            className="text-[10px] bg-primary/12 text-primary px-2 py-0.5 rounded-full font-medium"
                                                                        >
                                                                            + {d}
                                                                        </span>
                                                                    ))}
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            </motion.div>
                                        ))}
                                    </AnimatePresence>

                                    {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
                                        <motion.div
                                            initial={{ opacity: 0 }}
                                            animate={{ opacity: 1 }}
                                            className="flex items-start gap-3.5"
                                        >
                                            <div className="h-8 w-8 rounded-lg bg-primary/15 text-primary flex items-center justify-center shrink-0 text-xs font-bold">
                                                {directorInitials}
                                            </div>
                                            <div className="bg-secondary/50 border border-border/70 rounded-xl px-4 py-3 flex items-center gap-2.5">
                                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                                <span className="text-xs text-muted-foreground font-medium">
                                                    {collaborateMode
                                                        ? "Reuniendo perspectivas del consejo de especialistas (Razonamiento Profundo)..."
                                                        : deepThinking
                                                        ? `Analizando caso en profundidad con ${selectedDirector}...`
                                                        : `Redactando propuesta de ${selectedDirector}...`}
                                                </span>
                                            </div>
                                        </motion.div>
                                    )}
                                    <div ref={scrollRef} />
                                </div>
                            </div>

                            <div className="p-3.5 bg-secondary/30 border-t border-border space-y-2">
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".pdf,.docx,.pptx,.txt,.md"
                                    onChange={handleFileUpload}
                                    className="hidden"
                                />

                                {/* Attached Document Preview Banner */}
                                {attachedDoc && (
                                    <div className="max-w-3xl mx-auto rounded-xl border border-primary/30 bg-card p-3 shadow-2xs space-y-2">
                                        <div className="flex items-center justify-between gap-2">
                                            <div className="flex items-center gap-2.5 min-w-0">
                                                <div className="h-8 w-8 rounded-lg bg-primary/12 text-primary flex items-center justify-center shrink-0">
                                                    <FileText className="h-4 w-4" />
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-xs font-bold text-foreground truncate">
                                                        {attachedDoc.filename}
                                                    </p>
                                                    <p className="text-[11px] text-muted-foreground">
                                                        {attachedDoc.char_count.toLocaleString()} caracteres extraídos · Listo para analizar con la Biblioteca Irresistible Agent
                                                    </p>
                                                </div>
                                            </div>
                                            <Button
                                                type="button"
                                                variant="ghost"
                                                size="icon"
                                                className="h-7 w-7 shrink-0"
                                                onClick={() => setAttachedDoc(null)}
                                            >
                                                <X className="h-3.5 w-3.5" />
                                            </Button>
                                        </div>
                                        <div className="flex flex-wrap items-center gap-1.5 pt-0.5">
                                            <span className="text-[10px] font-semibold text-muted-foreground mr-1">
                                                Acción en 1 clic:
                                            </span>
                                            {[
                                                "Analiza este documento a la luz de la Biblioteca Irresistible Agent y dime cómo mejorarlo.",
                                                "Evalúa si este material aplica los principios estratégicos y el enfoque en el visitante.",
                                                "Convierte este documento en una guía práctica paso a paso para los líderes de mi área.",
                                            ].map((quickPrompt) => (
                                                <button
                                                    key={quickPrompt}
                                                    type="button"
                                                    onClick={() => submitMessage(quickPrompt)}
                                                    className="text-[11px] px-2.5 py-1 rounded-full bg-primary/10 text-primary hover:bg-primary hover:text-primary-foreground transition-colors font-medium"
                                                >
                                                    {quickPrompt}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {(deepThinking || collaborateMode) && (
                                    <div className="max-w-3xl mx-auto flex items-center justify-between text-[11px] px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary font-medium">
                                        <span className="flex items-center gap-1.5">
                                            <Sparkles className="h-3.5 w-3.5 shrink-0" />
                                            {collaborateMode
                                                ? isEs
                                                    ? "Modo Consejo Activo: Varios especialistas analizarán tu caso con razonamiento profundo."
                                                    : "Council Mode Active: Multiple specialists will analyze your case with deep reasoning."
                                                : isEs
                                                ? "Análisis Profundo Activo: Incluye diagnóstico de fondo, principio rector, plan paso a paso y guion pastoral."
                                                : "Deep Analysis Active: Includes root diagnosis, guiding principle, step-by-step plan, and pastoral script."}
                                        </span>
                                    </div>
                                )}
                                <form onSubmit={handleSend} className="max-w-3xl mx-auto">
                                    <div className="flex items-end gap-2 rounded-2xl border border-border bg-card px-3 py-2 shadow-2xs focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary/50 transition-all">
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon"
                                            onClick={() => fileInputRef.current?.click()}
                                            disabled={isLoading || isUploadingDoc}
                                            title="Subir documento (.pdf, .docx, .pptx, .txt) para analizar con la Biblioteca Irresistible Agent"
                                            className="h-9 w-9 rounded-xl shrink-0 text-muted-foreground hover:text-primary hover:bg-primary/10 mb-0.5"
                                        >
                                            {isUploadingDoc ? (
                                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                                            ) : (
                                                <Paperclip className="h-4 w-4" />
                                            )}
                                        </Button>
                                        <textarea
                                            ref={textareaRef}
                                            rows={1}
                                            value={input}
                                            onChange={(e) => setInput(e.target.value)}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter" && !e.shiftKey) {
                                                    e.preventDefault();
                                                    if ((input.trim() || attachedDoc) && !isLoading) {
                                                        submitMessage(input);
                                                    }
                                                }
                                            }}
                                            placeholder={
                                                attachedDoc
                                                    ? isEs
                                                        ? `Escribe qué quieres analizar de "${attachedDoc.filename}" o presiona Enter...`
                                                        : `Write what to analyze in "${attachedDoc.filename}" or press Enter...`
                                                    : isEs
                                                    ? `Plantea tu consulta a ${selectedDirector} o adjunta un documento (📎)...`
                                                    : `Ask ${selectedDirector} or attach a document (📎)...`
                                            }
                                            className="flex-1 bg-transparent border-0 resize-none py-1.5 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none max-h-[200px] overflow-y-auto"
                                            disabled={isLoading}
                                            autoFocus
                                        />
                                        <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
                                            <MicButton
                                                isListening={isListening}
                                                onStart={startListening}
                                                onStop={stopListening}
                                                disabled={isLoading || !hasMicSupport}
                                            />
                                            <Button
                                                type="submit"
                                                size="icon"
                                                className="h-9 w-9 rounded-xl shrink-0"
                                                disabled={isLoading || (!input.trim() && !attachedDoc)}
                                            >
                                                <Send className="h-4 w-4" />
                                            </Button>
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </Card>

                        {/* Side-by-Side Document Canvas Drawer (Full-screen overlay on mobile, side panel on desktop) */}
                        {canvasContent && (
                            <Card className="fixed inset-0 z-50 lg:static lg:z-auto flex lg:w-[44%] flex-col border-border bg-card shadow-xl lg:shadow-sm overflow-hidden rounded-none lg:rounded-xl">
                                <div className="px-4 py-3 border-b border-border bg-secondary/40 flex items-center justify-between">
                                    <div>
                                        <span className="text-[10px] font-bold uppercase tracking-wider text-primary">
                                            {isEs ? "Lienzo Editorial" : "Editorial Canvas"}
                                        </span>
                                        <h3 className="text-sm font-bold font-heading text-foreground">
                                            {selectedDirector}
                                        </h3>
                                    </div>
                                    <div className="flex items-center gap-1.5">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="h-7 text-xs gap-1"
                                            onClick={() => {
                                                navigator.clipboard.writeText(canvasContent);
                                                setCopiedCanvas(true);
                                                setTimeout(() => setCopiedCanvas(false), 2000);
                                            }}
                                        >
                                            {copiedCanvas ? (
                                                <>
                                                    <Check className="h-3 w-3 text-green-600" />
                                                    Copiado
                                                </>
                                            ) : (
                                                <>
                                                    <Copy className="h-3 w-3" />
                                                    Copiar
                                                </>
                                            )}
                                        </Button>
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-7 w-7"
                                            onClick={() => setCanvasContent(null)}
                                        >
                                            <X className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto p-5 sm:p-6 prose prose-stone max-w-none text-sm">
                                    <Markdown>{canvasContent}</Markdown>
                                </div>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
