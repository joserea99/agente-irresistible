"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Send, Bot, User, Loader2, FileDown, Users, Clock, Volume2, StopCircle } from "lucide-react";
import { useAuthStore, api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { motion, AnimatePresence } from "framer-motion";
import { ChatHistorySidebar } from "@/components/chat-history";
import { MicButton } from "@/components/ui/mic-button";
import { useSpeechToText } from "@/hooks/use-speech-to-text";
import { useTextToSpeech } from "@/hooks/use-text-to-speech";

interface Director {
    id: string;
    name: string;
    key: string;
}

export default function ChatPage() {
    const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [directors, setDirectors] = useState<Director[]>([]);
    const [selectedDirector, setSelectedDirector] = useState<string>("Programación de Servicio");
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [showHistory, setShowHistory] = useState(true); // Toggle for desktop/mobile

    const scrollRef = useRef<HTMLDivElement>(null);
    const { user } = useAuthStore();
    const { t, language } = useLanguage();

    // Voice Hooks
    const { isListening, startListening, stopListening, hasSupport: hasMicSupport } = useSpeechToText({
        onResult: (text) => setInput((prev) => prev + (prev && !prev.endsWith(' ') ? " " : "") + text),
        language: language === 'es' ? 'es-ES' : 'en-US'
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
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" });
        }
    }, [messages, isLoading]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const newMessage = { role: "user", content: input };
        setMessages((prev) => [...prev, newMessage]);
        setInput("");
        setIsLoading(true);

        try {
            // Optimistic update

            const response = await api.post("/chat/message", {
                message: newMessage.content,
                session_id: currentSessionId, // Pass ID if exists
                director: selectedDirector,
                rag_enabled: false
            });

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
        // ...
    };

    return (
        <DashboardLayout>
            <div className="flex h-[calc(100vh-8rem)] gap-4 items-stretch">
                {/* History Sidebar - Hidden on mobile by default */}
                <div className={`${showHistory ? 'flex' : 'hidden'} md:flex w-full md:w-64 shrink-0 flex-col`}>
                    <ChatHistorySidebar
                        currentSessionId={currentSessionId}
                        onSelectSession={handleSelectSession}
                        onNewChat={handleNewChat}
                        className="rounded-lg border bg-card/50 shadow-sm h-full"
                    />
                </div>

                {/* Main Chat Area */}
                <div className="flex-1 flex flex-col min-w-0">
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                        <div className="flex flex-col gap-2">
                            <div className="flex items-center gap-2">
                                <Button variant="outline" size="icon" className="md:hidden" onClick={() => setShowHistory(!showHistory)}>
                                    <Clock className="h-4 w-4" />
                                </Button>
                                <h2 className="text-3xl font-bold font-heading">
                                    {directors.find(d => d.key === selectedDirector)?.name || "Agente Estratégico"}
                                </h2>
                            </div>
                            <p className="text-muted-foreground hidden sm:block">Consultoría estratégica especializada</p>
                        </div>

                        <div className="flex gap-2 items-center w-full sm:w-auto">
                            <Select value={selectedDirector} onValueChange={setSelectedDirector}>
                                <SelectTrigger className="w-full sm:w-[250px]">
                                    <Users className="h-4 w-4 mr-2" />
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

                            {messages.length > 0 && (
                                <div className="flex gap-2">
                                    <Button
                                        variant="outline"
                                        size="sm"
                                        onClick={handleExportConversation}
                                        title="Exportar a Word"
                                    >
                                        <FileDown className="h-4 w-4" />
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>

                    <Card className="flex-1 flex flex-col overflow-hidden border-primary/20 bg-card/50 relative">
                        <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                            <div className="space-y-4 max-w-3xl mx-auto">
                                {messages.length === 0 && (
                                    <div className="text-center py-20 text-muted-foreground">
                                        <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                                        <p>Inicia una conversación con tu director seleccionado</p>
                                        <p className="text-sm mt-2">Pregunta sobre estrategia, liderazgo, o cualquier desafío ministerial</p>
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
                                            <div className={`flex flex-col gap-2 max-w-[80%]`}>
                                                <div className={`rounded-lg px-4 py-3 text-sm ${m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"}`}>
                                                    <span className="whitespace-pre-wrap">{m.content}</span>
                                                </div>
                                                {/* TTS Button for Assistant */}
                                                {m.role === "assistant" && (
                                                    <div className="flex gap-2">
                                                        <Button
                                                            variant="ghost"
                                                            size="sm"
                                                            className="h-6 w-6 p-0 rounded-full hover:bg-muted-foreground/10"
                                                            onClick={() => isSpeaking ? stopSpeaking() : speak(m.content, language === 'es' ? 'es-ES' : 'en-US')}
                                                            title="Leer en voz alta"
                                                        >
                                                            {isSpeaking ? <StopCircle className="h-3 w-3" /> : <Volume2 className="h-3 w-3 opacity-50 hover:opacity-100" />}
                                                        </Button>
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
                                    placeholder="Escribe tu pregunta o desafío... (o usa el micrófono)"
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
