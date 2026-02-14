"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { CreditCard, Star, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";

export default function SubscriptionPage() {
    const { t } = useLanguage();

    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const router = useRouter();

    const handleSubscribe = async () => {
        setIsLoading(true);
        setError("");
        try {
            // Get token from storage or cookie (store typically has it)
            // If we are here, middleware ensured we are logged in, but let's be safe
            // We'll rely on axios interceptor in `api` from store or simple fetch with cookie

            // Using fetch directly for simplicity with cookie or localStorage
            // But let's try to use the `api` instance if possible, or build headers manually
            const token = document.cookie.split('; ').find(row => row.startsWith('access_token='))?.split('=')[1];

            if (!token) {
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
                throw new Error(data.detail || "Error initiating checkout");
            }

            const data = await response.json();
            if (data.url) {
                window.location.href = data.url;
            } else {
                throw new Error("No checkout URL returned");
            }

        } catch (err: any) {
            console.error(err);
            setError(err.message || "Something went wrong.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="max-w-4xl w-full grid md:grid-cols-2 gap-8"
            >
                {/* Left side: Message */}
                <div className="flex flex-col justify-center space-y-6">
                    <div>
                        <h1 className="text-4xl font-bold font-heading mb-2 text-primary">Acceso Bloqueado</h1>
                        <p className="text-xl text-muted-foreground">Tu periodo de prueba ha finalizado.</p>
                    </div>

                    <div className="space-y-4">
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-6 w-6 text-green-500 shrink-0" />
                            <p>Acceso ilimitado al Agente Estratégico</p>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-6 w-6 text-green-500 shrink-0" />
                            <p>Inteligencia artificial entrenada con el modelo Irresistible</p>
                        </div>
                        <div className="flex items-start gap-3">
                            <CheckCircle className="h-6 w-6 text-green-500 shrink-0" />
                            <p>Base de Conocimiento segura para tu iglesia</p>
                        </div>
                    </div>
                </div>

                {/* Right side: Pricing Card */}
                <Card className="border-primary shadow-2xl bg-card relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-4">
                        <Star className="h-12 w-12 text-yellow-500 opacity-20" />
                    </div>
                    <CardHeader>
                        <CardTitle className="text-2xl">Plan Iglesia Irresistible</CardTitle>
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
