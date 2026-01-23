"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { CreditCard, Star, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";

export default function SubscriptionPage() {
    const { t } = useLanguage();

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
                            $49 <span className="text-lg text-muted-foreground font-normal">/ mes</span>
                        </div>
                        <p className="text-sm text-muted-foreground">
                            Cancela en cualquier momento. Acceso inmediato después del pago.
                        </p>

                        <Button className="w-full h-12 text-lg gap-2" size="lg">
                            <CreditCard className="h-5 w-5" />
                            Suscribirse Ahora
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
