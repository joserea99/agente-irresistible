"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Send, Bot, User, Loader2, FileDown, Users, Clock, Volume2, StopCircle, Sparkles } from "lucide-react";
import { useAuthStore, api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { motion, AnimatePresence } from "framer-motion";
import { ChatHistorySidebar } from "@/components/chat-history";
import { MicButton } from "@/components/ui/mic-button";
import { Markdown } from "@/components/ui/markdown";
import { useSpeechToText } from "@/hooks/use-speech-to-text";
import { useTextToSpeech } from "@/hooks/use-text-to-speech";

interface Director {
    id: string;
    name: string;
    key: string;
}

// Suggested starter prompts shown on the empty state, tailored per director.
const STARTER_PROMPTS: Record<string, string[]> = {
    "Pastor Principal": [
        "Ayúdame a redactar la visión de nuestra iglesia para este año en una frase memorable.",
        "Dame una estructura de sermón con Hook, Book, Look, Took sobre el perdón.",
        "¿Cómo manejo la resistencia del equipo ante un cambio de horario de servicio?",
    ],
    "Comunicador": [
        "Crea 5 ideas de publicaciones para redes para invitar a personas no creyentes.",
        "Escribe un correo de bienvenida para nuevos visitantes.",
        "¿Cómo comunicamos una nueva serie de predicaciones de forma irresistible?",
    ],
    "Programación de Servicio": [
        "Diseña un run sheet de un servicio dominical de 75 minutos.",
        "Ideas para mejorar la experiencia del foyer y la bienvenida.",
        "¿Cómo reclutar y retener voluntarios de servicio?",
    ],
    "Niños (NextGen)": [
        "Plan de seguridad infantil con los 5 Estándares de Oro.",
        "¿Cómo aplicar la estrategia Orange con las familias de nuestra iglesia?",
        "Ideas de un currículo de 4 semanas sobre la amabilidad para niños.",
    ],
    "Estudiantes": [
        "Diseña un retiro juvenil de fin de semana con tema y dinámicas.",
        "¿Cómo conecto a un adolescente nuevo a un grupo pequeño?",
        "Ideas para que los estudiantes inviten a sus amigos no creyentes.",
    ],
    "Adultos (Grupos)": [
        "Plan para lanzar grupos pequeños con un GroupLink.",
        "¿Cómo entreno a un líder de grupo con el modelo Lead Small?",
        "Preguntas de discusión para un grupo sobre la ansiedad.",
    ],
};

const DEFAULT_PROMPTS = [
    "¿Qué haría a nuestra iglesia irresistible para quienes no asisten?",
    "Explícame las 7 Prácticas de una iglesia irresistible con ejemplos.",
    "Ayúdame a definir 'el win' (la victoria) para mi área de ministerio.",
];

export default function ChatPage() {
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [directors, setDirectors] = useState<Director[]>([]);
    const [selectedDirector, setSelectedDirector] = useState<string>("Programación de Servicio");
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [showHistory, setShowHistory] = useState(false); // Start closed on mobile
    const [collaborateMode, setCollaborateMode] = useState(false);
    const [consultedDirectors, setConsultedDirectors] = useState<string[]>([]);

    const scrollRef = useRef<HTMLDivElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const { user } = useAuthStore();
    const { t, language } = useLanguage();

    // Mapping user roles to persona keys
    useEffect(() => {
        if (user && user.role) {
            const ROLE_TO_PERSONA_MAP: Record<string, string> = {
                "admin": "Pastor Principal",
                "pastor_principal": "Pastor Principal",
                "kids_director": "Niños (NextGen)",
                "students_director": "Estudiantes",
                "adults_director": "Adultos (Grupos)",
                "media_director": "Media (Creativos)",
                "service_director": "Programación de Servicio",
                "operations_director": "Servicios Ministeriales",
                "philosophy_director": "Filosofía y Modelo",
                "be_rich_director": "Be Rich"
            };
            
            if (ROLE_TO_PERSONA_MAP[user.role]) {
                setSelectedDirector(ROLE_TO_PERSONA_MAP[user.role]);
            }
        }
    }, [user]);

    // Voice Hooks — stabilize onResult with useCallback
    const handleVoiceResult = useCallback((text: string) => {
        setInput((prev) => prev + (prev && !prev.endsWith(' ') ? " " : "") + text);
    }, []);

    const { isListening, startListening, stopListening, hasSupport: hasMicSupport } = useSpeechToText({
        onResult: handleVoiceResult,
        language: language === 'es' ? 'es-US' : 'en-US'
    });

    const { speak, stop: stopSpeaking, isSpeaking } = useTextToSpeech();

    // Fetch directors on mount
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

    // Load Session (if selected)
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

    const submitMessage = async (text: string) => {
        const trimmed = text.trim();
        if (!trimmed || isLoading) return;

        setMessages((prev) => [...prev, { role: "user", content: trimmed }]);
        setInput("");
        setIsLoading(true);

        try {
            let response;
            setConsultedDirectors([]);

            if (collaborateMode) {
                // Multi-director consultation
                response = await api.post("/chat/consult", {
                    message: trimmed,
                    session_id: currentSessionId,
                    primary_director: selectedDirector,
                    auto_collaborate: true,
                    rag_enabled: true,
                });

                // Track which directors contributed
                const consulted = (response.data.consulted_directors || [])
                    .filter((d: { status: string }) => d.status === "success")
                    .map((d: { director: string }) => d.director);
                setConsultedDirectors(consulted);
            } else {
                // Standard single-director chat
                response = await api.post("/chat/message", {
                    message: trimmed,
                    session_id: currentSessionId,
                    director: selectedDirector,
                    rag_enabled: true,
                });
            }

            // Update session ID if new
            if (response.data.session_id && response.data.session_id !== currentSessionId) {
                setCurrentSessionId(response.data.session_id);
            }

            setMessages((prev) => [...prev, { role: "assistant", content: response.data.message }]);
        } catch (error) {
            console.error("Chat error:", error);
            setMessages((prev) => [...prev, { role: "assistant", content: "Error: No se pudo obtener respuesta del servidor." }]);
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
        setShowHistory(false); // Close sidebar on mobile
        // Optional: Focus input
    };

    const handleSelectSession = (id: string) => {
        setCurrentSessionId(id);
        setShowHistory(false); // Close sidebar on mobile
    };

    // ... Export function remains same ...
    const handleExportConversation = async () => {
        try {
            const response = await api.post("/chat/export", {
                history: messages,
                title: `Conversación - ${selectedDirector}`
            }, {
                responseType: 'blob'
            });

            // Create blob with correct MIME type
            const blob = new Blob([response.data], {
                type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            });

            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;

            // Clean filename
            const cleanDirector = selectedDirector.replace(/[^a-z0-9]/gi, '-');
            const timestamp = new Date().toISOString().slice(0, 10);
            link.setAttribute('download', `Conversacion-${cleanDirector}-${timestamp}.docx`);

            document.body.appendChild(link);
            link.click();

            // Cleanup
            setTimeout(() => {
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
            }, 100);

            console.log('✅ Archivo exportado exitosamente');
        } catch (error) {
            console.error("Export error:", error);
            alert("Error al exportar la conversación. Por favor intenta de nuevo.");
        }
    };

    return (
        <DashboardLayout>
            <div className="flex h-[calc(100vh-5rem)] md:h-[calc(100vh-8rem)] gap-0 md:gap-4 items-stretch relative">
                {/* Mobile overlay backdrop */}
                {showHistory && (
                    <div
                        className="fixed inset-0 bg-black/50 z-30 md:hidden"
                        onClick={() => setShowHistory(false)}
                    />
                )}

                {/* History Sidebar - Overlay on mobile, static on desktop */}
                <div className={`
                    fixed top-0 left-0 h-full w-72 z-40
                    transition-transform duration-200 ease-in-out
                    ${showHistory ? 'translate-x-0' : '-translate-x-full'}
                    md:relative md:translate-x-0 md:w-64 md:z-auto md:h-auto md:top-auto md:left-auto md:shrink-0
                    flex flex-col
                    ${!showHistory ? 'max-md:pointer-events-none' : ''}
                `}>
                    <ChatHistorySidebar
                        currentSessionId={currentSessionId}
                        onSelectSession={handleSelectSession}
                        onNewChat={handleNewChat}
                        className="rounded-lg border bg-card shadow-lg md:shadow-sm md:bg-card/50 h-full"
                    />
                </div>

                {/* Main Chat Area */}
                <div className="flex-1 flex flex-col min-w-0">
                    <div className="flex flex-col gap-2 mb-2 md:mb-4">
                        {/* Top row: history toggle + director selector + export */}
                        <div className="flex items-center gap-2">
                            <Button variant="outline" size="icon" className="md:hidden shrink-0 h-9 w-9" onClick={() => setShowHistory(!showHistory)}>
                                <Clock className="h-4 w-4" />
                            </Button>

                            {/* Director selector inline on mobile */}
                            <Select value={selectedDirector} onValueChange={setSelectedDirector}>
                                <SelectTrigger className="flex-1 md:w-[280px] md:flex-none h-9">
                                    <Users className="h-4 w-4 mr-2 shrink-0" />
                                    <SelectValue placeholder="Selecciona un director" />
                                </SelectTrigger>
                                <SelectContent>
                                    {directors.map((director) => (
                                        <SelectItem key={director.id} value={director.key}>
                                            {director.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>

                            {/* Collaborate Mode Toggle */}
                            <Button
                                variant={collaborateMode ? "default" : "outline"}
                                size="sm"
                                onClick={() => setCollaborateMode(!collaborateMode)}
                                title={collaborateMode ? "Modo Consejo activado" : "Activar Modo Consejo"}
                                className="shrink-0 h-9 gap-1.5 text-xs"
                            >
                                <Sparkles className="h-3.5 w-3.5" />
                                <span className="hidden sm:inline">Consejo</span>
                            </Button>

                            {messages.length > 0 && (
                                <Button
                                    variant="outline"
                                    size="icon"
                                    onClick={handleExportConversation}
                                    title="Exportar a Word"
                                    className="shrink-0 h-9 w-9"
                                >
                                    <FileDown className="h-4 w-4" />
                                </Button>
                            )}
                        </div>
                    </div>

                    <Card className="flex-1 flex flex-col overflow-hidden border-primary/20 bg-card/50 relative">
                        <div ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                            <div className="space-y-4 max-w-3xl mx-auto">
                                {messages.length === 0 && (
                                    <div className="py-12 md:py-16 px-2">
                                        <div className="text-center mb-8">
                                            <div className="h-14 w-14 mx-auto mb-4 rounded-2xl bg-primary/10 flex items-center justify-center">
                                                <Sparkles className="h-7 w-7 text-primary" />
                                            </div>
                                            <h2 className="text-lg font-semibold text-foreground">{selectedDirector}</h2>
                                            <p className="text-sm text-muted-foreground mt-1 max-w-md mx-auto">
                                                Tu consultor con acceso a la base de conocimiento de la Iglesia Irresistible. Pregunta lo que necesites o empieza con una idea:
                                            </p>
                                        </div>
                                        <div className="grid gap-2 max-w-2xl mx-auto sm:grid-cols-2">
                                            {(STARTER_PROMPTS[selectedDirector] || DEFAULT_PROMPTS).map((prompt) => (
                                                <button
                                                    key={prompt}
                                                    onClick={() => submitMessage(prompt)}
                                                    className="text-left text-sm rounded-xl border border-border bg-card/40 hover:bg-muted hover:border-primary/40 transition-colors px-4 py-3 text-foreground/90"
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
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            className={`flex items-start gap-4 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                                        >
                                            <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}>
                                                {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                            </div>
                                            <div className={`flex flex-col gap-2 max-w-[85%] sm:max-w-[80%]`}>
                                                <div className={`rounded-lg px-4 py-3 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground whitespace-pre-wrap" : "bg-muted"}`}>
                                                    {m.role === "user" ? m.content : <Markdown>{m.content}</Markdown>}
                                                </div>
                                                {/* TTS Button + Consulted Directors Badge */}
                                                {m.role === "assistant" && (
                                                    <div className="flex items-center gap-2 flex-wrap">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-6 w-6 p-0 rounded-full hover:bg-muted-foreground/10"
                                                            onClick={() => isSpeaking ? stopSpeaking() : speak(m.content, language === 'es' ? 'es-US' : 'en-US')}
                                                            title="Leer en voz alta"
                                                        >
                                                            {isSpeaking ? <StopCircle className="h-3 w-3" /> : <Volume2 className="h-3 w-3 opacity-50 hover:opacity-100" />}
                                                        </Button>
                                                        {/* Show consulted directors on the last assistant message */}
                                                        {i === messages.length - 1 && consultedDirectors.length > 0 && (
                                                            <div className="flex items-center gap-1 flex-wrap">
                                                                <Sparkles className="h-3 w-3 text-primary opacity-70" />
                                                                {consultedDirectors.map((d) => (
                                                                    <span key={d} className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded-full">
                                                                        {d}
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

                                {isLoading && (
                                    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start gap-4">
                                        <div className="h-8 w-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center shrink-0">
                                            <Bot className="h-4 w-4" />
                                        </div>
                                        <div className="bg-muted rounded-lg px-4 py-3 flex items-center gap-2">
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                            <span className="text-xs text-muted-foreground">Pensando...</span>
                                        </div>
                                    </motion.div>
                                )}
                                <div ref={scrollRef} />
                            </div>
                        </div>

                        <div className="p-4 bg-background/50 border-t border-border">
                            <form onSubmit={handleSend} className="max-w-3xl mx-auto flex gap-2">
                                <Input
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Escribe tu pregunta..."
                                    className="flex-1 bg-background"
                                    disabled={isLoading}
                                    autoFocus
                                />
                                {/* Mic Button */}
                                <MicButton
                                    isListening={isListening}
                                    onStart={startListening}
                                    onStop={stopListening}
                                    disabled={isLoading || !hasMicSupport}
                                />
                                <Button type="submit" size="icon" disabled={isLoading || !input.trim()}>
                                    <Send className="h-4 w-4" />
                                </Button>
                            </form>
                        </div>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
