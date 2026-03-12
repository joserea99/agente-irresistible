"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { User, ArrowLeft } from "lucide-react";
import { motion } from "framer-motion";
import { supabase } from "@/lib/supabase";

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const { t } = useLanguage();

    const handleResetPassword = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");
        setMessage("");

        try {
            const { error } = await supabase.auth.resetPasswordForEmail(email, {
                redirectTo: `${window.location.origin}/update-password`,
            });

            if (error) throw error;

            setMessage("Te hemos enviado un enlace para restablecer tu contraseña. Por favor, revisa tu correo electrónico.");
        } catch (err: any) {
            console.error("Reset Password Error:", err);
            setError(err.message || "Error al solicitar restablecimiento de contraseña");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background to-sidebar relative overflow-hidden">
            {/* Background Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-full opacity-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary blur-[100px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-accent blur-[100px]" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="z-10"
            >
                <Card className="w-[400px] border-sidebar-border bg-card/50 backdrop-blur-xl shadow-2xl">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl font-bold font-heading text-primary">Recuperar Contraseña</CardTitle>
                        <CardDescription>Ingresa tu correo para recibir un enlace de recuperación</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {message ? (
                            <div className="bg-primary/20 text-primary border border-primary/50 rounded-lg p-4 text-sm text-center">
                                {message}
                            </div>
                        ) : (
                            <form onSubmit={handleResetPassword} className="space-y-4">
                                <div className="space-y-2">
                                    <Label htmlFor="email">Email</Label>
                                    <div className="relative">
                                        <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="correo@ejemplo.com"
                                            className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            required
                                        />
                                    </div>
                                </div>
                                {error && <p className="text-sm text-destructive font-medium">{error}</p>}
                                <Button type="submit" className="w-full bg-primary hover:bg-primary/90 transition-all shadow-lg shadow-primary/25" disabled={isLoading}>
                                    {isLoading ? "Enviando..." : "Enviar enlace de recuperación"}
                                </Button>
                            </form>
                        )}
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-2">
                        <div className="text-center">
                            <a
                                href="/login"
                                className="text-sm text-muted-foreground hover:text-primary transition-colors inline-flex items-center gap-2"
                            >
                                <ArrowLeft className="h-4 w-4" /> Volver al Login
                            </a>
                        </div>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
