"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/store";
import { ShieldCheck, Mail, CheckCircle, AlertCircle } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export default function VerifyDevicePage() {
    const [code, setCode] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [status, setStatus] = useState<{ type: 'error' | 'success', text: string } | null>(null);
    const router = useRouter();
    const login = useAuthStore((state) => state.login);

    const handleVerify = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setStatus(null);

        // In a real app, verify code with backend
        await new Promise(resolve => setTimeout(resolve, 1500));

        if (code === "123456") {
            // Success - Mock user and token to establish session
            const mockUser = {
                username: "user",
                full_name: "Usuario Verificado",
                role: "admin"
            };
            login("mock-token-session", mockUser);

            setStatus({ type: 'success', text: "Dispositivo verificado. Redirigiendo..." });

            // Give user time to see success message before redirecting
            setTimeout(() => {
                router.push("/dashboard");
            }, 1500);
        } else {
            setStatus({ type: 'error', text: "Código inválido. Por favor intenta de nuevo." });
            setIsLoading(false);
        }
    };

    const handleResend = async () => {
        setIsLoading(true);
        // Mock resend logic
        await new Promise(resolve => setTimeout(resolve, 1000));
        setStatus({ type: 'success', text: "Nuevo código enviado a tu correo." });
        setIsLoading(false);
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="w-[400px] border-primary/20 bg-card shadow-2xl">
                    <CardHeader className="text-center">
                        <div className="mx-auto w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                            <ShieldCheck className="w-6 h-6 text-primary" />
                        </div>
                        <CardTitle className="text-2xl font-bold font-heading">Verificación de Seguridad</CardTitle>
                        <CardDescription>
                            Hemos detectado un nuevo dispositivo. Por favor ingresa el código que enviamos a tu correo.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleVerify} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="code">Código de 6 dígitos</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="code"
                                        placeholder="123456"
                                        className="pl-9 text-center tracking-widest text-lg"
                                        value={code}
                                        onChange={(e) => setCode(e.target.value)}
                                        maxLength={6}
                                        required
                                        disabled={isLoading}
                                    />
                                </div>
                            </div>

                            <AnimatePresence mode="wait">
                                {status && (
                                    <motion.div
                                        initial={{ opacity: 0, y: -10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: -10 }}
                                        className={cn(
                                            "p-3 rounded-md text-sm flex items-center gap-2",
                                            status.type === 'success' ? "bg-green-500/10 text-green-500 border border-green-500/20" : "bg-destructive/10 text-destructive border border-destructive/20"
                                        )}
                                    >
                                        {status.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertCircle className="h-4 w-4" />}
                                        {status.text}
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            <Button type="submit" className="w-full" disabled={isLoading}>
                                {isLoading ? "Procesando..." : "Verificar Dispositivo"}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="justify-center">
                        <Button
                            variant="link"
                            className="text-xs text-muted-foreground"
                            onClick={handleResend}
                            disabled={isLoading}
                        >
                            ¿No recibiste el código? Reenviar
                        </Button>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
