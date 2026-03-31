"use client";

import { useState, useEffect, useCallback, useRef } from "react";

/**
 * Split text into chunks at sentence boundaries to avoid Chrome's ~15 second
 * utterance cutoff on mobile. Each chunk stays under maxLen characters.
 */
function splitIntoChunks(text: string, maxLen = 180): string[] {
    if (text.length <= maxLen) return [text];

    const chunks: string[] = [];
    let remaining = text;

    while (remaining.length > 0) {
        if (remaining.length <= maxLen) {
            chunks.push(remaining);
            break;
        }

        // Find the last sentence boundary within maxLen
        const slice = remaining.slice(0, maxLen);
        let splitAt = -1;

        // Try splitting at sentence-ending punctuation
        for (const sep of ['. ', '! ', '? ', '.\n', '!\n', '?\n']) {
            const idx = slice.lastIndexOf(sep);
            if (idx > splitAt) splitAt = idx + sep.length;
        }

        // Fallback: split at last comma or semicolon
        if (splitAt <= 0) {
            for (const sep of [', ', '; ']) {
                const idx = slice.lastIndexOf(sep);
                if (idx > splitAt) splitAt = idx + sep.length;
            }
        }

        // Last resort: split at last space
        if (splitAt <= 0) {
            splitAt = slice.lastIndexOf(' ');
        }

        // Absolute last resort: hard cut
        if (splitAt <= 0) {
            splitAt = maxLen;
        }

        chunks.push(remaining.slice(0, splitAt).trim());
        remaining = remaining.slice(splitAt).trim();
    }

    return chunks.filter(c => c.length > 0);
}

export function useTextToSpeech() {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
    const isCancellingRef = useRef(false); // Guard against cancel triggering onerror
    const chunksQueueRef = useRef<string[]>([]);
    const currentOnEndRef = useRef<(() => void) | null>(null);
    const currentLangRef = useRef("es-US");

    useEffect(() => {
        if (typeof window === "undefined" || !window.speechSynthesis) return;

        const loadVoices = () => {
            const availableVoices = window.speechSynthesis.getVoices();
            setVoices(availableVoices);
        };

        loadVoices();

        if (window.speechSynthesis.onvoiceschanged !== undefined) {
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }
    }, []);

    useEffect(() => {
        if (typeof window === "undefined" || !window.speechSynthesis) return;

        const interval = setInterval(() => {
            if (!isCancellingRef.current) {
                setIsSpeaking(window.speechSynthesis.speaking);
            }
        }, 100);
        return () => clearInterval(interval);
    }, []);

    const findBestVoice = useCallback((lang: string): SpeechSynthesisVoice | null => {
        const langPrefix = lang.split('-')[0];

        // Priority 1: Google voice for this language (best quality on Chrome)
        const googleVoice = voices.find(v =>
            (v.lang === lang || v.lang.startsWith(langPrefix)) && v.name.includes("Google")
        );
        if (googleVoice) return googleVoice;

        // Priority 2: Any voice matching the exact lang
        const exactMatch = voices.find(v => v.lang === lang);
        if (exactMatch) return exactMatch;

        // Priority 3: Any voice matching the language prefix (e.g., es for es-ES)
        const prefixMatch = voices.find(v => v.lang.startsWith(langPrefix));
        if (prefixMatch) return prefixMatch;

        return null;
    }, [voices]);

    const speakNextChunk = useCallback(() => {
        if (chunksQueueRef.current.length === 0) {
            setIsSpeaking(false);
            if (currentOnEndRef.current) {
                currentOnEndRef.current();
                currentOnEndRef.current = null;
            }
            return;
        }

        const text = chunksQueueRef.current.shift()!;
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = currentLangRef.current;
        utterance.rate = 1.1;

        const voice = findBestVoice(currentLangRef.current);
        if (voice) utterance.voice = voice;

        utterance.onend = () => {
            // Speak next chunk in queue
            speakNextChunk();
        };

        utterance.onerror = (e) => {
            // Ignore errors from intentional cancellation
            if (isCancellingRef.current) return;

            console.error("TTS utterance error:", e);
            chunksQueueRef.current = []; // Clear remaining chunks
            setIsSpeaking(false);
            if (currentOnEndRef.current) {
                currentOnEndRef.current();
                currentOnEndRef.current = null;
            }
        };

        window.speechSynthesis.speak(utterance);
    }, [findBestVoice]);

    const speak = useCallback((text: string, language: string = "es-US", onEnd?: () => void) => {
        if (!text || typeof window === "undefined" || !window.speechSynthesis) return;

        // Cancel any ongoing speech with guard
        isCancellingRef.current = true;
        window.speechSynthesis.cancel();
        // Small delay to let cancel propagate before starting new speech
        setTimeout(() => {
            isCancellingRef.current = false;

            currentLangRef.current = language;
            currentOnEndRef.current = onEnd || null;
            chunksQueueRef.current = splitIntoChunks(text);

            setIsSpeaking(true);
            speakNextChunk();
        }, 50);
    }, [speakNextChunk]);

    const stop = useCallback(() => {
        isCancellingRef.current = true;
        chunksQueueRef.current = [];
        currentOnEndRef.current = null;
        if (typeof window !== "undefined" && window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }
        setTimeout(() => {
            isCancellingRef.current = false;
            setIsSpeaking(false);
        }, 50);
    }, []);

    return {
        isSpeaking,
        speak,
        stop,
        hasSupport: typeof window !== "undefined" && !!window.speechSynthesis
    };
}
