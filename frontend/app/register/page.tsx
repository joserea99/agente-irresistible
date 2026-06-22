"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Lock, User, Mail, UserCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "@/lib/language-context";

export default function RegisterPage() {
    const { language } = useLanguage();
    const t = {
        title:        language === 'es' ? "Crear Cuenta"                              : "Create Account",
        description:  language === 'es' ? "Regístrate para acceder al Agente Estratégico" : "Sign up to access the Strategic Agent",
        fullName:     language === 'es' ? "Nombre Completo"                           : "Full Name",
        username:     language === 'es' ? "Nombre de Usuario"                        : "Username",
        email:        language === 'es' ? "Correo Electrónico"                       : "Email",
        password:     language === 'es' ? "Contraseña"                               : "Password",
        submit:       language === 'es' ? "Registrarse"                              : "Sign Up",
        loading:      language === 'es' ? "Creando Cuenta..."                        : "Creating Account...",
        success:      language === 'es' ? "¡Cuenta creada! Redirigiendo..."          : "Account created! Redirecting...",
        hasAccount:   language === 'es' ? "¿Ya tienes cuenta?"                       : "Already have an account?",
        signIn:       language === 'es' ? "Inicia sesión"                            : "Sign in",
        footer:       language === 'es' ? "Seguridad Irresistible Agent"             : "Irresistible Agent Security",
    };

    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        full_name: ""
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");
    const router = useRouter();

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");
        setSuccessMessage("");

        try {
            // 1. Sign up with Supabase Auth
            const { data, error: authError } = await supabase.auth.signUp({
                email: formData.email,
                password: formData.password,
                options: {
                    data: {
                        full_name: formData.full_name,
                        username: formData.username
                    },
                    emailRedirectTo: `${window.location.origin}/dashboard` // Redirect back to dashboard after confirmation
                }
            });

            if (authError) throw authError;

            // 2. Check if confirmation is required
            if (data.user && data.user.identities && data.user.identities.length === 0) {
                setError("This email is already taken.");
                return;
            }

            // Supabase trigger should handle profile creation in 'public.profiles'

            setSuccessMessage(t.success);

            // Short delay then redirect
            setTimeout(() => {
                router.push("/login?registered=true");
            }, 1500);

        } catch (err: any) {
            console.error("Registration Error:", err);
            setError(err.message || "Registration failed. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
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
            >
                <Card className="w-[450px] border-sidebar-border bg-card/50 backdrop-blur-xl shadow-2xl">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl font-bold font-heading text-primary">{t.title}</CardTitle>
                        <CardDescription>{t.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="full_name">{t.fullName}</Label>
                                <div className="relative">
                                    <UserCircle className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="full_name"
                                        name="full_name"
                                        placeholder="John Doe"
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={formData.full_name}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="username">{t.username}</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="username"
                                        name="username"
                                        placeholder="johndoe"
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={formData.username}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">{t.email}</Label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="email"
                                        name="email"
                                        type="email"
                                        placeholder="john@example.com"
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={formData.email}
                                        onChange={handleChange}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="password">{t.password}</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="password"
                                        name="password"
                                        type="password"
                                        placeholder="••••••••"
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={formData.password}
                                        onChange={handleChange}
                                        required
                                        minLength={6}
                                    />
                                </div>
                            </div>
                            {error && <p className="text-sm text-destructive font-medium">{error}</p>}
                            {successMessage && <p className="text-sm text-green-500 font-medium">{successMessage}</p>}
                            <Button
                                type="submit"
                                className="w-full bg-primary hover:bg-primary/90 transition-all shadow-lg shadow-primary/25"
                                disabled={isLoading}
                            >
                                {isLoading ? t.loading : t.submit}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-2">
                        <div className="text-center">
                            <p className="text-sm text-muted-foreground">
                                {t.hasAccount}{" "}
                                <a href="/login" className="text-primary hover:underline font-medium">
                                    {t.signIn}
                                </a>
                            </p>
                        </div>
                        <p className="text-xs text-muted-foreground text-center">{t.footer}</p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
