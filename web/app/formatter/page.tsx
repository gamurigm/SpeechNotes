'use client';

import { useState, useEffect } from 'react';

interface FileMetadata {
  fecha?: string;
  palabras?: string;
  temas?: string;
}

interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
  metadata: FileMetadata;
}

interface FormatterProgress {
  job_id: string;
  current: number;
  total: number;
  file_name: string;
  status: 'reading' | 'formatting' | 'saving' | 'completed' | 'error';
  output_path?: string;
  error?: string;
  timestamp: string;
}

export default function FormatterPage() {
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState<FormatterProgress[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [summary, setSummary] = useState<{ successful: number; failed: number } | null>(null);
  const [completedFiles, setCompletedFiles] = useState<number>(0);

  // Load available files on mount
  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      setIsLoading(true);
      // Try with session cookies first (preferred)
      let res = await fetch('http://localhost:8001/api/format/files', {
        credentials: 'include'
      });

      // If session request failed (e.g., not authenticated), fall back to dev API key
      if (!res.ok) {
        console.warn('Session fetch failed, retrying with dev API key', res.status);
        res = await fetch('http://localhost:8001/api/format/files', {
          headers: { 'x-api-key': 'dev-secret-api-key' }
        });
      }

      if (!res.ok) {
        const text = await res.text();
        console.error('Failed to load files:', res.status, text);
        setFiles([]);
        return;
      }

      const data = await res.json();
      if (!Array.isArray(data)) {
        console.error('Invalid response for files (expected array):', data);
        setFiles([]);
        return;
      }

      setFiles(data);
    } catch (error) {
      console.error('Error loading files:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleFile = (path: string) => {
    const newSelected = new Set(selectedFiles);
    if (newSelected.has(path)) {
      newSelected.delete(path);
    } else {
      newSelected.add(path);
    }
    setSelectedFiles(newSelected);
  };

  const selectAll = () => {
    if (selectedFiles.size === files.length) {
      setSelectedFiles(new Set());
    } else {
      setSelectedFiles(new Set(files.map(f => f.path)));
    }
  };

  const startFormatting = async () => {
    if (selectedFiles.size === 0) return;

    setIsRunning(true);
    setProgress([]);
    setSummary(null);
    setCompletedFiles(0);

    try {
      // Start formatting job
      // Try to start job with session cookies first
      let res = await fetch('http://localhost:8001/api/format/start', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ files: Array.from(selectedFiles), output_dir: 'notas' })
      });

      // If session attempt failed, retry with dev API key as fallback
      if (!res.ok) {
        console.warn('Session start failed, retrying with dev API key', res.status);
        res = await fetch('http://localhost:8001/api/format/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'x-api-key': 'dev-secret-api-key' },
          body: JSON.stringify({ files: Array.from(selectedFiles), output_dir: 'notas' })
        });
      }

      if (!res.ok) {
        const text = await res.text();
        console.error('Failed to start formatting job:', res.status, text);
        setIsRunning(false);
        return;
      }

      const body = await res.json();
      const { job_id, ws_url } = body;
      setJobId(job_id);

      // Connect to WebSocket for progress updates
      const websocket = new WebSocket(`ws://localhost:8001/api/format${ws_url}`);
      
      websocket.onopen = () => {
        console.log('WebSocket connected');
      };

      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.status === 'job_completed') {
          setSummary({
            successful: data.successful,
            failed: data.failed
          });
          setIsRunning(false);
          websocket.close();
        } else if (data.error) {
          console.error('Job error:', data.error);
          setIsRunning(false);
          websocket.close();
        } else {
          setProgress(prev => {
            const next = [...prev, data as FormatterProgress];
            const done = next.filter(p => p.status === 'completed' || p.status === 'error').length;
            setCompletedFiles(done);
            return next;
          });
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsRunning(false);
      };

      websocket.onclose = () => {
        console.log('WebSocket closed');
        // isRunning is set to false when we receive job_completed or an error.
      };

      setWs(websocket);

    } catch (error) {
      console.error('Error starting formatting:', error);
      setIsRunning(false);
    }
  };

  const totalFiles = progress.length > 0
    ? progress[progress.length - 1].total
    : selectedFiles.size || files.length || 0;

  const isJobDone = !!summary || (!isRunning && totalFiles > 0 && completedFiles >= totalFiles);

  const formatFileSize = (bytes: number) => {
    return (bytes / 1024).toFixed(1) + ' KB';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'reading': return '📖';
      case 'formatting': return '🤖';
      case 'saving': return '💾';
      case 'completed': return '✅';
      case 'error': return '❌';
      default: return '⏳';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-50 border-green-200';
      case 'error': return 'bg-red-50 border-red-200';
      default: return 'bg-blue-50 border-blue-200';
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto p-8 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando archivos...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">🎯 Formateador con Minimax M2</h1>
        <p className="text-gray-600">
          Selecciona archivos de transcripción para formatearlos profesionalmente usando IA
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Selection Panel */}
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Archivos Disponibles</h2>
            <button
              onClick={selectAll}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {selectedFiles.size === files.length ? 'Deseleccionar todos' : 'Seleccionar todos'}
            </button>
          </div>

          {files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>No hay archivos disponibles para formatear</p>
              <p className="text-sm mt-2">Los archivos deben estar en el directorio `notas/`</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {files.map(file => (
                <label
                  key={file.path}
                  className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedFiles.has(file.path)
                      ? 'bg-blue-50 border-blue-300'
                      : 'hover:bg-gray-50 border-gray-200'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedFiles.has(file.path)}
                    onChange={() => toggleFile(file.path)}
                    className="mt-1 mr-3 h-4 w-4"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm truncate">{file.name}</div>
                    <div className="text-xs text-gray-600 mt-1">
                      {file.metadata.fecha && (
                        <span className="mr-3">📅 {file.metadata.fecha}</span>
                      )}
                      {file.metadata.palabras && (
                        <span className="mr-3">📝 {file.metadata.palabras} palabras</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-400 mt-1">
                      {formatFileSize(file.size)}
                    </div>
                  </div>
                </label>
              ))}
            </div>
          )}

          <button
            onClick={startFormatting}
            disabled={selectedFiles.size === 0 || isRunning}
            className={`mt-6 w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              selectedFiles.size === 0 || isRunning
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isRunning
              ? '⏳ Procesando...'
              : `✨ Formatear ${selectedFiles.size} archivo${selectedFiles.size !== 1 ? 's' : ''}`
            }
          </button>
        </div>

        {/* Progress Panel */}
        <div className="border rounded-lg p-6 bg-white shadow-sm">
          <h2 className="text-xl font-semibold mb-4">Progreso en Tiempo Real</h2>

          {/* Global job status */}
          {(isRunning || summary || isJobDone) && (
            <div className="mb-4">
              {totalFiles > 0 && (
                <div className="mb-2 flex items-center justify-between text-xs text-gray-600">
                  <span>
                    Progreso total: {completedFiles}/{totalFiles} archivo{totalFiles !== 1 ? 's' : ''}
                  </span>
                  {isRunning && !summary && !isJobDone && (
                    <span className="text-[11px] text-gray-500">Procesando... esto puede tardar unos segundos</span>
                  )}
                  {!isRunning && isJobDone && (
                    <span className="text-[11px] text-green-600">Proceso finalizado</span>
                  )}
                </div>
              )}
              {totalFiles > 0 && (
                <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-blue-600 h-2 transition-all"
                    style={{ width: `${totalFiles ? (Math.min(completedFiles, totalFiles) / totalFiles) * 100 : 0}%` }}
                  />
                </div>
              )}
            </div>
          )}

          {jobId && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <div className="text-xs text-gray-600">Job ID</div>
              <code className="text-xs font-mono">{jobId}</code>
            </div>
          )}

          {summary && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="font-semibold text-green-800 mb-2">🎉 Formateo Completado</div>
              <div className="text-sm text-green-700">
                ✅ Exitosos: {summary.successful} | ❌ Fallidos: {summary.failed}
              </div>
              <button
                className="mt-3 inline-flex items-center px-3 py-1.5 text-xs font-medium text-green-800 bg-green-100 rounded hover:bg-green-200"
                onClick={() => {
                  setProgress([]);
                  setSummary(null);
                  setJobId(null);
                  setCompletedFiles(0);
                  setSelectedFiles(new Set());
                }}
              >
                🔁 Nuevo trabajo
              </button>
            </div>
          )}

          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {progress.length === 0 && !isRunning && (
              <div className="text-center py-12 text-gray-400">
                <p>El progreso aparecerá aquí cuando inicies el formateo</p>
              </div>
            )}

            {progress.map((p, idx) => (
              <div
                key={idx}
                className={`p-4 border rounded-lg transition-all ${getStatusColor(p.status)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm truncate flex-1">{p.file_name}</span>
                  <span className="text-xs text-gray-600 ml-2">
                    {p.current}/{p.total}
                  </span>
                </div>
                
                <div className="flex items-center text-sm">
                  <span className="mr-2">{getStatusIcon(p.status)}</span>
                  <span>
                    {p.status === 'reading' && 'Leyendo archivo...'}
                    {p.status === 'formatting' && 'Formateando con Minimax M2...'}
                    {p.status === 'saving' && 'Guardando archivo...'}
                    {p.status === 'completed' && 'Completado exitosamente'}
                    {p.status === 'error' && `Error: ${p.error}`}
                  </span>
                </div>

                {p.output_path && (
                  <div className="mt-2 text-xs text-gray-600 truncate">
                    📁 {p.output_path}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
