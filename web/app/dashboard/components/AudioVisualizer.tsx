'use client';

import { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
    analyser: AnalyserNode | null;
    isRecording: boolean;
    threshold?: number; // 0-255
}

export function AudioVisualizer({ analyser, isRecording, threshold = 0 }: AudioVisualizerProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (!analyser || !canvasRef.current) return;

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

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

            // Draw background
            ctx.fillStyle = '#f3f4f6';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw threshold line
            if (threshold > 0) {
                const y = canvas.height - (threshold / 255) * canvas.height;
                ctx.beginPath();
                ctx.strokeStyle = 'rgba(255, 0, 0, 0.5)';
                ctx.lineWidth = 2;
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
                
                ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
                ctx.font = '10px sans-serif';
                ctx.fillText('Umbral', 5, y - 5);
            }

            // Draw bars
            const barWidth = (canvas.width / bufferLength) * 2.5;
            let barHeight;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                barHeight = (dataArray[i] / 255) * canvas.height;

                // Color based on volume vs threshold
                if (dataArray[i] > threshold) {
                    ctx.fillStyle = `rgb(50, 200, 50)`; // Green if above threshold
                } else {
                    ctx.fillStyle = `rgb(200, 200, 200)`; // Gray if below
                }

                ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

                x += barWidth + 1;
            }
            
            // Draw current level indicator
            ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
            ctx.font = '12px monospace';
            ctx.fillText(`Vol: ${Math.round(average)}`, canvas.width - 60, 20);
        };

        draw();

        return () => {
            cancelAnimationFrame(animationId);
        };
    }, [analyser, threshold]);

    return (
        <canvas 
            ref={canvasRef} 
            width={300} 
            height={60} 
            className="rounded border border-gray-200"
        />
    );
}
