"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/lib/language-context";
import { api } from "@/lib/store";
import { Loader2, Send, User, Bot, Play, Trophy, AlertTriangle, Target, MessageSquare, Sparkles, Volume2, StopCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { Markdown } from "@/components/ui/markdown";
import { MicButton } from "@/components/ui/mic-button";
import { useSpeechToText } from "@/hooks/use-speech-to-text";
import { useTextToSpeech } from "@/hooks/use-text-to-speech";

interface Scenario {
    id: string;
    name: string;
    description: string;
}

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function DojoPage() {
    const { t, language } = useLanguage();

    // States
    const [scenarios, setScenarios] = useState<Scenario[]>([]);
    const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
    const [activeScenario, setActiveScenario] = useState<any>(null); // Full details

    // Chat States
    const [isPlaying, setIsPlaying] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    // Custom Scenario State
    const [customInput, setCustomInput] = useState("");

    // Evaluation State
    const [evaluation, setEvaluation] = useState<string | null>(null);
    const [isEvaluating, setIsEvaluating] = useState(false);

    const scrollRef = useRef<HTMLDivElement>(null);
    const dojoTextareaRef = useRef<HTMLTextAreaElement>(null);
    const autoSendTimerRef = useRef<NodeJS.Timeout | null>(null);
    const inputRef = useRef(input); // Keep input in ref for auto-send

    // Keep input ref in sync and auto-resize textarea
    useEffect(() => {
        inputRef.current = input;
        const el = dojoTextareaRef.current;
        if (el) {
            el.style.height = "auto";
            el.style.height = `${Math.min(el.scrollHeight, 180)}px`;
        }
    }, [input]);

    // Voice Hooks — stabilize onResult with useCallback to prevent hook recreation
    const handleVoiceResult = useCallback((text: string) => {
        setInput((prev) => prev + (prev && !prev.endsWith(' ') ? " " : "") + text);

        // Auto-send: reset timer on each voice result, send after 2s of silence
        if (autoSendTimerRef.current) clearTimeout(autoSendTimerRef.current);
        autoSendTimerRef.current = setTimeout(() => {
            if (inputRef.current.trim()) {
                // Trigger form submit programmatically
                const form = document.getElementById('dojo-chat-form') as HTMLFormElement;
                if (form) form.requestSubmit();
            }
        }, 2000); // 2 seconds of silence → auto-send
    }, []);

    const { isListening, startListening, stopListening, hasSupport: hasMicSupport } = useSpeechToText({
        onResult: handleVoiceResult,
        language: language === 'es' ? 'es-US' : 'en-US'
    });
    const { speak, stop: stopSpeaking, isSpeaking } = useTextToSpeech();

    const lastSpokenIndex = useRef<number>(-1);
    const isPlayingRef = useRef(isPlaying);

    // Keep ref in sync with state
    useEffect(() => {
        isPlayingRef.current = isPlaying;
    }, [isPlaying]);

    // Detect mobile for longer post-speak delay
    const isMobile = typeof window !== "undefined" && /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    // Auto-speak assistant messages
    useEffect(() => {
        if (messages.length > 0 && isPlaying) {
            const lastIndex = messages.length - 1;
            const lastMsg = messages[lastIndex];

            // Only speak if we haven't spoken this message yet
            if (lastMsg.role === 'assistant' && lastIndex > lastSpokenIndex.current) {
                lastSpokenIndex.current = lastIndex; // Mark as spoken

                stopListening(); // Stop mic before speaking
                speak(
                    lastMsg.content,
                    language === 'es' ? 'es-US' : 'en-US',
                    () => {
                        // Guard: only restart mic if session is still active
                        if (!isPlayingRef.current) return;
                        // Longer delay on mobile to avoid echo/overlap
                        const delay = isMobile ? 800 : 500;
                        setTimeout(() => {
                            if (isPlayingRef.current) {
                                startListening();
                            }
                        }, delay);
                    }
                );
            }
        }
    }, [messages, isPlaying, language, speak, stopListening, startListening, isMobile]);
    // Removed the secondary useEffect that caused the race condition

    // Load Scenarios
    useEffect(() => {
        // Reset active session when language changes to avoid mixed state
        setIsPlaying(false);
        setSelectedScenarioId(null);
        setActiveScenario(null);
        setMessages([]);
        setEvaluation(null);
        lastSpokenIndex.current = -1; // Reset speech tracker
        stopSpeaking(); // Stop any pending audio
        stopListening(); // Ensure mic is off

        const fetchScenarios = async () => {
            try {
                const res = await api.get(`/dojo/scenarios?language=${language}`);
                setScenarios(res.data.scenarios);
            } catch (err) {
                console.error("Failed to fetch scenarios", err);
            }
        };
        fetchScenarios();
    }, [language, stopSpeaking]);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleStart = async (scenarioId: string) => {
        setIsLoading(true);
        setSelectedScenarioId(scenarioId);
        setMessages([]);
        setEvaluation(null);
        lastSpokenIndex.current = -1; // Reset tracker

        try {
            const res = await api.post("/dojo/start", {
                scenario_id: scenarioId,
                language: language
            });

            setActiveScenario(res.data);
            setMessages([{ role: "assistant", content: res.data.opening_line }]);
            setIsPlaying(true);
        } catch (err) {
            console.error("Failed to start", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateCustom = async () => {
        if (!customInput.trim()) return;
        setIsLoading(true);
        setEvaluation(null);

        try {
            const res = await api.post("/dojo/create", {
                description: customInput,
                language: language
            });

            // The response is the full scenario object
            const newScenario = res.data;

            // We need to 'inject' this scenario into the local state so we can play it
            // Ideally we'd add it to the list, but for now we just jump straight to playing it.
            // Be careful, start_scenario expects an ID that exists in the backend list usually.
            // But here we already have the start data (opening line, etc).
            // Actually, we need to pass this custom scenario context to the backend for subsequent chats?
            // Wait, the backend currently looks up scenario by ID in `DOJO_SCENARIOS`.
            // The `create` endpoint returns the scenario data, but doesn't persist it in `DOJO_SCENARIOS` globally for stateless requests.
            // CRITICAL FIX: The `generate_roleplay_response` expects `scenario_id` to look up the `system_prompt`.
            // If the ID is dynamic, the BACKEND won't know the system prompt on the next request ("/message").
            // SOLUTION: We need to pass the `system_prompt` back and forth OR store it temporarily.
            // Given the stateless nature, I should probably update the backend to allow passing `custom_system_prompt` in the `/message` and `start` requests?
            // OR simpler: For this session, I will mock the ID for now and realize I might need a quick backend fix to support transient scenarios.

            // Re-reading DojoService: `generate_roleplay_response` does `DOJO_SCENARIOS.get(scenario_id)`.
            // If I send a custom ID, it will fail. 
            // I need to update `DojoService` to handle "transient" scenarios or pass the full context in every message.

            // QUICK FIX LOOP: I'll update the backend to accept an optional `system_prompt` in the `RoleplayRequest`.
            // If provided, it uses that instead of looking up the ID.

            setActiveScenario(newScenario);
            setSelectedScenarioId(newScenario.id); // "custom_..."
            setMessages([{ role: "assistant", content: newScenario.opening_line }]);
            setCustomInput(""); // clear input
            setIsPlaying(true);

        } catch (err) {
            console.error("Failed to create custom scenario", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = async () => {
        if (!input.trim() || !selectedScenarioId) return;

        // Clear auto-send timer to prevent double-send
        if (autoSendTimerRef.current) {
            clearTimeout(autoSendTimerRef.current);
            autoSendTimerRef.current = null;
        }

        stopListening(); // Stop mic while processing
        const userMsg = input;
        setInput("");

        // Optimistic UI
        const newHistory = [...messages, { role: "user", content: userMsg } as Message];
        setMessages(newHistory);
        setIsLoading(true);

        try {
            const res = await api.post("/dojo/message", {
                scenario_id: selectedScenarioId,
                message: userMsg,
                history: newHistory, // Send updated history
                language: language,
                system_prompt: activeScenario?.system_prompt // Pass prompt for custom scenarios
            });

            setMessages(prev => [...prev, { role: "assistant", content: res.data.message }]);
        } catch (err) {
            console.error("Failed to send message", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleEvaluate = async () => {
        setIsEvaluating(true);
        try {
            const res = await api.post("/dojo/evaluate", {
                scenario_id: selectedScenarioId,
                history: messages,
                language: language,
                system_prompt: activeScenario?.system_prompt
            });
            setEvaluation(res.data.evaluation);
            setIsPlaying(false);

            // Save completion to backend (fire and forget)
            try {
                const scoreMatch = res.data.evaluation?.match(/(\d+)\s*\/\s*10/);
                const score = scoreMatch ? parseInt(scoreMatch[1], 10) : 0;
                await api.post("/dojo/complete", {
                    scenario_id: selectedScenarioId,
                    scenario_name: activeScenario?.name || selectedScenarioId,
                    score
                });
            } catch (saveErr) {
                console.error("Failed to save dojo completion", saveErr);
            }
        } catch (err) {
            console.error("Evaluation failed", err);
        } finally {
            setIsEvaluating(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="flex flex-col gap-4 lg:gap-6 lg:h-[calc(100dvh-8rem)] pb-6 lg:pb-0">

                {/* Header (hidden on mobile during active simulation to maximize chat space) */}
                <div className={`${(isPlaying || evaluation) ? "hidden lg:flex" : "flex"} justify-between items-center shrink-0`}>
                    <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-primary block mb-0.5">
                            {language === "es" ? "Formación Práctica por Área Ministerial" : "Practical Ministry Area Training"}
                        </span>
                        <h2 className="text-xl sm:text-2xl md:text-3xl font-bold font-heading tracking-tight text-foreground">
                            {language === "es" ? "Centro de Entrenamiento para Líderes" : "Leadership Training Center"}
                        </h2>
                        <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
                            {language === "es"
                                ? "Practica conversaciones reales de tu área (grupos pequeños, niños, atención al invitado, producción o liderazgo) y recibe retroalimentación inmediata."
                                : "Practice real conversations from your ministry area and receive immediate coaching."}
                        </p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6 flex-1 min-h-0">

                    {/* LEFT PANEL: Selection / Context */}
                    <div className="lg:col-span-1 flex flex-col gap-4 lg:h-full min-h-0 lg:overflow-y-auto lg:pr-2">
                        {!isPlaying && !evaluation ? (
                            // LIST VIEW
                            <div className="space-y-4">
                                {/* CUSTOM SCENARIO CREATOR */}
                                <Card className="border-dashed border-2 border-primary/50 bg-primary/5">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-base flex items-center gap-2">
                                            <Sparkles className="h-4 w-4 text-primary" />
                                            {t.dojo.createCustom}
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent className="space-y-3">
                                        <div className="relative">
                                            <textarea
                                                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none"
                                                placeholder={t.dojo.customPlaceholder}
                                                value={customInput}
                                                onChange={(e) => setCustomInput(e.target.value)}
                                            />
                                        </div>
                                        <Button
                                            size="sm"
                                            className="w-full"
                                            onClick={handleCreateCustom}
                                            disabled={isLoading || !customInput.trim()}
                                        >
                                            {isLoading ? <Loader2 className="mr-2 h-3 w-3 animate-spin" /> : <Play className="mr-2 h-3 w-3" />}
                                            {t.dojo.createButton}
                                        </Button>
                                    </CardContent>
                                </Card>

                                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">{t.dojo.selectScenario}</h3>
                                {scenarios.map(s => (
                                    <Card key={s.id}
                                        className="cursor-pointer hover:border-primary transition-all hover:bg-muted/50"
                                        onClick={() => handleStart(s.id)}>
                                        <CardHeader className="pb-2">
                                            <CardTitle className="text-base">{s.name}</CardTitle>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-xs text-muted-foreground">{s.description}</p>
                                        </CardContent>
                                        <CardFooter className="pt-0">
                                            <Button size="sm" variant="secondary" className="w-full text-xs">
                                                <Play className="mr-2 h-3 w-3" /> {t.dojo.startSimulation}
                                            </Button>
                                        </CardFooter>
                                    </Card>
                                ))}
                            </div>
                        ) : (
                            // CONTEXT VIEW (Compact on mobile, full card on desktop)
                            <Card className="lg:h-full border-primary/25 bg-primary/5 flex flex-col">
                                <CardHeader className="py-3 px-4 lg:p-6">
                                    <div className="flex justify-between items-center gap-2">
                                        <CardTitle className="text-sm sm:text-base lg:text-lg text-primary truncate">
                                            {activeScenario?.name}
                                        </CardTitle>
                                        <div className="flex items-center gap-1.5 shrink-0">
                                            <Button
                                                variant="default"
                                                size="sm"
                                                className="lg:hidden h-7 px-2.5 text-xs bg-red-600 hover:bg-red-700 text-white"
                                                onClick={handleEvaluate}
                                                disabled={isEvaluating || !!evaluation}
                                            >
                                                <Trophy className="mr-1 h-3 w-3" /> {t.dojo.endSimulation}
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                className="h-7 px-2 text-xs"
                                                onClick={() => { setIsPlaying(false); setEvaluation(null); setSelectedScenarioId(null); }}
                                            >
                                                {t.dojo.exit}
                                            </Button>
                                        </div>
                                    </div>
                                    <p className="lg:hidden text-xs text-muted-foreground mt-1 line-clamp-2">
                                        <strong>{t.dojo.goal}:</strong> {activeScenario?.goal || t.dojo.goalDesc}
                                    </p>
                                    <Separator className="hidden lg:block bg-primary/20 mt-2" />
                                </CardHeader>
                                <CardContent className="hidden lg:block space-y-6 flex-1">
                                    <div className="space-y-2">
                                        <h4 className="flex items-center gap-2 text-sm font-bold uppercase text-primary">
                                            <MessageSquare className="h-4 w-4" /> {t.dojo.context}
                                        </h4>
                                        <p className="text-sm">{activeScenario?.context || t.dojo.contextDesc}</p>
                                    </div>

                                    <div className="space-y-2">
                                        <h4 className="flex items-center gap-2 text-sm font-bold uppercase text-amber-600 dark:text-amber-400">
                                            <Target className="h-4 w-4" /> {t.dojo.goal}
                                        </h4>
                                        <p className="text-sm opacity-90">{activeScenario?.goal || t.dojo.goalDesc}</p>
                                    </div>

                                    <div className="space-y-2">
                                        <h4 className="flex items-center gap-2 text-sm font-bold uppercase text-rose-600 dark:text-rose-400">
                                            <AlertTriangle className="h-4 w-4" /> {t.dojo.tone}
                                        </h4>
                                        <p className="text-sm opacity-90">{activeScenario?.tone || t.dojo.toneDesc}</p>
                                    </div>
                                </CardContent>
                                <CardFooter className="hidden lg:flex">
                                    <Button
                                        variant="default"
                                        className="w-full bg-red-600 hover:bg-red-700 text-white"
                                        onClick={handleEvaluate}
                                        disabled={isEvaluating || !!evaluation}
                                    >
                                        <Trophy className="mr-2 h-4 w-4" /> {t.dojo.endSimulation}
                                    </Button>
                                </CardFooter>
                            </Card>
                        )}
                    </div>

                    {/* RIGHT PANEL: Chat / Evaluation */}
                    <div className={`${(!selectedScenarioId && !evaluation) ? "hidden lg:block" : "block"} lg:col-span-2 h-[calc(100dvh-13.5rem)] lg:h-full min-h-0`}>
                        <Card className="h-full flex flex-col border-none shadow-none bg-transparent">
                            {evaluation ? (
                                // EVALUATION RESULTS
                                <motion.div
                                    initial={{ opacity: 0, scale: 0.95 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    className="h-full overflow-y-auto p-6 bg-card border rounded-xl"
                                >
                                    <div className="flex items-center gap-3 mb-6">
                                        <div className="h-12 w-12 rounded-full bg-yellow-500/20 flex items-center justify-center">
                                            <Trophy className="h-6 w-6 text-yellow-500" />
                                        </div>
                                        <div>
                                            <h2 className="text-2xl font-bold">{t.dojo.feedbackReport}</h2>
                                            <p className="text-muted-foreground">{t.dojo.evaluateDescription}</p>
                                        </div>
                                    </div>
                                    <div className="max-w-none">
                                        <Markdown>{evaluation}</Markdown>
                                    </div>
                                    <div className="mt-8 flex justify-center">
                                        <Button onClick={() => { setEvaluation(null); setSelectedScenarioId(null); setIsPlaying(false); }}>
                                            Try Another Scenario
                                        </Button>
                                    </div>
                                </motion.div>
                            ) : selectedScenarioId ? (
                                // CHAT INTERFACE
                                <div className="flex flex-col h-full border rounded-xl bg-card overflow-hidden">
                                    {/* Chat Area */}
                                    <div
                                        className="flex-1 overflow-y-auto p-4 space-y-4"
                                        ref={scrollRef}
                                    >
                                        {messages.map((msg, i) => (
                                            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                                <div className={`flex gap-3 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                                                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 text-xs font-bold ${msg.role === 'user' ? 'bg-foreground text-background' : 'bg-primary/15 text-primary border border-primary/20'}`}>
                                                        {msg.role === 'user' ? <User className="h-4 w-4" /> : "SIM"}
                                                    </div>
                                                    <div className={`p-3 rounded-lg text-sm ${msg.role === 'user'
                                                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                                                        : 'bg-muted rounded-tl-none'
                                                        }`}>
                                                        {msg.content}
                                                    </div>
                                                    {msg.role === 'assistant' && (
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="h-8 w-8 rounded-full shrink-0"
                                                            onClick={() => isSpeaking ? stopSpeaking() : speak(msg.content, language === 'es' ? 'es-US' : 'en-US')}
                                                            title="Reproducir audio"
                                                        >
                                                            {isSpeaking ? <StopCircle className="h-4 w-4" /> : <Volume2 className="h-4 w-4 opacity-50 hover:opacity-100" />}
                                                        </Button>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                        {isLoading && (
                                            <div className="flex justify-start">
                                                <div className="bg-muted p-3 rounded-lg rounded-tl-none">
                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Input Area */}
                                    <div className="p-4 bg-muted/30 border-t">
                                        <form
                                            id="dojo-chat-form"
                                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                                        >
                                            <div className="flex items-end gap-2 rounded-2xl border border-border bg-card px-3.5 py-2 shadow-2xs focus-within:ring-2 focus-within:ring-primary/30 focus-within:border-primary/50 transition-all">
                                                <textarea
                                                    ref={dojoTextareaRef}
                                                    rows={1}
                                                    value={input}
                                                    onChange={e => setInput(e.target.value)}
                                                    onKeyDown={(e) => {
                                                        if (e.key === "Enter" && !e.shiftKey) {
                                                            e.preventDefault();
                                                            if (input.trim() && !isLoading) {
                                                                handleSend();
                                                            }
                                                        }
                                                    }}
                                                    placeholder={t.dojo.typeResponse + (isListening ? " (Escuchando...)" : "")}
                                                    disabled={isLoading}
                                                    className="flex-1 bg-transparent border-0 resize-none py-1.5 text-sm leading-relaxed text-foreground placeholder:text-muted-foreground focus:outline-none max-h-[180px] overflow-y-auto"
                                                    autoFocus
                                                />
                                                <div className="flex items-center gap-1.5 shrink-0 pb-0.5">
                                                    <MicButton
                                                        isListening={isListening}
                                                        onStart={startListening}
                                                        onStop={stopListening}
                                                        disabled={isLoading || !hasMicSupport}
                                                    />
                                                    <Button type="submit" size="icon" className="h-9 w-9 rounded-xl shrink-0" disabled={isLoading || !input.trim()}>
                                                        <Send className="h-4 w-4" />
                                                    </Button>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                </div>
                            ) : (
                                // EMPTY STATE
                                <div className="h-full flex flex-col items-center justify-center text-muted-foreground p-8 text-center border border-border bg-card rounded-xl shadow-2xs">
                                    <div className="h-14 w-14 rounded-2xl bg-primary/12 text-primary flex items-center justify-center mb-4 border border-primary/20">
                                        <Target className="h-7 w-7" />
                                    </div>
                                    <h3 className="text-xl font-bold font-heading text-foreground mb-2">
                                        {language === "es"
                                            ? "Entrena a tu Equipo para la Vida Real"
                                            : "Train Your Team for Real Ministry Conversations"}
                                    </h3>
                                    <p className="max-w-md text-sm leading-relaxed">
                                        {language === "es"
                                            ? "Elige un escenario a la izquierda (padres en el área de niños, miembros de grupo pequeño, visitantes nuevos, voluntarios agotados) o escribe una situación real de tu área para practicar cómo responder con empatía y claridad."
                                            : t.dojo.emptyStateDesc}
                                    </p>
                                </div>
                            )}
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
