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
    const isIntentionallyListening = useRef(false); // Track if user wants it on

    useEffect(() => {
        // Check if browser supports speech recognition
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (SpeechRecognition) {
            const recognition = new SpeechRecognition();
            recognition.continuous = true;
            recognition.interimResults = true;
            recognition.lang = language;

            recognition.onstart = () => {
                setIsListening(true);
            };

            recognition.onend = () => {
                // If the user didn't stop it, restart it (browser silence timeout)
                if (isIntentionallyListening.current) {
                    try {
                        recognition.start();
                        console.log("🔄 Auto-restarting speech recognition...");
                    } catch (e) {
                        console.error("Failed to restart:", e);
                        setIsListening(false);
                        isIntentionallyListening.current = false;
                    }
                } else {
                    setIsListening(false);
                }
            };

            recognition.onresult = (event: any) => {
                let interimTranscript = "";

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const result = event.results[i];
                    const transcriptText = result[0].transcript;

                    if (result.isFinal) {
                        if (onResult) {
                            onResult(transcriptText);
                        }
                    } else {
                        interimTranscript += transcriptText;
                    }
                }
                setTranscript(interimTranscript);
            };

            recognition.onerror = (event: any) => {
                console.error("Speech recognition error", event.error);
                // Don't auto-restart on fatal errors to avoid loops, unless it's just 'no-speech'
                if (event.error !== 'no-speech') {
                    setIsListening(false);
                    isIntentionallyListening.current = false;
                }
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
            isIntentionallyListening.current = true;
            setTranscript("");
            try {
                recognitionRef.current.start();
            } catch (e) {
                console.error("Start error", e);
                isIntentionallyListening.current = false;
            }
        }
    }, [isListening]);

    const stopListening = useCallback(() => {
        isIntentionallyListening.current = false; // Explicit stop
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
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
