"use client";

import { Mic, MicOff } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface MicButtonProps {
    isListening: boolean;
    onStart: () => void;
    onStop: () => void;
    className?: string;
    disabled?: boolean;
}

export function MicButton({ isListening, onStart, onStop, className, disabled }: MicButtonProps) {
    return (
        <Button
            type="button" // Prevent submitting forms
            variant={isListening ? "destructive" : "secondary"}
            size="icon"
            className={cn(
                "rounded-full transition-all duration-300",
                isListening ? "animate-pulse shadow-lg shadow-red-500/50" : "",
                className
            )}
            onClick={isListening ? onStop : onStart}
            disabled={disabled}
            title={isListening ? "Stop Listening" : "Start Voice Input"}
        >
            {isListening ? (
                <Mic className="h-5 w-5 animate-bounce" />
            ) : (
                <Mic className="h-5 w-5" />
            )}
        </Button>
    );
}
