'use client';

import { useChat } from '@ai-sdk/react';
import { DefaultChatTransport } from 'ai';
import { useState } from 'react';
import { Navbar, NavbarBrand, NavbarContent, NavbarItem, Link } from "@heroui/react";

export default function ChatPage() {
  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({
      api: '/api/chat',
    }),
  });
  const [input, setInput] = useState('');

  const isLoading = status === 'submitted';

  const normalizedMessages = Array.isArray(messages) ? messages : [];

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <Navbar isBordered maxWidth="xl" className="bg-white">
        <NavbarBrand>
          <p className="font-bold text-inherit text-2xl">SpeechNotes</p>
        </NavbarBrand>
        <NavbarContent className="hidden sm:flex gap-4" justify="center">
          <NavbarItem>
            <Link color="foreground" href="/dashboard">
              📝 Transcribir
            </Link>
          </NavbarItem>
          <NavbarItem isActive>
            <Link href="/dashboard/chat" aria-current="page">
              💬 Chat con Documentos
            </Link>
          </NavbarItem>
        </NavbarContent>
      </Navbar>
      <div className="max-w-4xl mx-auto w-full p-4 pb-0">
          <p className="text-sm text-gray-500">
            Pregunta sobre tus clases grabadas y transcripciones
          </p>
      </div>

      <div className="flex-1 flex flex-col max-w-4xl mx-auto p-4 w-full overflow-hidden">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          {normalizedMessages.length === 0 && (
            <div className="text-center text-gray-400 mt-8">
              <p className="mb-4">💬 Comienza una conversación</p>
              <div className="text-sm space-y-2">
                <p>Prueba preguntas como:</p>
                <ul className="space-y-1 text-left max-w-md mx-auto">
                  <li>• "¿De qué trata la clase de análisis y diseño?"</li>
                  <li>• "¿Cuándo se grabó la clase sobre patrones de diseño?"</li>
                  <li>• "Resume los puntos principales del documento X"</li>
                </ul>
              </div>
            </div>
          )}
          
          {normalizedMessages.map(message => (
            <div
              key={message.id}
              className={`flex ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              <div
                className={`max-w-[80%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="text-xs font-semibold mb-1 opacity-70">
                  {message.role === 'user' ? '👤 Tú' : '🤖 Asistente'}
                </div>
                <div className="whitespace-pre-wrap">
                  {"text" in message ? (message as any).text : (message as any).content}
                </div>
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-100 rounded-lg px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form
          onSubmit={e => {
            e.preventDefault();
            if (input.trim()) {
              (sendMessage as any)({ role: 'user', content: input });
              setInput('');
            }
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={status !== 'ready'}
            placeholder="Escribe tu pregunta sobre los documentos..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={status !== 'ready' || !input.trim()}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Pensando...' : 'Enviar'}
          </button>
        </form>
      </div>
    </div>
  );
}
