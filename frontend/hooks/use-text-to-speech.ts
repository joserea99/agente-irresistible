"use client";

import { useState, useEffect, useCallback } from "react";

export function useTextToSpeech() {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);

    useEffect(() => {
        const loadVoices = () => {
            const availableVoices = window.speechSynthesis.getVoices();
            setVoices(availableVoices);
        };

        loadVoices();

        // Voices load asynchronously in Chrome
        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }, []);

    useEffect(() => {
        // Poll for speaking state since there's no native 'onstart' global listener effectively
        const interval = setInterval(() => {
            setIsSpeaking(window.speechSynthesis.speaking);
        }, 100);
        return () => clearInterval(interval);
    }, []);

    const speak = useCallback((text: string, language: string = "es-ES") => {
        if (!text) return;

        // Stop invalid utterance
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        utterance.rate = 1.1; // Slightly faster for natural feel

        // Try to find a good voice
        const voice = voices.find(v =>
            (v.lang === language || v.lang.startsWith(language.split('-')[0]))
            && !v.name.includes("Google") // Sometimes specific ones are better, but let's default to standard logic
        );

        // Prioritize "Google" voices if available (usually better quality on Chrome)
        const googleVoice = voices.find(v => v.lang.includes(language.split('-')[0]) && v.name.includes("Google"));

        if (googleVoice) {
            utterance.voice = googleVoice;
        } else if (voice) {
            utterance.voice = voice;
        }

        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        window.speechSynthesis.speak(utterance);
        setIsSpeaking(true);
    }, [voices]);

    const stop = useCallback(() => {
        window.speechSynthesis.cancel();
        setIsSpeaking(false);
    }, []);

    return {
        isSpeaking,
        speak,
        stop,
        hasSupport: typeof window !== "undefined" && !!window.speechSynthesis
    };
}
