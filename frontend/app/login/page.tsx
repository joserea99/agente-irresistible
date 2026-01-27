"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore, api } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Lock, User } from "lucide-react";
import { motion } from "framer-motion";

import Cookies from 'js-cookie';

export default function LoginPage() {
    const [username, setUsername] = useState("");
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
            // Fingerprint simulation (simplified for demo)
            const deviceFingerprint = navigator.userAgent + (new Date()).getMonth(); // Simple fingerprint
            const response = await api.post("/auth/login", {
                username,
                password,
                device_fingerprint: deviceFingerprint
            });
            login(response.data.access_token, response.data.user);
            Cookies.set('access_token', response.data.access_token, { expires: 1, path: '/' }); // Explicit path to avoid duplicates
            router.push("/dashboard");
        } catch (err: any) {
            console.error("Login Error Full:", err);
            const detail = err.response?.data?.detail;
            console.log("Error Detail:", detail);
            console.log("Error Status:", err.response?.status);

            if (err.response?.status === 403) {
                if (detail?.includes("Trial")) {
                    router.push("/subscription?reason=trial_expired");
                    return;
                }
                if (detail?.includes("Subscription")) {
                    router.push("/subscription?reason=expired");
                    return;
                }
            }

            if (err.response?.status === 401) {
                if (detail?.includes("New device")) {
                    console.log("Redirecting to verify-device...");
                    router.push("/verify-device");
                    return;
                }
                // Handle "Incorrect username or password" specifically if needed
            }

            // Fallback to error from server or generic localized error
            const errorMessage = detail || t.auth.error;
            console.error("Setting error message:", errorMessage);
            setError(errorMessage);
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
                                <Label htmlFor="username">{t.auth.usernameParams}</Label>
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        id="username"
                                        placeholder={t.auth.usernameParams}
                                        className="pl-9 bg-background/50 border-input focus:border-primary transition-all"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
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
                                Don't have an account?{" "}
                                <a
                                    href="/register"
                                    className="text-primary hover:underline font-medium"
                                >
                                    Sign up
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
