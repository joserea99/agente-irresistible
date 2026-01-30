"use client";

import { useState, useEffect, useRef } from "react";
import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useLanguage } from "@/lib/language-context";
import { api } from "@/lib/store";
import { Loader2, Send, User, Bot, Play, Trophy, AlertTriangle, Target, MessageSquare, Sparkles } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from 'react-markdown';

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

    // Load Scenarios
    useEffect(() => {
        // Reset active session when language changes to avoid mixed state
        setIsPlaying(false);
        setSelectedScenarioId(null);
        setActiveScenario(null);
        setMessages([]);
        setEvaluation(null);

        const fetchScenarios = async () => {
            try {
                const res = await api.get(`/dojo/scenarios?language=${language}`);
                setScenarios(res.data.scenarios);
            } catch (err) {
                console.error("Failed to fetch scenarios", err);
            }
        };
        fetchScenarios();
    }, [language]);

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
        } catch (err) {
            console.error("Evaluation failed", err);
        } finally {
            setIsEvaluating(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="h-[calc(100vh-140px)] flex flex-col gap-6">

                {/* Header */}
                <div className="flex justify-between items-center shrink-0">
                    <div>
                        <h2 className="text-3xl font-bold font-heading tracking-tight flex items-center gap-2">
                            🥋 {t.dojo.title}
                        </h2>
                        <p className="text-muted-foreground">{t.dojo.subtitle}</p>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full min-h-0">

                    {/* LEFT PANEL: Selection / Context */}
                    <div className="lg:col-span-1 flex flex-col gap-4 h-full min-h-0 overflow-y-auto pr-2">
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
                            // CONTEXT VIEW (During Simulation)
                            <Card className="h-full border-blue-500/20 bg-blue-500/5 flex flex-col">
                                <CardHeader>
                                    <div className="flex justify-between items-start">
                                        <CardTitle className="text-lg text-blue-400">{activeScenario?.name}</CardTitle>
                                        <Button variant="ghost" size="sm" onClick={() => { setIsPlaying(false); setEvaluation(null); setSelectedScenarioId(null); }}>
                                            {t.dojo.exit}
                                        </Button>
                                    </div>
                                    <Separator className="bg-blue-500/20" />
                                </CardHeader>
                                <CardContent className="space-y-6 flex-1">
                                    <div className="space-y-2">
                                        <h4 className="flex items-center gap-2 text-sm font-bold uppercase text-blue-600 dark:text-blue-400">
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
                                <CardFooter>
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
                    <div className="lg:col-span-2 h-full min-h-0">
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
                                    <div className="prose dark:prose-invert max-w-none">
                                        {/* Use basic pre-wrap for now to avoid react-markdown issues if not installed */}
                                        <div className="whitespace-pre-wrap">{evaluation}</div>
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
                                                    <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                                                        {msg.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                                                    </div>
                                                    <div className={`p-3 rounded-lg text-sm ${msg.role === 'user'
                                                        ? 'bg-primary text-primary-foreground rounded-tr-none'
                                                        : 'bg-muted rounded-tl-none'
                                                        }`}>
                                                        {msg.content}
                                                    </div>
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
                                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                                            className="flex gap-2"
                                        >
                                            <Input
                                                value={input}
                                                onChange={e => setInput(e.target.value)}
                                                placeholder={t.dojo.typeResponse}
                                                disabled={isLoading}
                                                className="flex-1"
                                                autoFocus
                                            />
                                            <Button type="submit" disabled={isLoading || !input.trim()}>
                                                <Send className="h-4 w-4" />
                                            </Button>
                                        </form>
                                    </div>
                                </div>
                            ) : (
                                // EMPTY STATE
                                <div className="h-full flex flex-col items-center justify-center text-muted-foreground p-8 text-center border-2 border-dashed rounded-xl">
                                    <Bot className="h-16 w-16 mb-4 opacity-20" />
                                    <h3 className="text-xl font-bold mb-2">{t.dojo.emptyStateTitle}</h3>
                                    <p className="max-w-md">{t.dojo.emptyStateDesc}</p>
                                </div>
                            )}
                        </Card>
                    </div>
                </div>
            </div>
        </DashboardLayout>
    );
}
