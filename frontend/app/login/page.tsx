"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Lock, User } from "lucide-react";
import { motion } from "framer-motion";
import { supabase } from "@/lib/supabase";
import Cookies from 'js-cookie';

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();
    const login = useAuthStore((state) => state.login);
    const { t } = useLanguage();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const { data, error } = await supabase.auth.signInWithPassword({
                email: email,
                password: password,
            });

            if (error) throw error;

            if (data.session && data.user) {
                // Fetch extra profile data if needed, but for now relies on store
                // We'll update store to handle session
                const { data: profile } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', data.user.id)
                    .single();

                const userData = {
                    username: data.user.email || "",
                    full_name: profile?.full_name || data.user.user_metadata?.full_name || "Usuario",
                    role: profile?.role || "member"
                };

                login(data.session.access_token, userData);
                Cookies.set('access_token', data.session.access_token, { expires: 1, path: '/' });

                router.push("/dashboard");
            }
        } catch (err: any) {
            console.error("Login Error:", err);
            setError(err.message || "Error al iniciar sesión");
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
            >
                <Card className="w-[400px] border-sidebar-border bg-card/50 backdrop-blur-xl shadow-2xl">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl font-bold font-heading text-primary">{t.auth.signInTitle}</CardTitle>
                        <CardDescription>{t.auth.signInDescription}</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleLogin} className="space-y-4">
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
                            <div className="space-y-2">
                                <Label htmlFor="password">{t.auth.passwordParams}</Label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="password"
                                        type="password"
                                        placeholder={t.auth.passwordParams}
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                            {error && <p className="text-sm text-destructive font-medium">{error}</p>}
                            <Button type="submit" className="w-full bg-primary hover:bg-primary/90 transition-all shadow-lg shadow-primary/25" disabled={isLoading}>
                                {isLoading ? t.auth.loggingIn : t.auth.signInButton}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="flex flex-col space-y-2">
                        <div className="text-center">
                            <p className="text-sm text-muted-foreground">
                                ¿No tienes cuenta?{" "}
                                <a
                                    href="/register"
                                    className="text-primary hover:underline font-medium"
                                >
                                    Regístrate
                                </a>
                            </p>
                        </div>
                        <p className="text-xs text-muted-foreground text-center">{t.common.appName} Security</p>
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
