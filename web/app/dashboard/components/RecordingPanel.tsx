'use client';

import { useState } from 'react';
import { Button, Card, CardBody, Modal, ModalBody, ModalContent, ModalFooter, ModalHeader, Slider, useDisclosure } from '@heroui/react';
import { AlertTriangle, Mic, RefreshCw, Settings2, Square } from 'lucide-react';
import { useRecording } from '../providers/RecordingProvider';
import { AudioVisualizer } from './AudioVisualizer';
import { useBackground } from '../../providers';

type Language = 'auto' | 'en' | 'es';

type RecordingButtonProps = Readonly<{
    isRecording: boolean;
    onStart: () => void | Promise<void>;
    onRequestStop: () => void;
}>;

type LanguageToggleProps = Readonly<{
    isLight: boolean;
    isRecording: boolean;
    language: Language;
    setLanguage: (language: Language) => void;
}>;

type SettingsButtonProps = Readonly<{
    isLight: boolean;
    showSettings: boolean;
    onToggle: () => void;
}>;

type SettingsPanelProps = Readonly<{
    gainValue: number;
    setGainValue: (value: number) => void;
    visualThreshold: number;
    setVisualThreshold: (value: number) => void;
    isRecording: boolean;
    diarization: boolean;
    setDiarization: (value: boolean) => void;
    audioDevices: Array<{ deviceId: string; label: string }>;
    selectedDeviceId: string;
    setSelectedDeviceId: (deviceId: string) => void;
    refreshAudioDevices: () => void | Promise<void>;
}>;

type StopConfirmationModalProps = Readonly<{
    isLight: boolean;
    isOpen: boolean;
    duration: number;
    onOpenChange: (isOpen: boolean) => void;
    onConfirm: () => void;
}>;

const LANGUAGE_CYCLE: Language[] = ['auto', 'en', 'es'];
const LANGUAGE_LABELS: Record<Language, string> = {
    auto: 'AUTO',
    en: 'EN',
    es: 'ES',
};
const LANGUAGE_TITLES: Record<Language, string> = {
    auto: 'Auto-detectar idioma',
    en: 'Forzar ingles',
    es: 'Forzar espanol',
};

function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function getLanguageStyle(language: Language, isLight: boolean): string {
    const styles: Record<Language, string> = {
        auto: isLight ? 'bg-slate-50 border-slate-300 text-slate-700' : 'bg-white/10 border-white/30 text-slate-200',
        en: isLight ? 'bg-blue-50 border-blue-300 text-blue-700' : 'bg-blue-500/20 border-blue-500/50 text-blue-300',
        es: isLight ? 'bg-amber-50 border-amber-300 text-amber-700' : 'bg-amber-500/20 border-amber-500/50 text-amber-300',
    };
    return styles[language];
}

function getSettingsButtonClass(showSettings: boolean, isLight: boolean): string {
    if (showSettings) return 'bg-indigo-500/20 text-indigo-400 scale-110';
    return isLight
        ? 'text-slate-600 hover:bg-slate-200/50 hover:text-indigo-600'
        : 'text-theme-primary hover:bg-white/10 hover:text-indigo-400';
}

function getModalClassNames(isLight: boolean) {
    return {
        base: isLight ? 'bg-white/95 border border-slate-200 backdrop-blur-xl shadow-2xl' : 'bg-slate-900/95 border border-white/10 backdrop-blur-xl shadow-2xl',
        header: isLight ? 'border-b border-slate-100' : 'border-b border-white/5',
        footer: isLight ? 'border-t border-slate-100' : 'border-t border-white/5',
        closeButton: 'hover:bg-black/5 dark:hover:bg-white/10 active:bg-black/10 dark:active:bg-white/20',
    };
}

function RecordingButton({ isRecording, onStart, onRequestStop }: RecordingButtonProps) {
    const className = `min-w-14 h-14 font-bold shadow-lg transition-all duration-300 transform hover:scale-110 active:scale-90 ${isRecording
        ? 'bg-gradient-to-br from-rose-500 to-red-700 text-white shadow-red-500/40'
        : 'bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700 text-white hover:shadow-blue-500/50 hover:from-blue-600 hover:to-indigo-800'
        }`;

    return (
        <Button
            onPress={isRecording ? onRequestStop : onStart}
            aria-label={isRecording ? 'Detener grabación' : 'Iniciar grabación'}
            isIconOnly
            size="lg"
            radius="full"
            className={className}
        >
            {isRecording ? <StopIcon /> : <Mic size={24} />}
        </Button>
    );
}

function StopIcon() {
    return (
        <div className="relative flex items-center justify-center">
            <div className="absolute inset-0 bg-white/20 rounded-full animate-ping" />
            <Square size={24} className="relative z-10" />
        </div>
    );
}

function RecordingStatus({ isRecording, duration }: Readonly<{ isRecording: boolean; duration: number }>) {
    return (
        <div className="flex flex-col">
            <span className="text-[10px] font-bold uppercase tracking-widest text-theme-secondary/80">
                {isRecording ? 'Grabando' : 'Listo para grabar'}
            </span>
            <span className="text-xl font-mono font-black bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent drop-shadow-sm">
                {formatDuration(duration)}
            </span>
        </div>
    );
}

function LanguageToggle({ isLight, isRecording, language, setLanguage }: LanguageToggleProps) {
    const handleClick = () => {
        if (isRecording) return;
        const index = LANGUAGE_CYCLE.indexOf(language);
        setLanguage(LANGUAGE_CYCLE[(index + 1) % LANGUAGE_CYCLE.length]);
    };

    return (
        <button type="button"
            onClick={handleClick}
            disabled={isRecording}
            title={isRecording ? 'Deten la grabacion para cambiar idioma' : LANGUAGE_TITLES[language]}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-black uppercase tracking-widest border transition-all duration-200
                ${isRecording ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer hover:scale-105 active:scale-95'}
                ${getLanguageStyle(language, isLight)}`}
        >
            <span>{LANGUAGE_LABELS[language]}</span>
        </button>
    );
}

function SettingsButton({ isLight, showSettings, onToggle }: SettingsButtonProps) {
    return (
        <Button
            onPress={onToggle}
            isIconOnly
            size="md"
            variant="light"
            className={`transition-all duration-300 ${getSettingsButtonClass(showSettings, isLight)}`}
            title="Configuracion de Audio"
        >
            <Settings2 size={20} className={showSettings ? 'animate-spin-slow' : ''} />
            {!showSettings && <div className="absolute top-1 right-1 w-1.5 h-1.5 bg-indigo-500 rounded-full animate-soft-pulse" />}
        </Button>
    );
}

function SettingsPanel(props: SettingsPanelProps) {
    return (
        <Card className="shadow-md border-none glass">
            <CardBody className="p-4">
                <h4 className="text-sm font-black mb-4 uppercase tracking-[0.1em] title-semi-neon">Configuracion de Audio</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <MicDeviceSelect
                        devices={props.audioDevices}
                        selectedDeviceId={props.selectedDeviceId}
                        onChange={props.setSelectedDeviceId}
                        onRefresh={props.refreshAudioDevices}
                        disabled={props.isRecording}
                    />
                    <GainSlider value={props.gainValue} onChange={props.setGainValue} />
                    <VisualThresholdSlider value={props.visualThreshold} onChange={props.setVisualThreshold} />
                    <DiarizationToggle
                        isRecording={props.isRecording}
                        diarization={props.diarization}
                        setDiarization={props.setDiarization}
                    />
                </div>
            </CardBody>
        </Card>
    );
}

function MicDeviceSelect({
    devices,
    selectedDeviceId,
    onChange,
    onRefresh,
    disabled,
}: Readonly<{
    devices: Array<{ deviceId: string; label: string }>;
    selectedDeviceId: string;
    onChange: (deviceId: string) => void;
    onRefresh: () => void | Promise<void>;
    disabled: boolean;
}>) {
    return (
        <div className="space-y-2 md:col-span-2">
            <div className="flex items-center justify-between gap-2">
                <label htmlFor="recording-microphone-device" className="label-technical">Entrada de microfono</label>
                <button type="button"
                    onClick={() => void onRefresh()}
                    disabled={disabled}
                    className="inline-flex items-center gap-1 rounded-lg border border-white/10 px-2 py-1 text-[10px] font-bold text-theme-secondary hover:text-theme-primary disabled:opacity-40"
                >
                    <RefreshCw size={12} />
                    Actualizar
                </button>
            </div>
            <select
                id="recording-microphone-device"
                value={selectedDeviceId}
                onChange={(event) => onChange(event.target.value)}
                disabled={disabled}
                className="w-full rounded-xl border border-white/10 bg-black/10 px-3 py-2 text-xs font-semibold text-theme-primary outline-none transition focus:border-indigo-400 disabled:opacity-50"
            >
                <option value="">Microfono predeterminado del sistema</option>
                {devices.map(device => (
                    <option key={device.deviceId} value={device.deviceId}>
                        {device.label}
                    </option>
                ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">Elige el microfono fisico correcto; evita entradas virtuales o de monitor.</p>
        </div>
    );
}
function GainSlider({ value, onChange }: Readonly<{ value: number; onChange: (value: number) => void }>) {
    return (
        <div className="space-y-2">
            <Slider
                label="Ganancia (Volumen)"
                classNames={{
                    label: 'label-technical',
                    value: 'text-[10px] font-black tabular-nums text-violet-400 text-glow-contrast',
                }}
                size="sm"
                step={0.1}
                minValue={0.5}
                maxValue={10.0}
                value={value}
                onChange={(nextValue) => onChange(nextValue as number)}
                className="max-w-md"
                color="primary"
                formatOptions={{ maximumFractionDigits: 1 }}
                showTooltip={true}
            />
            <p className="text-xs text-gray-500 mt-1">Aumenta si el audio se detecta muy bajo.</p>
        </div>
    );
}

function VisualThresholdSlider({ value, onChange }: Readonly<{ value: number; onChange: (value: number) => void }>) {
    return (
        <div className="space-y-2">
            <Slider
                label="Umbral Visual"
                size="sm"
                step={1}
                minValue={0}
                maxValue={100}
                value={value}
                onChange={(nextValue) => onChange(nextValue as number)}
                className="max-w-md"
                color="danger"
                showTooltip={true}
            />
            <p className="text-xs text-gray-500 mt-1">Nivel minimo para considerar voz (visual).</p>
        </div>
    );
}

function DiarizationToggle({ isRecording, diarization, setDiarization }: Pick<SettingsPanelProps, 'isRecording' | 'diarization' | 'setDiarization'>) {
    return (
        <div className="space-y-2 col-span-1 md:col-span-2">
            <div className="flex items-center justify-between bg-black/5 dark:bg-white/5 p-3 rounded-lg border border-black/10 dark:border-white/10">
                <div>
                    <p className="text-sm font-bold title-semi-neon flex items-center gap-2">
                        Identificar Locutores (Diarizacion){' '}
                        <span className="px-1.5 py-0.5 text-[9px] bg-amber-500/20 text-amber-500 rounded border border-amber-500/30 uppercase tracking-widest font-black">Beta</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">Separa el texto indicando [Locutor 1], [Locutor 2]. Requiere mas recursos del servidor.</p>
                </div>
                <button type="button"
                    onClick={() => setDiarization(!diarization)}
                    disabled={isRecording}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-300 focus:outline-none ${isRecording ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${diarization ? 'bg-indigo-500' : 'bg-gray-400 dark:bg-gray-600'}`}
                >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${diarization ? 'translate-x-6' : 'translate-x-1'}`} />
                </button>
            </div>
        </div>
    );
}

function StopConfirmationModal({ isLight, isOpen, duration, onOpenChange, onConfirm }: StopConfirmationModalProps) {
    return (
        <Modal
            isOpen={isOpen}
            onOpenChange={onOpenChange}
            backdrop="blur"
            classNames={getModalClassNames(isLight)}
        >
            <ModalContent>
                {(onClose) => (
                    <>
                        <ModalHeader className="flex flex-col gap-1">
                            <div className="flex items-center gap-2 text-rose-400">
                                <AlertTriangle size={20} />
                                <span>Finalizar Grabacion?</span>
                            </div>
                        </ModalHeader>
                        <ModalBody>
                            <p className={`${isLight ? 'text-slate-600' : 'text-slate-300'} text-sm`}>
                                Estas seguro de que deseas detener la grabacion actual?
                                La transcripcion se guardara y procesara automaticamente.
                            </p>
                            <div className={`p-3 rounded-xl ${isLight ? 'bg-slate-50 border-slate-200' : 'bg-white/5 border-white/10'} border flex items-center justify-between`}>
                                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Duracion acumulada:</span>
                                <span className="text-lg font-mono font-bold text-indigo-400">{formatDuration(duration)}</span>
                            </div>
                        </ModalBody>
                        <ModalFooter>
                            <Button variant="light" onPress={onClose} className={`font-semibold ${isLight ? 'text-slate-500 hover:text-slate-900' : 'text-slate-300 hover:text-white'} transition-colors`}>
                                Continuar grabacion
                            </Button>
                            <Button
                                className="bg-gradient-to-r from-rose-600 to-red-700 text-white font-bold shadow-lg shadow-rose-500/30"
                                onPress={() => {
                                    onConfirm();
                                    onClose();
                                }}
                            >
                                Si, detener ahora
                            </Button>
                        </ModalFooter>
                    </>
                )}
            </ModalContent>
        </Modal>
    );
}

export function RecordingPanel() {
    const recording = useRecording();
    const { themeType } = useBackground();
    const [showSettings, setShowSettings] = useState(false);
    const [visualThreshold, setVisualThreshold] = useState(20);
    const { isOpen, onOpen, onOpenChange } = useDisclosure();
    const isLight = themeType === 'light';

    return (
        <div className="flex flex-col gap-2">
            <Card className="shadow-lg border-none glass backdrop-blur-xl">
                <CardBody className="px-3 py-2">
                    <div className="flex items-center gap-2">
                        <RecordingButton
                            isRecording={recording.isRecording}
                            onStart={recording.startRecording}
                            onRequestStop={onOpen}
                        />
                        <RecordingStatus isRecording={recording.isRecording} duration={recording.duration} />
                        <div className="flex-1 flex justify-center max-w-xs">
                            <AudioVisualizer
                                analyser={recording.analyser}
                                isRecording={recording.isRecording}
                                threshold={visualThreshold}
                            />
                        </div>
                        <LanguageToggle
                            isLight={isLight}
                            isRecording={recording.isRecording}
                            language={recording.language}
                            setLanguage={recording.setLanguage}
                        />
                        <SettingsButton
                            isLight={isLight}
                            showSettings={showSettings}
                            onToggle={() => setShowSettings((current) => !current)}
                        />
                    </div>
                </CardBody>
            </Card>

            {showSettings && (
                <SettingsPanel
                    gainValue={recording.gainValue}
                    setGainValue={recording.setGainValue}
                    visualThreshold={visualThreshold}
                    setVisualThreshold={setVisualThreshold}
                    isRecording={recording.isRecording}
                    diarization={recording.diarization}
                    setDiarization={recording.setDiarization}
                    audioDevices={recording.audioDevices}
                    selectedDeviceId={recording.selectedDeviceId}
                    setSelectedDeviceId={recording.setSelectedDeviceId}
                    refreshAudioDevices={recording.refreshAudioDevices}
                />
            )}

            <StopConfirmationModal
                isLight={isLight}
                isOpen={isOpen}
                duration={recording.duration}
                onOpenChange={onOpenChange}
                onConfirm={recording.stopRecording}
            />
        </div>
    );
}
