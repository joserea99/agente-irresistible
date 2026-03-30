"use client";

import { useState, useEffect, useRef, useCallback } from "react";

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
    const isIntentionallyListening = useRef(false);
    const isListeningRef = useRef(false); // Mirror state in ref to avoid race conditions
    const onResultRef = useRef(onResult); // Store callback in ref to keep recognition stable

    // Keep the ref current without triggering recognition recreation
    useEffect(() => {
        onResultRef.current = onResult;
    }, [onResult]);

    // Only recreate recognition when language changes (not on every render)
    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) return;

        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = language;

        recognition.onstart = () => {
            isListeningRef.current = true;
            setIsListening(true);
        };

        recognition.onend = () => {
            if (isIntentionallyListening.current) {
                // Browser silence timeout — auto-restart with retry
                const tryRestart = (attempt: number) => {
                    try {
                        recognition.start();
                    } catch (e) {
                        if (attempt < 2) {
                            setTimeout(() => tryRestart(attempt + 1), 300);
                        } else {
                            console.error("Failed to restart after retries:", e);
                            isListeningRef.current = false;
                            setIsListening(false);
                            isIntentionallyListening.current = false;
                        }
                    }
                };
                tryRestart(0);
            } else {
                isListeningRef.current = false;
                setIsListening(false);
            }
        };

        recognition.onresult = (event: any) => {
            let interimTranscript = "";

            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                const transcriptText = result[0].transcript;

                if (result.isFinal) {
                    if (onResultRef.current) {
                        onResultRef.current(transcriptText);
                    }
                } else {
                    interimTranscript += transcriptText;
                }
            }
            setTranscript(interimTranscript);
        };

        recognition.onerror = (event: any) => {
            // Ignore non-fatal errors that happen during normal operation
            if (event.error === 'no-speech' || event.error === 'aborted') {
                return;
            }
            console.error("Speech recognition error:", event.error);
            isListeningRef.current = false;
            setIsListening(false);
            isIntentionallyListening.current = false;
        };

        recognitionRef.current = recognition;

        return () => {
            if (recognitionRef.current) {
                isIntentionallyListening.current = false;
                recognitionRef.current.abort();
            }
        };
    }, [language]); // Only language — onResult is in a ref

    const startListening = useCallback(() => {
        // Use ref instead of state to avoid async race condition
        if (recognitionRef.current && !isListeningRef.current) {
            isIntentionallyListening.current = true;
            setTranscript("");
            try {
                recognitionRef.current.start();
            } catch (e) {
                // If already started, stop first then restart
                try {
                    recognitionRef.current.stop();
                    setTimeout(() => {
                        try {
                            recognitionRef.current?.start();
                        } catch (_) {
                            isIntentionallyListening.current = false;
                        }
                    }, 200);
                } catch (_) {
                    isIntentionallyListening.current = false;
                }
            }
        }
    }, []);

    const stopListening = useCallback(() => {
        isIntentionallyListening.current = false;
        if (recognitionRef.current) {
            try {
                recognitionRef.current.stop();
            } catch (_) {
                // Already stopped
            }
        }
        isListeningRef.current = false;
        setIsListening(false);
    }, []);

    return {
        isListening,
        transcript,
        startListening,
        stopListening,
        hasSupport: typeof window !== "undefined" && !!(window.SpeechRecognition || window.webkitSpeechRecognition)
    };
}
