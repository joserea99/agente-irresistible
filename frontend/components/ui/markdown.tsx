"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

/**
 * Reusable Markdown renderer themed for Iglesia Irresistible OS.
 * Styles each element explicitly so it works without the Tailwind
 * typography plugin and stays consistent across chat, dojo, and magic.
 */
export function Markdown({ children, className }: { children: string; className?: string }) {
    return (
        <div className={cn("markdown-body text-sm leading-relaxed break-words", className)}>
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    h1: ({ children }) => <h1 className="text-lg font-bold mt-4 mb-2 first:mt-0">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mt-4 mb-2 first:mt-0">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-semibold mt-3 mb-1.5 first:mt-0">{children}</h3>,
                    p: ({ children }) => <p className="mb-3 last:mb-0">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1 last:mb-0">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1 last:mb-0">{children}</ol>,
                    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                    strong: ({ children }) => <strong className="font-semibold text-foreground">{children}</strong>,
                    em: ({ children }) => <em className="italic">{children}</em>,
                    a: ({ children, href }) => (
                        <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary underline underline-offset-2 hover:opacity-80">
                            {children}
                        </a>
                    ),
                    blockquote: ({ children }) => (
                        <blockquote className="border-l-2 border-primary/40 pl-3 italic text-muted-foreground my-3">{children}</blockquote>
                    ),
                    code: ({ className, children }) => {
                        const isBlock = (className || "").includes("language-");
                        if (isBlock) {
                            return (
                                <code className="block bg-background/60 border border-border rounded-md p-3 my-3 text-xs font-mono overflow-x-auto whitespace-pre">
                                    {children}
                                </code>
                            );
                        }
                        return <code className="bg-background/60 border border-border rounded px-1 py-0.5 text-[0.85em] font-mono">{children}</code>;
                    },
                    hr: () => <hr className="my-4 border-border" />,
                    table: ({ children }) => (
                        <div className="overflow-x-auto my-3">
                            <table className="w-full text-xs border-collapse">{children}</table>
                        </div>
                    ),
                    thead: ({ children }) => <thead className="bg-muted/60">{children}</thead>,
                    th: ({ children }) => <th className="border border-border px-2 py-1.5 text-left font-semibold">{children}</th>,
                    td: ({ children }) => <td className="border border-border px-2 py-1.5 align-top">{children}</td>,
                }}
            >
                {children}
            </ReactMarkdown>
        </div>
    );
}
