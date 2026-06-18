"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/store";
import { Loader2, Save, CheckCircle2, Building2 } from "lucide-react";

interface ChurchProfile {
    church_name?: string;
    city?: string;
    country?: string;
    size?: string;
    service_schedule?: string;
    current_series?: string;
    vision?: string;
    notes?: string;
}

const FIELDS: { key: keyof ChurchProfile; label: string; placeholder: string; textarea?: boolean }[] = [
    { key: "church_name", label: "Nombre de la iglesia", placeholder: "Ej: Iglesia Vida Nueva" },
    { key: "city", label: "Ciudad", placeholder: "Ej: Bogotá" },
    { key: "country", label: "País", placeholder: "Ej: Colombia" },
    { key: "size", label: "Tamaño / asistencia", placeholder: "Ej: 250 asistentes promedio" },
    { key: "service_schedule", label: "Horario de servicios", placeholder: "Ej: Domingos 9am y 11am" },
    { key: "current_series", label: "Serie / predicación actual", placeholder: "Ej: 'Reconstruyendo' (Nehemías)" },
    { key: "vision", label: "Visión / 'el win'", placeholder: "¿Cómo se ve el éxito para tu iglesia?", textarea: true },
    { key: "notes", label: "Notas adicionales", placeholder: "Cualquier contexto que el agente deba recordar siempre", textarea: true },
];

export function ChurchProfileEditor() {
    const [profile, setProfile] = useState<ChurchProfile>({});
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [saved, setSaved] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        (async () => {
            try {
                const res = await api.get("/church/profile");
                setProfile(res.data.profile || {});
            } catch {
                // table may not exist yet — start empty
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    const handleSave = async () => {
        setSaving(true);
        setSaved(false);
        setError("");
        try {
            await api.put("/church/profile", profile);
            setSaved(true);
            setTimeout(() => setSaved(false), 2500);
        } catch (e: any) {
            setError(e?.response?.data?.detail || "No se pudo guardar. Verifica que la migración 003 esté aplicada.");
        } finally {
            setSaving(false);
        }
    };

    const set = (key: keyof ChurchProfile, value: string) => setProfile((p) => ({ ...p, [key]: value }));

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Building2 className="h-5 w-5 text-primary" />
                    Memoria de la Iglesia
                </CardTitle>
                <CardDescription>
                    El agente usa esta información en cada respuesta para darte consejos a la medida de tu iglesia, no genéricos.
                </CardDescription>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex items-center gap-2 text-muted-foreground py-8 justify-center">
                        <Loader2 className="h-4 w-4 animate-spin" /> Cargando perfil...
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="grid gap-4 sm:grid-cols-2">
                            {FIELDS.filter((f) => !f.textarea).map((f) => (
                                <div key={f.key} className="space-y-1.5">
                                    <Label htmlFor={f.key}>{f.label}</Label>
                                    <Input
                                        id={f.key}
                                        value={profile[f.key] || ""}
                                        onChange={(e) => set(f.key, e.target.value)}
                                        placeholder={f.placeholder}
                                    />
                                </div>
                            ))}
                        </div>
                        {FIELDS.filter((f) => f.textarea).map((f) => (
                            <div key={f.key} className="space-y-1.5">
                                <Label htmlFor={f.key}>{f.label}</Label>
                                <Textarea
                                    id={f.key}
                                    value={profile[f.key] || ""}
                                    onChange={(e) => set(f.key, e.target.value)}
                                    placeholder={f.placeholder}
                                    rows={3}
                                />
                            </div>
                        ))}

                        {error && <p className="text-sm text-destructive">{error}</p>}

                        <div className="flex items-center gap-3">
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
                                Guardar memoria
                            </Button>
                            {saved && (
                                <span className="flex items-center gap-1.5 text-sm text-green-600">
                                    <CheckCircle2 className="h-4 w-4" /> Guardado
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
