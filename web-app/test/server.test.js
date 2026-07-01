const assert = require('node:assert/strict');
const http = require('node:http');
const { after, before, describe, it } = require('node:test');

const { app, errorHandler, publicDirectory, startServer } = require('../server');

describe('Express web app', () => {
    let server;
    let baseUrl;

    before(async () => {
        await new Promise((resolve) => {
            server = app.listen(0, () => {
                const { port } = server.address();
                baseUrl = `http://127.0.0.1:${port}`;
                resolve();
            });
        });
    });

    after(async () => {
        await new Promise((resolve, reject) => {
            server.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });

    function request(path) {
        return new Promise((resolve, reject) => {
            http.get(`${baseUrl}${path}`, (response) => {
                let body = '';
                response.setEncoding('utf8');
                response.on('data', (chunk) => {
                    body += chunk;
                });
                response.on('end', () => {
                    resolve({ body, response });
                });
            }).on('error', reject);
        });
    }

    it('serves the static game interface from the public directory', async () => {
        const { body, response } = await request('/');

        assert.equal(response.statusCode, 200);
        assert.match(publicDirectory, /public$/);
        assert.match(body, /Real-Time Sign Language Game/);
        assert.match(body, /Start Receiving/);
    });

    it('reports health for CI and local smoke checks', async () => {
        const { body, response } = await request('/health');

        assert.equal(response.statusCode, 200);
        assert.equal(response.headers['content-type'].includes('application/json'), true);
        assert.deepEqual(JSON.parse(body), { status: 'ok' });
    });
});

describe('server helpers', () => {
    it('maps upstream response errors to a 403 response', () => {
        const sent = {};
        const res = {
            status(code) {
                sent.statusCode = code;
                return this;
            },
            send(body) {
                sent.body = body;
            },
        };

        errorHandler({ response: {}, message: 'Forbidden' }, {}, res, () => {});

        assert.equal(sent.statusCode, 403);
        assert.deepEqual(sent.body, { title: 'Server responded with an error', message: 'Forbidden' });
    });

    it('maps missing upstream responses to a 503 response', () => {
        const sent = {};
        const res = {
            status(code) {
                sent.statusCode = code;
                return this;
            },
            send(body) {
                sent.body = body;
            },
        };

        errorHandler({ request: {}, message: 'No response' }, {}, res, () => {});

        assert.equal(sent.statusCode, 503);
        assert.deepEqual(sent.body, { title: 'Unable to communicate with server', message: 'No response' });
    });

    it('maps unexpected errors to a 500 response', () => {
        const sent = {};
        const res = {
            status(code) {
                sent.statusCode = code;
                return this;
            },
            send(body) {
                sent.body = body;
            },
        };

        errorHandler({ message: 'Unexpected' }, {}, res, () => {});

        assert.equal(sent.statusCode, 500);
        assert.deepEqual(sent.body, { title: 'An unexpected error occurred', message: 'Unexpected' });
    });

    it('starts and stops the HTTP server on a requested port', async () => {
        const started = await new Promise((resolve) => {
            const server = startServer(0);
            server.on('listening', () => resolve(server));
        });

        assert.equal(typeof started.address().port, 'number');

        await new Promise((resolve, reject) => {
            started.close((error) => {
                if (error) {
                    reject(error);
                    return;
                }
                resolve();
            });
        });
    });
});
