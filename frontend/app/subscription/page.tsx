"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { CreditCard, Star, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";

import { supabase } from "@/lib/supabase";

import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";

function SubscriptionContent() {
    const { t } = useLanguage();
    const searchParams = useSearchParams();
    const success = searchParams.get("success");

    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    useEffect(() => {
        if (success) {
            // Force session refresh to get new role/subscription status
            const refreshSession = async () => {
                await supabase.auth.refreshSession();
                setTimeout(() => {
                    router.push("/dashboard");
                }, 2000);
            };
            refreshSession();
        }
    }, [success, router]);

    const handleSubscribe = async () => {
        setIsLoading(true);
        setError("");
        try {
            // Get fresh token directly from Supabase client
            const { data: { session } } = await supabase.auth.getSession();
            const token = session?.access_token;

            if (!token) {
                console.error("No active Supabase session found");
                setError("No authentication token found. Please log in again.");
                router.push("/login?redirect=/subscription");
                return;
            }

            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-a8ef.up.railway.app'}/subscription/checkout`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    return_url: window.location.origin + "/subscription"
                })
            });

            if (!response.ok) {
                const data = await response.json();
                let errorMessage = data.detail || "Error initiating checkout";
                if (typeof errorMessage === 'object') {
                    errorMessage = JSON.stringify(errorMessage);
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            if (data.url) {
                console.log("Redirecting to:", data.url);
                window.location.href = data.url;
            } else {
                throw new Error("No checkout URL returned");
            }

        } catch (err: any) {
            console.error("Checkout Error:", err);
            let displayError = err.message || "Something went wrong.";
            if (displayError === "[object Object]") {
                displayError = JSON.stringify(err);
            }
            setError(displayError);
        } finally {
            setIsLoading(false);
        }
    };

    if (success) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4">
                <Card className="max-w-md w-full border-green-500/50 bg-green-500/10 shadow-2xl">
                    <CardHeader className="text-center">
                        <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
                        <CardTitle className="text-2xl text-green-500">¡Pago Exitoso!</CardTitle>
                        <CardDescription>Tu suscripción se ha activado.</CardDescription>
                    </CardHeader>
                    <CardContent className="text-center">
                        <p className="text-muted-foreground">Te estamos redirigiendo al panel de control...</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="max-w-4xl w-full grid md:grid-cols-2 gap-8"
            >
                {/* Left side: Value Proposition */}
                <div className="flex flex-col justify-center space-y-6">
                    <div>
                        <span className="text-xs font-bold uppercase tracking-wider text-primary">
                            Membresía Ministerial Todo Incluido
                        </span>
                        <h1 className="text-3xl md:text-4xl font-bold font-heading mt-1 mb-2 text-foreground">
                            Equipa a tu iglesia cada domingo
                        </h1>
                        <p className="text-base text-muted-foreground">
                            Activa tu suscripción para seguir produciendo tus materiales semanales y accediendo a la biblioteca completa de la red.
                        </p>
                    </div>

                    <div className="space-y-3.5 text-sm">
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                            <p><strong>Prepara tu Semana en 1 Clic:</strong> Bosquejo de 5 Movimientos, Guía de Grupos Pequeños, Lección de Niños y Familia, Orden de Servicio y Pack de WhatsApp.</p>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                            <p><strong>Biblioteca de Recursos (1,812):</strong> Series de predicación, guías y manuales ministeriales listos para traducir y adaptar.</p>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                            <p><strong>Consulta con los Especialistas + Entrenamiento:</strong> Asesoría estratégica en 11 áreas ministeriales y entrenamiento práctico para tus líderes y voluntarios.</p>
                        </div>
                    </div>
                </div>

                {/* Right side: Pricing Card */}
                <Card className="border-primary shadow-2xl bg-card relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4">
                        <Star className="h-12 w-12 text-yellow-500 opacity-20" />
                    </div>
                    <CardHeader>
                        <CardTitle className="text-2xl">Plan Irresistible Agent</CardTitle>
                        <CardDescription>Suscripción Mensual</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="text-4xl font-bold">
                            $9.99 <span className="text-lg text-muted-foreground font-normal">/ mes</span>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            + impuestos y tarifas aplicables.
                            Cancela en cualquier momento. Acceso inmediato después del pago.
                        </p>

                        {error && <p className="text-sm text-destructive">{error}</p>}

                        <Button className="w-full h-12 text-lg gap-2" size="lg" onClick={handleSubscribe} disabled={isLoading}>
                            <CreditCard className="h-5 w-5" />
                            {isLoading ? "Procesando..." : "Suscribirse Ahora"}
                        </Button>
                    </CardContent>
                    <CardFooter className="justify-center border-t bg-muted/50 p-4">
                        <p className="text-xs text-muted-foreground">Pagos seguros procesados por Stripe</p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}

export default function SubscriptionPage() {
    return (
        <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><p>Cargando...</p></div>}>
            <SubscriptionContent />
        </Suspense>
    );
}
