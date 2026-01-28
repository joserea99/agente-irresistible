
"use client";

import { useState, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { MessageSquare, Plus, Trash2, Clock, Loader2 } from "lucide-react";
import { api } from "@/lib/store";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import { es } from "date-fns/locale";

interface ChatSession {
    id: string;
    title: string;
    director: string;
    updated_at: string;
}

interface ChatHistorySidebarProps {
    currentSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewChat: () => void;
    className?: string;
}

export function ChatHistorySidebar({
    currentSessionId,
    onSelectSession,
    onNewChat,
    className
}: ChatHistorySidebarProps) {
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const fetchHistory = async () => {
        try {
            const response = await api.get("/chat/history/current");
            setSessions(response.data.sessions);
        } catch (error) {
            console.error("Error fetching history:", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [currentSessionId]); // Refetch when session changes (e.g. title update)

    const handleDelete = async (e: React.MouseEvent, id: string) => {
        e.stopPropagation();
        if (!confirm("¿Estás seguro de querer borrar esta conversación?")) return;

        try {
            await api.delete(`/chat/session/${id}`);
            setSessions(prev => prev.filter(s => s.id !== id));
            if (currentSessionId === id) {
                onNewChat();
            }
        } catch (error) {
            console.error("Error deleting session:", error);
        }
    };

    return (
        <div className={cn("flex flex-col h-full border-r bg-card/50", className)}>
            <div className="p-4 border-b">
                <Button
                    onClick={onNewChat}
                    className="w-full justify-start gap-2"
                    variant={!currentSessionId ? "secondary" : "default"}
                >
                    <Plus className="h-4 w-4" />
                    Nueva Consulta
                </Button>
            </div>

            <ScrollArea className="flex-1">
                <div className="p-2 space-y-1">
                    {isLoading ? (
                        <div className="flex justify-center p-4">
                            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="text-center p-4 text-xs text-muted-foreground">
                            No hay historial reciente.
                        </div>
                    ) : (
                        sessions.map((session) => (
                            <div
                                key={session.id}
                                onClick={() => onSelectSession(session.id)}
                                className={cn(
                                    "group flex items-center justify-between p-3 rounded-lg text-sm cursor-pointer transition-colors hover:bg-muted/50",
                                    currentSessionId === session.id ? "bg-muted font-medium" : "text-muted-foreground"
                                )}
                            >
                                <div className="flex items-center gap-3 overflow-hidden">
                                    <MessageSquare className="h-4 w-4 shrink-0 opacity-70" />
                                    <div className="flex flex-col overflow-hidden">
                                        <span className="truncate">{session.title || "Nueva Conversación"}</span>
                                        <span className="text-[10px] opacity-70">
                                            {formatDistanceToNow(new Date(session.updated_at), { addSuffix: true, locale: es })}
                                        </span>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={(e) => handleDelete(e, session.id)}
                                >
                                    <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                                </Button>
                            </div>
                        ))
                    )}
                </div>
            </ScrollArea>
        </div>
    );
}
