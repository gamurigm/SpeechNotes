'use client';

import { useEffect, useRef } from 'react';
import { useBackground } from '../../providers';

interface AudioVisualizerProps {
    analyser: AnalyserNode | null;
    isRecording: boolean;
    threshold?: number; // 0-255
}

export function AudioVisualizer({ analyser, isRecording, threshold = 0 }: AudioVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const { themeType } = useBackground();
    const isLight = themeType === 'light';

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // If not recording or no analyser, show idle state
        if (!analyser || !isRecording) {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw subtle background based on theme
            if (isLight) {
                ctx.fillStyle = 'rgba(241, 245, 249, 0.6)'; // slate-100 with opacity
            } else {
                ctx.fillStyle = 'rgba(30, 41, 59, 0.4)'; // slate-800 with opacity
            }
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw idle bars (low height, gray)
            const barWidth = 4;
            const gap = 2;
            const barCount = Math.floor(canvas.width / (barWidth + gap));

            for (let i = 0; i < barCount; i++) {
                const barHeight = 4 + Math.sin(i * 0.3) * 3; // Subtle wave pattern
                const x = i * (barWidth + gap);

                if (isLight) {
                    ctx.fillStyle = 'rgba(148, 163, 184, 0.4)'; // slate-400
                } else {
                    ctx.fillStyle = 'rgba(100, 116, 139, 0.4)'; // slate-500
                }
                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
            }
            return;
        }

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        let animationId: number;

        const draw = () => {
            animationId = requestAnimationFrame(draw);

            analyser.getByteFrequencyData(dataArray);

            // Calculate average volume
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
            }
            const average = sum / bufferLength;

            // Clear canvas
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            // Draw background based on theme
            if (isLight) {
                ctx.fillStyle = 'rgba(241, 245, 249, 0.4)'; // Very subtle bg for light
            } else {
                ctx.fillStyle = 'rgba(15, 23, 42, 0.3)'; // Very subtle bg for dark
            }
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw threshold line if set
            if (threshold > 0) {
                const y = canvas.height - (threshold / 255) * canvas.height;
                ctx.beginPath();
                ctx.strokeStyle = 'rgba(239, 68, 68, 0.5)'; // rose-500
                ctx.lineWidth = 2;
                ctx.setLineDash([4, 4]);
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
                ctx.setLineDash([]);
            }

            // Draw bars with gradient
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * canvas.height;

                // Color based on volume with nice gradient
                if (dataArray[i] > threshold) {
                    // Active: Green gradient
                    const gradient = ctx.createLinearGradient(x, canvas.height, x, canvas.height - barHeight);
                    gradient.addColorStop(0, 'rgb(34, 197, 94)'); // green-500
                    gradient.addColorStop(1, 'rgb(16, 185, 129)'); // emerald-500
                    ctx.fillStyle = gradient;
                } else {
                    // Below threshold: Subtle gray
                    if (isLight) {
                        ctx.fillStyle = 'rgba(203, 213, 225, 0.6)'; // slate-300
                    } else {
                        ctx.fillStyle = 'rgba(71, 85, 105, 0.6)'; // slate-600
                    }
                }

                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

                x += barWidth + 1;
            }

            // Draw current level indicator with better styling
            ctx.font = 'bold 11px Inter, system-ui, sans-serif';
            if (isLight) {
                ctx.fillStyle = 'rgba(30, 41, 59, 0.8)'; // slate-800
            } else {
                ctx.fillStyle = 'rgba(226, 232, 240, 0.9)'; // slate-200
            }
            ctx.fillText(`Vol: ${Math.round(average)}`, canvas.width - 55, 16);
        };

        draw();

        return () => {
            cancelAnimationFrame(animationId);
        };
    }, [analyser, isRecording, threshold, isLight]);

    return (
        <canvas
            ref={canvasRef}
            width={300}
            height={60}
            className={`rounded-xl ${isLight ? 'border border-slate-200/50' : 'border border-white/10'} backdrop-blur-sm`}
        />
    );
}
