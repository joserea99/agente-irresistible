"use client";

import { useAuthStore } from "@/lib/store";
import { supabase } from "@/lib/supabase";
import { useLanguage } from "@/lib/language-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
    LayoutDashboard,
    Users,
    LogOut,
    Menu,
    Globe,
    Swords,
    ShieldAlert,
    BookOpen,
    Sparkles,
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, token, logout } = useAuthStore();
    const { t, language, toggleLanguage } = useLanguage();
    const router = useRouter();
    const pathname = usePathname();

    const [isHydrated, setIsHydrated] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    useEffect(() => {
        setIsHydrated(true);

        const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
            if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
                if (session) {
                    const fetchProfile = async () => {
                        const { data: profile } = await supabase
                            .from('profiles')
                            .select('*')
                            .eq('id', session.user.id)
                            .single();

                        useAuthStore.getState().login(session.access_token, {
                            username: session.user.email || "",
                            full_name: profile?.full_name || session.user.user_metadata.full_name || "",
                            role: profile?.role || "member"
                        });
                    };
                    fetchProfile();
                }
            } else if (event === 'SIGNED_OUT') {
                logout();
                router.push("/login");
            }
        });

        return () => {
            subscription.unsubscribe();
        };
    }, [logout, router]);

    useEffect(() => {
        if (isHydrated && !token) {
            router.push("/login");
        }
    }, [token, router, isHydrated]);

    if (!isHydrated) return null;
    if (!user) return null;

    const isEs = language === 'es';

    const links = [
        {
            href: "/dashboard",
            label: isEs ? "Centro de Mando" : "Command Center",
            shortLabel: isEs ? "Inicio" : "Home",
            icon: LayoutDashboard,
        },
        {
            href: "/studio",
            label: isEs ? "Prepara tu Semana" : "Prepare Your Week",
            shortLabel: isEs ? "Tu Semana" : "Weekly",
            icon: BookOpen,
            badge: isEs ? "1-Clic" : "1-Click",
        },
        {
            href: "/chat",
            label: isEs ? "Consulta con Especialistas" : "Ask the Specialists",
            shortLabel: isEs ? "Especialistas" : "Specialists",
            icon: Users,
        },
        {
            href: "/dojo",
            label: isEs ? "Entrenamiento de Líderes" : "Leadership Dojo",
            shortLabel: isEs ? "Entrenar" : "Train",
            icon: Swords,
        },
        ...((user.role === 'admin' || user.role === 'pastor_principal') ? [
            {
                href: "/admin",
                label: isEs ? "Administración y Sync" : "Admin & Sync",
                shortLabel: "Admin",
                icon: ShieldAlert,
            },
        ] : []),
    ];

    const SidebarContent = () => (
        <div className="flex flex-col h-full bg-sidebar text-sidebar-foreground">
            <div className="p-6 border-b border-sidebar-border">
                <div className="flex items-center gap-2.5">
                    <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground font-heading font-bold text-sm shadow-sm">
                        IA
                    </div>
                    <div>
                        <h1 className="text-base font-bold font-heading tracking-tight text-foreground leading-none">
                            Irresistible Agent
                        </h1>
                        <p className="text-[11px] text-muted-foreground mt-1 font-medium">
                            {isEs ? "Claridad, Recursos & Liderazgo" : "Clarity, Resources & Leadership"}
                        </p>
                    </div>
                </div>
            </div>

            <div className="flex-1 py-5 px-3 space-y-1">
                <div className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/70">
                    {isEs ? "Espacios de Trabajo" : "Workspaces"}
                </div>
                {links.map((link) => {
                    const isActive = pathname === link.href;
                    return (
                        <Link
                            key={link.href}
                            href={link.href}
                            className="block"
                            onClick={() => setMobileMenuOpen(false)}
                        >
                            <Button
                                variant="ghost"
                                className={cn(
                                    "w-full justify-start gap-3 h-10 px-3 transition-all duration-150 rounded-lg",
                                    isActive
                                        ? "bg-card text-primary shadow-xs border border-border/80 font-semibold"
                                        : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/70 font-normal"
                                )}
                            >
                                <link.icon className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-muted-foreground")} />
                                <span className="truncate text-sm">{link.label}</span>
                                {link.badge && (
                                    <span className="ml-auto text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-primary/12 text-primary">
                                        {link.badge}
                                    </span>
                                )}
                                {!link.badge && isActive && (
                                    <motion.div layoutId="active-pill" className="ml-auto w-1.5 h-1.5 bg-primary rounded-full" />
                                )}
                            </Button>
                        </Link>
                    );
                })}

                {/* Highlight CTA to Sunday Studio */}
                <div className="pt-4 px-1">
                    <Link href="/studio" onClick={() => setMobileMenuOpen(false)}>
                        <div className="rounded-xl p-3.5 bg-gradient-to-br from-primary/12 via-primary/6 to-transparent border border-primary/20 hover:border-primary/40 transition-all cursor-pointer">
                            <div className="flex items-center gap-2 text-xs font-semibold text-primary mb-1">
                                <Sparkles className="h-3.5 w-3.5" />
                                {isEs ? "Prepara tu Semana" : "Prepare Your Week"}
                            </div>
                            <p className="text-[11px] text-muted-foreground leading-relaxed">
                                {isEs
                                    ? "Genera bosquejo, guía de grupos, lección de niños y orden de servicio en 1 clic."
                                    : "Generate sermon outline, group guide, kids lesson & run sheet in 1 click."}
                            </p>
                        </div>
                    </Link>
                </div>
            </div>

            <div className="p-4 border-t border-sidebar-border space-y-3 bg-sidebar">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start gap-2.5 text-xs text-muted-foreground hover:text-foreground h-8"
                    onClick={toggleLanguage}
                >
                    <Globe className="h-3.5 w-3.5" />
                    {language === 'en' ? 'Idioma: Español' : 'Language: English'}
                </Button>

                <div className="flex items-center gap-3 px-2 py-1.5 rounded-lg bg-card/60 border border-border/60">
                    <div className="h-8 w-8 rounded-full bg-primary/15 text-primary flex items-center justify-center font-bold text-xs shrink-0">
                        {user.full_name?.[0]?.toUpperCase() || "L"}
                    </div>
                    <div className="overflow-hidden flex-1">
                        <p className="text-xs font-semibold text-foreground truncate">{user.full_name}</p>
                        <p className="text-[11px] text-muted-foreground truncate capitalize">
                            {user.role.replace(/_/g, ' ')}
                        </p>
                    </div>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    className="w-full text-xs text-muted-foreground hover:text-destructive hover:border-destructive/30 hover:bg-destructive/5 h-8"
                    onClick={async () => {
                        await supabase.auth.signOut();
                        logout();
                        router.push("/login");
                    }}
                >
                    <LogOut className="h-3.5 w-3.5 mr-2" />
                    {t.common.logout}
                </Button>
            </div>
        </div>
    );

    return (
        <div className="flex h-[100dvh] bg-background overflow-hidden">
            {/* Desktop Sidebar */}
            <aside className="hidden md:block w-64 bg-sidebar border-r border-sidebar-border shrink-0">
                <SidebarContent />
            </aside>

            <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                {/* Mobile Header */}
                <header className="md:hidden h-13 border-b border-border flex items-center px-3.5 justify-between bg-card/95 backdrop-blur-md sticky top-0 z-20 shrink-0">
                    <Link href="/dashboard" className="flex items-center gap-2 min-w-0">
                        <div className="h-7 w-7 rounded-md bg-primary flex items-center justify-center text-primary-foreground font-heading font-bold text-xs shrink-0">
                            IA
                        </div>
                        <span className="font-bold font-heading text-sm text-foreground truncate">
                            Irresistible Agent
                        </span>
                    </Link>
                    <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-9 w-9">
                                <Menu className="h-5 w-5" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="p-0 w-68 bg-sidebar border-r border-sidebar-border">
                            <SidebarContent />
                        </SheetContent>
                    </Sheet>
                </header>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto overflow-x-hidden p-3 sm:p-5 md:p-8 relative">
                    <div className="relative z-10 max-w-6xl mx-auto">
                        {children}
                    </div>
                </main>

                {/* Mobile Bottom Navigation Bar */}
                <nav className="md:hidden border-t border-border bg-card/95 backdrop-blur-md px-1 py-1 flex items-center justify-around shrink-0 z-20">
                    {links.slice(0, 4).map((link) => {
                        const isActive = pathname === link.href;
                        return (
                            <Link
                                key={link.href}
                                href={link.href}
                                className={cn(
                                    "flex flex-col items-center justify-center py-1 px-2.5 rounded-lg transition-colors min-w-[68px]",
                                    isActive
                                        ? "text-primary font-semibold"
                                        : "text-muted-foreground hover:text-foreground font-medium"
                                )}
                            >
                                <link.icon className={cn("h-4 w-4 mb-0.5", isActive ? "text-primary" : "text-muted-foreground")} />
                                <span className="text-[10px] leading-tight truncate">{link.shortLabel}</span>
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </div>
    );
}
