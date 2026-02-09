"use client";

import { useAuthStore } from "@/lib/store";
import { useLanguage } from "@/lib/language-context";
import { useRouter, usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Sidebar, LayoutDashboard, MessageSquare, Database, LogOut, ChevronRight, Menu, Globe, Swords, ShieldAlert } from "lucide-react";
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

    useEffect(() => {
        setIsHydrated(true);
    }, []);

    useEffect(() => {
        if (isHydrated && !token) {
            router.push("/login");
        }
    }, [token, router, isHydrated]);

    if (!isHydrated) return null; // Or a loading spinner
    if (!user) return null;

    const links = [
        { href: "/dashboard", label: t.dashboard.overview, icon: LayoutDashboard },
        { href: "/chat", label: t.dashboard.strategicAgent, icon: MessageSquare },
        { href: "/knowledge", label: t.dashboard.knowledgeBase, icon: Database },
        { href: "/dojo", label: t.dojo.title, icon: Swords }, // Leadership Dojo
        ...(user.role === 'admin' ? [{ href: "/admin", label: "Admin Console", icon: ShieldAlert }] : []),
    ];

    const SidebarContent = () => (
        <div className="flex flex-col h-full">
            <div className="p-6 border-b border-sidebar-border/50">
                <h1 className="text-xl font-bold font-heading text-primary bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">
                    Irresistible
                </h1>
                <p className="text-xs text-muted-foreground">{t.common.appTagline}</p>
            </div>
            <div className="flex-1 py-6 px-3 space-y-1">
                {links.map((link) => (
                    <Link key={link.href} href={link.href}>
                        <Button
                            variant="ghost"
                            className={cn(
                                "w-full justify-start gap-3 transition-all duration-200",
                                pathname === link.href
                                    ? "bg-sidebar-accent text-primary shadow-md font-medium"
                                    : "text-muted-foreground hover:text-foreground hover:bg-sidebar-accent/50"
                            )}
                        >
                            <link.icon className="h-4 w-4" />
                            {link.label}
                            {pathname === link.href && (
                                <motion.div layoutId="active-pill" className="ml-auto w-1 h-4 bg-primary rounded-full" />
                            )}
                        </Button>
                    </Link>
                ))}
            </div>
            <div className="p-4 border-t border-sidebar-border/50 space-y-3">
                <Button
                    variant="ghost"
                    size="sm"
                    className="w-full justify-start gap-3 text-muted-foreground hover:text-foreground"
                    onClick={toggleLanguage}
                >
                    <Globe className="h-4 w-4" />
                    {language === 'en' ? 'Cambiar a Español' : 'Switch to English'}
                </Button>

                <div className="flex items-center gap-3 px-2">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-primary to-accent flex items-center justify-center text-white font-bold text-xs ring-2 ring-background">
                        {user.full_name?.[0] || "U"}
                    </div>
                    <div className="overflow-hidden">
                        <p className="text-sm font-medium truncate">{user.full_name}</p>
                        <p className="text-xs text-muted-foreground truncate capitalize">{user.role}</p>
                    </div>
                </div>
                <Button variant="outline" className="w-full text-destructive border-destructive/20 hover:bg-destructive/10" onClick={() => { logout(); router.push("/login"); }}>
                    <LogOut className="h-4 w-4 mr-2" />
                    {t.common.logout}
                </Button>
            </div>
        </div>
    );

    return (
        <div className="flex h-screen bg-background overflow-hidden">
            {/* Desktop Sidebar */}
            <aside className="hidden md:block w-64 bg-sidebar border-r border-sidebar-border">
                <SidebarContent />
            </aside>

            <div className="flex-1 flex flex-col h-full overflow-hidden relative">
                {/* Mobile Header */}
                <header className="md:hidden h-14 border-b border-border flex items-center px-4 justify-between bg-card/80 backdrop-blur-md sticky top-0 z-20">
                    <span className="font-bold font-heading text-primary">Irresistible</span>
                    <Sheet>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon"><Menu className="h-5 w-5" /></Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="p-0 w-64 bg-sidebar border-r border-sidebar-border">
                            <SidebarContent />
                        </SheetContent>
                    </Sheet>
                </header>

                {/* Main Content Area */}
                <main className="flex-1 overflow-auto p-4 md:p-8 relative">
                    {/* Gradient Splashes */}
                    <div className="absolute top-0 left-0 w-full h-[500px] bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 max-w-6xl mx-auto">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
