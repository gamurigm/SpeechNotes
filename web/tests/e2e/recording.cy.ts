describe('Flujos críticos de SpeechNotes', () => {
    function installAudioSimulation(win: Cypress.AUTWindow) {
        class FakeAudioNode {
            connect<T>(destination: T): T { return destination; }
            disconnect() {}
        }

        class FakeAnalyser extends FakeAudioNode {
            fftSize = 256;
            frequencyBinCount = 128;

            getByteFrequencyData(data: Uint8Array) {
                data.fill(8);
            }
        }

        class FakeAudioContext {
            destination = new FakeAudioNode();
            sampleRate = 16_000;
            state = 'running';

            createAnalyser() { return new FakeAnalyser(); }
            createGain() { return Object.assign(new FakeAudioNode(), { gain: { value: 1 } }); }
            createMediaStreamSource() { return new FakeAudioNode(); }
            createScriptProcessor() {
                return Object.assign(new FakeAudioNode(), { onaudioprocess: null });
            }
            close() { return Promise.resolve(); }
            resume() { return Promise.resolve(); }
        }

        Object.defineProperty(win, 'AudioContext', {
            configurable: true,
            value: FakeAudioContext,
        });
        Object.defineProperty(win.navigator, 'mediaDevices', {
            configurable: true,
            value: {
                addEventListener() {},
                enumerateDevices: () => Promise.resolve([{
                    deviceId: 'cypress-microphone',
                    kind: 'audioinput',
                    label: 'Micrófono simulado por Cypress',
                }]),
                getUserMedia: () => Promise.resolve({
                    getTracks: () => [{ stop() {} }],
                }),
                removeEventListener() {},
            },
        });
    }

    function loginAsDemo() {
        cy.request('/api/auth/csrf').then(({ body }) => cy.request({
            method: 'POST',
            url: '/api/auth/callback/credentials',
            form: true,
            body: {
                callbackUrl: '/dashboard',
                csrfToken: body.csrfToken,
                email: 'demo@speechnotes.app',
                json: 'true',
                password: 'demo123',
            },
        }));
    }

    beforeEach(() => {
        loginAsDemo();
        cy.visit('/dashboard', { onBeforeLoad: installAudioSimulation });
        cy.contains('Transcripción en Vivo', { timeout: 30_000 }).should('be.visible');
    });

    it('carga la vista de una transcripción almacenada', () => {
        cy.contains('Clase de calidad simulada', { timeout: 30_000 }).should('be.visible');
        cy.contains('Transcripción histórica cargada por Cypress.', { timeout: 30_000 }).should('be.visible');
    });

    it('simula una grabación y muestra la transcripción en vivo', () => {
        cy.get('[aria-label="Iniciar grabación"]').click();

        cy.contains('Grabando', { timeout: 10_000 }).should('be.visible');
        cy.contains('Texto de prueba recibido desde el backend simulado.', { timeout: 10_000 })
            .should('be.visible');
        cy.screenshot('C2-grabacion-y-transcripcion-en-vivo');

        cy.get('[aria-label="Detener grabación"]').click();
        cy.contains('Si, detener ahora').click();
        cy.contains('Listo para grabar').should('be.visible');
    });
});
