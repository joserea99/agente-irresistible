"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
} from "@/components/ui/sheet";
import { Sparkles, FileText, Share2, ClipboardList, Loader2 } from "lucide-react";
import { api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";

// basic markdown renderer or just whitespace-pre-wrap
// import ReactMarkdown from 'react-markdown';

interface MagicMenuProps {
    source: string;
    title: string;
}

export function MagicMenu({ source, title }: MagicMenuProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState("");
    const [activeAction, setActiveAction] = useState("");
    const { t, language } = useLanguage();

    const handleAction = async (actionType: string, actionLabel: string) => {
        setIsLoading(true);
        setActiveAction(actionLabel);
        setIsOpen(true); // Open sheet immediately to show loading state
        setResult("");

        try {
            const response = await api.post("/magic/generate", {
                document_source: source,
                action_type: actionType,
                language: language // Pass current language context
            });
            setResult(response.data.result);
        } catch (error: any) {
            console.error("Magic generation failed", error);
            const msg = error.response?.data?.detail || error.message || t.magic.error;
            setResult(`❌ ${msg}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <DropdownMenu>
                <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <span className="sr-only">Open menu</span>
                        <Sparkles className="h-4 w-4 text-purple-500" />
                    </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                    <DropdownMenuLabel>⚡ {t.magic.actionsTitle}</DropdownMenuLabel>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem onClick={() => handleAction("guide", t.magic.createGuide)}>
                        <FileText className="mr-2 h-4 w-4" />
                        <span>{t.magic.createGuide}</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAction("plan", t.magic.createPlan)}>
                        <ClipboardList className="mr-2 h-4 w-4" />
                        <span>{t.magic.createPlan}</span>
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => handleAction("social", t.magic.socialPosts)}>
                        <Share2 className="mr-2 h-4 w-4" />
                        <span>{t.magic.socialPosts}</span>
                    </DropdownMenuItem>
                </DropdownMenuContent>
            </DropdownMenu>

            <Sheet open={isOpen} onOpenChange={setIsOpen}>
                <SheetContent className="w-[400px] sm:w-[540px] overflow-y-auto">
                    <SheetHeader>
                        <SheetTitle>⚡ {t.magic.generated} {activeAction}</SheetTitle>
                        <SheetDescription>
                            {t.magic.basedOn}: {title}
                        </SheetDescription>
                    </SheetHeader>
                    <div className="mt-6">
                        {isLoading ? (
                            <div className="flex flex-col items-center justify-center h-40 space-y-4">
                                <Loader2 className="h-8 w-8 animate-spin text-purple-500" />
                                <p className="text-sm text-muted-foreground">{t.magic.consulting}</p>
                            </div>
                        ) : (
                            <div className="prose dark:prose-invert text-sm">
                                {/* Check if react-markdown is available, otherwise simpler render */}
                                <div className="whitespace-pre-wrap">{result}</div>
                            </div>
                        )}
                    </div>
                </SheetContent>
            </Sheet>
        </>
    );
}
