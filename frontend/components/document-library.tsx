"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
    Table, TableBody, TableCell, TableHead, TableHeader, TableRow
} from "@/components/ui/table";
import {
    Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from "@/components/ui/select";
import {
    Trash2, RefreshCw, FileText, Globe, Database,
    Loader2, AlertCircle, SearchX, Filter
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface KnowledgeDocument {
    id: string;
    title: string;
    source: string;
    doc_type: string;
    chunk_count: number;
    created_at: string;
    updated_at: string;
}

function getSourceType(source: string): "direct" | "brandfolder" | "web" {
    if (source.startsWith("file://")) return "direct";
    if (source.includes("brandfolder.com")) return "brandfolder";
    return "web";
}

function SourceBadge({ source }: { source: string }) {
    const type = getSourceType(source);
    if (type === "direct") {
        return (
            <Badge variant="outline" className="gap-1 text-blue-400 border-blue-400/30 bg-blue-400/10">
                <FileText className="h-3 w-3" /> Subida directa
            </Badge>
        );
    }
    if (type === "brandfolder") {
        return (
            <Badge variant="outline" className="gap-1 text-purple-400 border-purple-400/30 bg-purple-400/10">
                <Database className="h-3 w-3" /> Brandfolder
            </Badge>
        );
    }
    return (
        <Badge variant="outline" className="gap-1 text-green-400 border-green-400/30 bg-green-400/10">
            <Globe className="h-3 w-3" /> Web
        </Badge>
    );
}

function formatDate(dateStr: string) {
    return new Date(dateStr).toLocaleDateString("es-ES", {
        day: "2-digit", month: "short", year: "numeric"
    });
}

function truncateSource(source: string) {
    if (source.startsWith("file://")) return source.replace("file://", "");
    try {
        const url = new URL(source);
        return url.hostname + url.pathname.slice(0, 40) + (url.pathname.length > 40 ? "…" : "");
    } catch {
        return source.slice(0, 60) + (source.length > 60 ? "…" : "");
    }
}

export function DocumentLibrary() {
    const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState("");
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState<"all" | "direct" | "brandfolder" | "web">("all");
    const [deletingId, setDeletingId] = useState<string | null>(null);

    const fetchDocuments = useCallback(async () => {
        setIsLoading(true);
        setError("");
        try {
            const res = await api.get(`/knowledge/documents?source_type=${filter}&limit=200`);
            setDocuments(res.data.documents || []);
        } catch (e: any) {
            setError("No se pudieron cargar los documentos.");
        } finally {
            setIsLoading(false);
        }
    }, [filter]);

    useEffect(() => { fetchDocuments(); }, [fetchDocuments]);

    const handleDelete = async (doc: KnowledgeDocument) => {
        if (!confirm(`¿Eliminar "${doc.title}" y todos sus datos del cerebro?\n\nEsta acción no se puede deshacer.`)) return;
        setDeletingId(doc.id);
        try {
            await api.delete(`/knowledge/documents/${doc.id}`);
            setDocuments(prev => prev.filter(d => d.id !== doc.id));
        } catch (e: any) {
            alert("Error eliminando documento. Intenta de nuevo.");
        } finally {
            setDeletingId(null);
        }
    };

    const filtered = documents.filter(doc =>
        doc.title.toLowerCase().includes(search.toLowerCase()) ||
        doc.source.toLowerCase().includes(search.toLowerCase())
    );

    const counts = {
        all: documents.length,
        direct: documents.filter(d => getSourceType(d.source) === "direct").length,
        brandfolder: documents.filter(d => getSourceType(d.source) === "brandfolder").length,
        web: documents.filter(d => getSourceType(d.source) === "web").length,
    };

    return (
        <div className="space-y-4">
            {/* Header + controls */}
            <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between">
                <div className="flex items-center gap-3 flex-wrap">
                    <div className="relative">
                        <Filter className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Select value={filter} onValueChange={(v: any) => setFilter(v)}>
                            <SelectTrigger className="pl-9 w-[180px] h-9">
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">Todos ({counts.all})</SelectItem>
                                <SelectItem value="direct">Subida directa ({counts.direct})</SelectItem>
                                <SelectItem value="brandfolder">Brandfolder ({counts.brandfolder})</SelectItem>
                                <SelectItem value="web">Web ({counts.web})</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>
                    <Input
                        placeholder="Buscar por título o fuente..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="h-9 w-[260px]"
                    />
                </div>
                <Button variant="outline" size="sm" onClick={fetchDocuments} className="gap-2 shrink-0">
                    <RefreshCw className="h-4 w-4" /> Actualizar
                </Button>
            </div>

            {/* Table */}
            <div className="rounded-lg border border-border overflow-hidden">
                <Table>
                    <TableHeader>
                        <TableRow className="bg-muted/40 hover:bg-muted/40">
                            <TableHead className="w-[35%]">Documento</TableHead>
                            <TableHead className="w-[20%]">Tipo</TableHead>
                            <TableHead className="w-[25%]">Fuente</TableHead>
                            <TableHead className="text-center w-[8%]">Chunks</TableHead>
                            <TableHead className="text-center w-[8%]">Fecha</TableHead>
                            <TableHead className="text-right w-[4%]"></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading && (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center h-32">
                                    <Loader2 className="h-6 w-6 animate-spin text-primary mx-auto" />
                                </TableCell>
                            </TableRow>
                        )}

                        {!isLoading && error && (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center h-32 text-destructive">
                                    <AlertCircle className="h-5 w-5 mx-auto mb-2" />
                                    {error}
                                </TableCell>
                            </TableRow>
                        )}

                        {!isLoading && !error && filtered.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={6} className="text-center h-32 text-muted-foreground">
                                    <SearchX className="h-6 w-6 mx-auto mb-2 opacity-50" />
                                    {search ? "No se encontraron resultados para tu búsqueda." : "No hay documentos en esta categoría."}
                                </TableCell>
                            </TableRow>
                        )}

                        <AnimatePresence>
                            {!isLoading && filtered.map((doc) => (
                                <motion.tr
                                    key={doc.id}
                                    initial={{ opacity: 1 }}
                                    exit={{ opacity: 0, height: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="border-b border-border last:border-0 hover:bg-muted/30 transition-colors"
                                >
                                    <TableCell className="font-medium">
                                        <span className="line-clamp-2 text-sm">{doc.title || "Sin título"}</span>
                                    </TableCell>
                                    <TableCell>
                                        <SourceBadge source={doc.source} />
                                    </TableCell>
                                    <TableCell>
                                        <span
                                            className="text-xs text-muted-foreground font-mono truncate block max-w-[220px]"
                                            title={doc.source}
                                        >
                                            {truncateSource(doc.source)}
                                        </span>
                                    </TableCell>
                                    <TableCell className="text-center">
                                        <Badge variant="secondary" className="text-xs">
                                            {doc.chunk_count}
                                        </Badge>
                                    </TableCell>
                                    <TableCell className="text-center text-xs text-muted-foreground whitespace-nowrap">
                                        {formatDate(doc.created_at)}
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <Button
                                            variant="ghost"
                                            size="icon"
                                            className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                                            onClick={() => handleDelete(doc)}
                                            disabled={deletingId === doc.id}
                                        >
                                            {deletingId === doc.id
                                                ? <Loader2 className="h-4 w-4 animate-spin" />
                                                : <Trash2 className="h-4 w-4" />
                                            }
                                        </Button>
                                    </TableCell>
                                </motion.tr>
                            ))}
                        </AnimatePresence>
                    </TableBody>
                </Table>
            </div>

            {!isLoading && filtered.length > 0 && (
                <p className="text-xs text-muted-foreground text-right">
                    Mostrando {filtered.length} de {documents.length} documentos
                </p>
            )}
        </div>
    );
}
