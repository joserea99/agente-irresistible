"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// Add support for the non-standard Web Speech API in TypeScript
declare global {
    interface Window {
        webkitSpeechRecognition: any;
        SpeechRecognition: any;
    }
}

interface UseSpeechToTextProps {
    onResult?: (transcript: string) => void;
    language?: string;
}

export function useSpeechToText({ onResult, language = "es-ES" }: UseSpeechToTextProps = {}) {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState("");
    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        // Check if browser supports speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = false; // Stop after one sentence for "walkie-talkie" feel
            recognition.interimResults = true; // Show results while talking
            recognition.lang = language;

            recognition.onstart = () => {
                setIsListening(true);
            };

            recognition.onend = () => {
                setIsListening(false);
            };

            recognition.onresult = (event: any) => {
                let currentTranscript = "";
                for (let i = event.resultIndex; i < event.results.length; i++) {
                    currentTranscript += event.results[i][0].transcript;
                }
                setTranscript(currentTranscript);

                if (onResult && event.results[0].isFinal) {
                    onResult(currentTranscript);
                }
            };

            recognition.onerror = (event: any) => {
                console.error("Speech recognition error", event.error);
                setIsListening(false);
            };

            recognitionRef.current = recognition;
        }

        return () => {
            if (recognitionRef.current) {
                recognitionRef.current.abort();
            }
        }
    }, [language, onResult]);

    const startListening = useCallback(() => {
        if (recognitionRef.current && !isListening) {
            setTranscript("");
            try {
                recognitionRef.current.start();
            } catch (e) {
                console.error("Start error", e);
            }
        }
    }, [isListening]);

    const stopListening = useCallback(() => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
        }
    }, [isListening]);

    return {
        isListening,
        transcript,
        startListening,
        stopListening,
        hasSupport: typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition)
    };
}
