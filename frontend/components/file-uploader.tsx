
"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, FileText, FileAudio, FileVideo, X, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/store";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

export function FileUploader() {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState<"idle" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setStatus("idle");
            setMessage("");
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        setStatus("idle");
        setProgress(10); // Start progress

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await api.post("/knowledge/upload", formData, {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
                onUploadProgress: (progressEvent) => {
                    const percentCompleted = Math.round((progressEvent.loaded * 100) / (progressEvent.total || 100));
                    setProgress(percentCompleted);
                },
            });

            setStatus("success");
            setMessage(`Archivo "${response.data.filename}" subido y en cola para procesamiento.`);
            setFile(null); // Reset file
            if (fileInputRef.current) fileInputRef.current.value = "";
        } catch (error: any) {
            console.error("Upload error:", error);
            setStatus("error");
            setMessage(error.response?.data?.detail || "Error al subir el archivo.");
        } finally {
            setUploading(false);
            setProgress(0);
        }
    };

    const getIcon = (type: string) => {
        if (type.includes("pdf") || type.includes("text")) return <FileText className="h-8 w-8 text-blue-500" />;
        if (type.includes("audio")) return <FileAudio className="h-8 w-8 text-green-500" />;
        if (type.includes("video")) return <FileVideo className="h-8 w-8 text-purple-500" />;
        return <Upload className="h-8 w-8 text-gray-400" />;
    };

    return (
        <div className="w-full max-w-xl mx-auto p-6 bg-card rounded-lg border border-border shadow-sm">
            <h3 className="text-lg font-semibold mb-2">Subida Directa</h3>
            <p className="text-sm text-muted-foreground mb-4">
                Sube libros (PDF), audios o videos para que el Agente los aprenda.
            </p>

            <div
                className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center gap-4 transition-colors ${file ? "border-primary/50 bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50"
                    }`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
                        setFile(e.dataTransfer.files[0]);
                    }
                }}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    accept=".pdf,.txt,.md,.mp3,.mp4,.wav,.m4a"
                />

                {!file ? (
                    <>
                        <div className="p-4 rounded-full bg-muted">
                            <Upload className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <div className="text-center">
                            <Button variant="ghost" onClick={() => fileInputRef.current?.click()}>
                                Seleccionar Archivo
                            </Button>
                            <p className="text-xs text-muted-foreground mt-1">
                                O arrastra y suelta aquí
                            </p>
                        </div>
                    </>
                ) : (
                    <div className="flex items-center gap-4 w-full">
                        {getIcon(file.type)}
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{file.name}</p>
                            <p className="text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => setFile(null)} disabled={uploading}>
                            <X className="h-4 w-4" />
                        </Button>
                    </div>
                )}
            </div>

            {uploading && (
                <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-xs">
                        <span>Subiendo...</span>
                        <span>{progress}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                </div>
            )}

            {status === "success" && (
                <Alert className="mt-4 border-green-500/20 bg-green-500/10">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    <AlertTitle className="text-green-600">¡Éxito!</AlertTitle>
                    <AlertDescription className="text-green-600/90 text-sm">
                        {message}
                    </AlertDescription>
                </Alert>
            )}

            {status === "error" && (
                <Alert variant="destructive" className="mt-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>
                        {message}
                    </AlertDescription>
                </Alert>
            )}

            <div className="mt-4 flex justify-end">
                <Button onClick={handleUpload} disabled={!file || uploading}>
                    {uploading ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Procesando
                        </>
                    ) : (
                        "Subir a Base de Conocimiento"
                    )}
                </Button>
            </div>
        </div>
    );
}
