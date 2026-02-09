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
import { Trash2, UserCog, ShieldAlert } from "lucide-react";
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
        }
    }, [user]);

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
                                                <Badge variant={u.subscription_status === 'active' ? 'default' : 'secondary'}>
                                                    {u.subscription_status}
                                                </Badge>
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
