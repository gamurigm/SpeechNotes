'use client';

import { signIn } from 'next-auth/react';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

type AuthMode = 'login' | 'register';

type ApiError = {
    error?: string;
};

const USERNAME_PATTERN = /^[a-z0-9._-]{3,32}$/;
const NAME_PATTERN = /^[\p{L}\p{M}][\p{L}\p{M} .'-]{1,79}$/u;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MIN_PASSWORD_LENGTH = 8;
const MAX_PASSWORD_LENGTH = 128;
const MAX_EMAIL_LENGTH = 254;

export default function LoginPage() {
    const router = useRouter();
    const [mode, setMode] = useState<AuthMode>('login');
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const normalizedName = fullName.trim().replace(/\s+/g, ' ');
    const normalizedEmail = email.trim().toLowerCase();
    const normalizedUsername = username.trim().toLowerCase();

    const validateForm = () => {
        if (mode === 'register' && !NAME_PATTERN.test(normalizedName)) {
            setError('Ingresa un nombre completo valido de 2 a 80 caracteres.');
            return false;
        }

        if (
            mode === 'register' &&
            (normalizedEmail.length > MAX_EMAIL_LENGTH || !EMAIL_PATTERN.test(normalizedEmail))
        ) {
            setError('Ingresa un correo electronico valido.');
            return false;
        }

        if (!normalizedUsername) {
            setError('Ingresa un usuario.');
            return false;
        }

        if (mode === 'register' && !USERNAME_PATTERN.test(normalizedUsername)) {
            setError('El usuario solo puede usar letras, numeros, punto, guion o guion bajo.');
            return false;
        }

        if (!password) {
            setError('Ingresa una contrasena.');
            return false;
        }

        if (password.length > MAX_PASSWORD_LENGTH) {
            setError('La contrasena no puede superar 128 caracteres.');
            return false;
        }

        if (
            mode === 'register' &&
            (password.length < MIN_PASSWORD_LENGTH || !/[A-Za-z]/.test(password) || !/\d/.test(password))
        ) {
            setError('La contrasena debe tener al menos 8 caracteres, letras y numeros.');
            return false;
        }

        if (mode === 'register' && password.toLowerCase() === normalizedUsername) {
            setError('La contrasena no puede ser igual al usuario.');
            return false;
        }

        if (mode === 'register' && password !== confirmPassword) {
            setError('Las contrasenas no coinciden.');
            return false;
        }

        return true;
    };

    const credentialsSignIn = async () => {
        const result = await signIn('credentials', {
            redirect: false,
            username: normalizedUsername,
            password,
        });

        if (result?.error) {
            setError('Usuario o contrasena incorrectos.');
            return false;
        }

        router.push('/');
        router.refresh();
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            if (!validateForm()) {
                return;
            }

            if (mode === 'register') {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        name: normalizedName,
                        email: normalizedEmail,
                        username: normalizedUsername,
                        password,
                    }),
                });

                if (!response.ok) {
                    const body = (await response.json().catch(() => ({}))) as ApiError;
                    setError(body.error || 'No se pudo crear el usuario.');
                    return;
                }
            }

            await credentialsSignIn();
        } catch {
            setError('No se pudo completar la solicitud.');
        } finally {
            setLoading(false);
        }
    };

    const selectMode = (nextMode: AuthMode) => {
        setMode(nextMode);
        setError('');
        setConfirmPassword('');
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100 px-4 py-8">
            <div className="w-full max-w-md space-y-6 rounded-lg bg-white p-8 shadow-2xl backdrop-blur-sm sm:p-10">
                <div className="text-center">
                    <p className="text-sm font-semibold text-indigo-700">SpeechNotes</p>
                    <h1 className="mt-2 text-3xl font-bold text-gray-900">
                        {mode === 'login' ? 'Iniciar sesion' : 'Registrar usuario'}
                    </h1>
                    <p className="mt-2 text-sm text-gray-600">
                        {mode === 'login'
                            ? 'Ingresa con tu usuario y contrasena'
                            : 'Crea tus credenciales de acceso'}
                    </p>
                </div>

                <div className="grid grid-cols-2 rounded-lg bg-gray-100 p-1 text-sm font-semibold">
                    <button
                        type="button"
                        aria-pressed={mode === 'login'}
                        onClick={() => selectMode('login')}
                        className={`rounded-md px-3 py-2 transition ${
                            mode === 'login'
                                ? 'bg-white text-indigo-700 shadow-sm'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Iniciar sesion
                    </button>
                    <button
                        type="button"
                        aria-pressed={mode === 'register'}
                        onClick={() => selectMode('register')}
                        className={`rounded-md px-3 py-2 transition ${
                            mode === 'register'
                                ? 'bg-white text-indigo-700 shadow-sm'
                                : 'text-gray-600 hover:text-gray-900'
                        }`}
                    >
                        Registrar usuario
                    </button>
                </div>

                <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
                    <div className="space-y-4">
                        {mode === 'register' && (
                            <>
                                <div>
                                    <label
                                        htmlFor="full-name"
                                        className="mb-1.5 block text-sm font-medium text-gray-700"
                                    >
                                        Nombre completo
                                    </label>
                                    <input
                                        id="full-name"
                                        name="name"
                                        type="text"
                                        autoComplete="name"
                                        required
                                        minLength={2}
                                        maxLength={80}
                                        className="relative block w-full rounded-lg border-0 px-4 py-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                        placeholder="Nombre y apellido"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                    />
                                </div>
                                <div>
                                    <label
                                        htmlFor="register-email"
                                        className="mb-1.5 block text-sm font-medium text-gray-700"
                                    >
                                        Correo electronico
                                    </label>
                                    <input
                                        id="register-email"
                                        name="email"
                                        type="email"
                                        inputMode="email"
                                        autoComplete="email"
                                        autoCapitalize="none"
                                        spellCheck={false}
                                        required
                                        maxLength={MAX_EMAIL_LENGTH}
                                        className="relative block w-full rounded-lg border-0 px-4 py-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                        placeholder="nombre@correo.com"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                    />
                                </div>
                            </>
                        )}
                        <div>
                            <label htmlFor="username" className="mb-1.5 block text-sm font-medium text-gray-700">
                                {mode === 'login' ? 'Usuario o correo' : 'Usuario'}
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                autoComplete="username"
                                autoCapitalize="none"
                                spellCheck={false}
                                required
                                maxLength={mode === 'register' ? 32 : 254}
                                pattern={mode === 'register' ? '[a-z0-9._-]{3,32}' : undefined}
                                className="relative block w-full rounded-lg border-0 px-4 py-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                placeholder={mode === 'login' ? 'Usuario o correo' : 'Usuario'}
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="mb-1.5 block text-sm font-medium text-gray-700">
                                Contrasena
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                                required
                                minLength={mode === 'register' ? MIN_PASSWORD_LENGTH : undefined}
                                maxLength={MAX_PASSWORD_LENGTH}
                                className="relative block w-full rounded-lg border-0 px-4 py-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                placeholder="Contrasena"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                aria-describedby={mode === 'register' ? 'password-rules' : undefined}
                            />
                            {mode === 'register' && (
                                <p id="password-rules" className="mt-1.5 text-xs text-gray-500">
                                    Minimo 8 caracteres, con letras y numeros.
                                </p>
                            )}
                        </div>
                        {mode === 'register' && (
                            <div>
                                <label
                                    htmlFor="confirm-password"
                                    className="mb-1.5 block text-sm font-medium text-gray-700"
                                >
                                    Confirmar contrasena
                                </label>
                                <input
                                    id="confirm-password"
                                    name="confirmPassword"
                                    type="password"
                                    autoComplete="new-password"
                                    required
                                    minLength={MIN_PASSWORD_LENGTH}
                                    maxLength={MAX_PASSWORD_LENGTH}
                                    className="relative block w-full rounded-lg border-0 px-4 py-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                                    placeholder="Repite la contrasena"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                />
                            </div>
                        )}
                    </div>

                    {error && (
                        <div
                            role="alert"
                            aria-live="polite"
                            className="rounded-md bg-red-50 p-3 text-center text-sm text-red-800"
                        >
                            {error}
                        </div>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative flex w-full justify-center rounded-lg bg-indigo-600 px-4 py-3 text-sm font-semibold text-white transition-all hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                            {loading
                                ? mode === 'login'
                                    ? 'Ingresando...'
                                    : 'Creando usuario...'
                                : mode === 'login'
                                  ? 'Iniciar sesion'
                                  : 'Registrar usuario'}
                        </button>
                    </div>

                    {mode === 'login' && (
                        <>
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-gray-300" />
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="bg-white px-2 text-gray-500">O continuar con</span>
                                </div>
                            </div>

                            <div>
                                <button
                                    type="button"
                                    onClick={() => signIn('google', { callbackUrl: '/' })}
                                    className="group relative flex w-full items-center justify-center gap-3 rounded-lg bg-white px-4 py-3 text-sm font-semibold text-gray-700 ring-1 ring-inset ring-gray-300 transition-all hover:bg-gray-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-600"
                                >
                                    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
                                        <path
                                            d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                            fill="#4285F4"
                                        />
                                        <path
                                            d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                            fill="#34A853"
                                        />
                                        <path
                                            d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                            fill="#FBBC05"
                                        />
                                        <path
                                            d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                            fill="#EA4335"
                                        />
                                    </svg>
                                    Iniciar con Google
                                </button>
                            </div>
                        </>
                    )}

                    <div className="text-center text-sm text-gray-600">
                        {mode === 'login' ? 'No tienes usuario?' : 'Ya tienes usuario?'}{' '}
                        <button
                            type="button"
                            onClick={() => selectMode(mode === 'login' ? 'register' : 'login')}
                            className="font-semibold text-indigo-700 hover:text-indigo-600 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            {mode === 'login' ? 'Registrar usuario' : 'Iniciar sesion'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
