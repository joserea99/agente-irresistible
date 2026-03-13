"use client";

import DashboardLayout from "@/components/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useAuthStore, api } from "@/lib/store";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Trash2, UserCog, RefreshCw, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { AVAILABLE_ROLES } from "@/lib/dashboard-config";

interface UserData {
    id: string; // Added ID for deletion/updates
    username: string;
    full_name: string;
    role: string;
    subscription_status: string;
    updated_at: string;
}

export default function AdminPage() {
    const { user } = useAuthStore();
    const router = useRouter();
    const [users, setUsers] = useState<UserData[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [syncStatus, setSyncStatus] = useState<any>(null);
    const [isSyncing, setIsSyncing] = useState(false);
    const [syncMessage, setSyncMessage] = useState("");

    // Protected Route Check
    useEffect(() => {
        if (user && user.role !== 'admin') {
            router.push('/dashboard');
        }
    }, [user, router]);

    const fetchUsers = async () => {
        try {
            const response = await api.get("/auth/users");
            setUsers(response.data);
        } catch (error) {
            console.error("Failed to fetch users", error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (user?.role === 'admin') {
            fetchUsers();
            fetchSyncStatus();
        }
    }, [user]);

    const fetchSyncStatus = async () => {
        try {
            const response = await api.get("/sync/status");
            setSyncStatus(response.data);
        } catch (error) {
            console.error("Failed to fetch sync status", error);
        }
    };

    const handleTriggerSync = async () => {
        if (!confirm("¿Lanzar sincronización completa del Brandfolder? Solo se indexará contenido NUEVO. La memoria existente NO se modifica.")) return;
        setIsSyncing(true);
        setSyncMessage("");
        try {
            const response = await api.post("/sync/trigger");
            setSyncMessage("✅ " + response.data.message);
            // Poll status after a couple seconds
            setTimeout(fetchSyncStatus, 3000);
        } catch (error) {
            setSyncMessage("❌ Error al lanzar la sincronización. Revisa los logs.");
        } finally {
            setIsSyncing(false);
        }
    };

    const handleRoleChange = async (userId: string, newRole: string) => {
        try {
            await api.put(`/auth/users/${userId}/role`, { role: newRole });
            // Optimistic update
            setUsers(users.map(u => u.id === userId ? { ...u, role: newRole } : u));
        } catch (error) {
            console.error("Failed to update role", error);
            alert("Failed to update role");
        }
    };

    const handleSubscriptionChange = async (userId: string, newStatus: string) => {
        try {
            await api.put(`/auth/users/${userId}/subscription`, { status: newStatus });
            // Optimistic update
            setUsers(users.map(u => u.id === userId ? { ...u, subscription_status: newStatus } : u));
        } catch (error) {
            console.error("Failed to update subscription", error);
            alert("Failed to update subscription status");
        }
    };

    const handleDeleteUser = async (userId: string) => {
        if (!confirm(`Are you sure you want to delete this user? This action cannot be undone.`)) return;

        try {
            await api.delete(`/auth/users/${userId}`);
            setUsers(users.filter(u => u.id !== userId));
        } catch (error) {
            console.error("Failed to delete user", error);
            alert("Failed to delete user");
        }
    };

    if (user?.role !== 'admin') return <div className="p-8 text-center">Unauthorized</div>;

    // Get all available roles from our config + admin/member
    const availableRoles = Array.from(new Set([
        "admin",
        "admin",
        "member",
        ...AVAILABLE_ROLES
    ]));

    return (
        <DashboardLayout>
            <div className="space-y-8">
                <div className="flex flex-col gap-2">
                    <h2 className="text-3xl font-bold font-heading tracking-tight">Admin Console</h2>
                    <p className="text-muted-foreground">Manage users, roles, and system access.</p>
                </div>

                {/* ─── Sync Card ─── */}
                <Card className="border-primary/30">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <RefreshCw className="h-5 w-5 text-primary" />
                            Sincronización de Conocimiento
                        </CardTitle>
                        <CardDescription>
                            Escanea toda la biblioteca del Brandfolder e indexa el contenido nuevo en la memoria del agente.
                            El contenido ya existente NO se toca.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        {/* Status display */}
                        {syncStatus && (
                            <div className="rounded-lg bg-muted/50 p-4 text-sm space-y-1">
                                <div className="flex items-center gap-2 font-medium">
                                    {syncStatus.status === "completed" && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                                    {syncStatus.status === "running" && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                                    {syncStatus.status === "failed" && <AlertCircle className="h-4 w-4 text-destructive" />}
                                    {syncStatus.status === "never_run" && <AlertCircle className="h-4 w-4 text-muted-foreground" />}
                                    <span className="capitalize">Estado: {syncStatus.status ?? "Sin datos"}</span>
                                </div>
                                {syncStatus.status !== "never_run" && (
                                    <>
                                        <p className="text-muted-foreground">Iniciada: {syncStatus.started_at ?? "—"}</p>
                                        <p className="text-muted-foreground">Completada: {syncStatus.completed_at ?? "En progreso..."}</p>
                                        <div className="flex gap-4 pt-1">
                                            <span className="text-green-600 font-medium">✅ Nuevos: {syncStatus.new_indexed ?? 0}</span>
                                            <span className="text-muted-foreground">⏭️ Omitidos: {syncStatus.skipped ?? 0}</span>
                                            <span className="text-destructive">❌ Fallidos: {syncStatus.failed ?? 0}</span>
                                        </div>
                                    </>
                                )}
                                {syncStatus.status === "never_run" && (
                                    <p className="text-muted-foreground">Nunca se ha ejecutado una sincronización completa.</p>
                                )}
                            </div>
                        )}

                        {/* Trigger button */}
                        <div className="flex items-center gap-4">
                            <Button
                                onClick={handleTriggerSync}
                                disabled={isSyncing || syncStatus?.status === "running"}
                                className="flex items-center gap-2"
                            >
                                {isSyncing ? (
                                    <><Loader2 className="h-4 w-4 animate-spin" /> Lanzando...</>
                                ) : (
                                    <><RefreshCw className="h-4 w-4" /> Sincronizar Todo Ahora</>
                                )}
                            </Button>
                            <Button variant="outline" size="sm" onClick={fetchSyncStatus}>
                                Actualizar estado
                            </Button>
                        </div>
                        {syncMessage && (
                            <p className="text-sm font-medium mt-1">{syncMessage}</p>
                        )}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <UserCog className="h-5 w-5" />
                            User Management
                        </CardTitle>
                        <CardDescription>Assign roles to grant access to specific Dashboards.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-md border">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>User</TableHead>
                                        <TableHead>Role (Dashboard Access)</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {users.map((u) => (
                                        <TableRow key={u.username}>
                                            <TableCell>
                                                <div className="flex flex-col">
                                                    <span className="font-medium">{u.full_name}</span>
                                                    <span className="text-xs text-muted-foreground">{u.username}</span>
                                                </div>
                                            </TableCell>
                                            <TableCell>
                                                <Select
                                                    value={u.role}
                                                    onValueChange={(val) => handleRoleChange(u.id, val)}
                                                    disabled={u.username === user.username} // Prevent changing own role effectively to lock out
                                                >
                                                    <SelectTrigger className="w-[180px] h-8 text-xs">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {availableRoles.map(role => (
                                                            <SelectItem key={role} value={role}>
                                                                {role.replace('_', ' ').toUpperCase()}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell>
                                                <Select
                                                    value={u.subscription_status}
                                                    onValueChange={(val) => handleSubscriptionChange(u.id, val)}
                                                >
                                                    <SelectTrigger className="w-[120px] h-8 text-xs">
                                                        <SelectValue />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {["active", "trial", "past_due", "canceled"].map(status => (
                                                            <SelectItem key={status} value={status}>
                                                                {status.toUpperCase()}
                                                            </SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                {u.username !== user.username && (
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-8 w-8 text-destructive hover:text-destructive/90"
                                                        onClick={() => handleDeleteUser(u.id)}
                                                    >
                                                        <Trash2 className="h-4 w-4" />
                                                    </Button>
                                                )}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                    {users.length === 0 && !isLoading && (
                                        <TableRow>
                                            <TableCell colSpan={4} className="text-center h-24 text-muted-foreground">
                                                No users found.
                                            </TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </DashboardLayout>
    );
}
