const assert = require('node:assert/strict');
const { describe, it } = require('node:test');

const game = require('../public/js/index');

function createElement(id) {
    return {
        className: '',
        id,
        innerHTML: '',
        innerText: '',
        style: {},
        attributes: {},
        setAttribute(name, value) {
            this.attributes[name] = value;
        },
    };
}

function createDocument(ids = ['subscribe-button', 'wait-message', 'response-text', 'output']) {
    const elements = Object.fromEntries(ids.map((id) => [id, createElement(id)]));
    return {
        elements,
        getElementById(id) {
            return elements[id] || null;
        },
    };
}

function createAjaxRecorder(successPayload = 'ok') {
    const calls = [];
    return {
        ajax(options) {
            calls.push(options);
            options.success(successPayload);
        },
        calls,
    };
}

describe('browser game helpers', () => {
    it('builds backend URLs for the Flask bridge', () => {
        assert.equal(game.backendUrl('/cloud-start'), 'http://127.0.0.1:5000/cloud-start');
    });

    it('exports the browser handlers used by index.html', () => {
        assert.equal(typeof globalThis.subscribeStart, 'function');
        assert.equal(typeof globalThis.cloudStart, 'function');
        assert.equal(typeof globalThis.mainLetterFind, 'function');
    });

    it('runs the local Ajax helper success callback for 2xx responses', () => {
        const originalRequest = globalThis.XMLHttpRequest;
        const calls = [];

        class FakeRequest {
            open(method, url, async) {
                calls.push({ method, url, async });
            }

            send() {
                this.readyState = 4;
                this.status = 200;
                this.responseText = 'ready';
                this.onreadystatechange();
            }
        }

        globalThis.XMLHttpRequest = FakeRequest;
        try {
            let payload;
            game.localAjax({
                type: 'GET',
                url: '/ok',
                success(responseText) {
                    payload = responseText;
                },
                error() {
                    throw new Error('Expected success callback');
                },
            });

            assert.deepEqual(calls, [{ method: 'GET', url: '/ok', async: true }]);
            assert.equal(payload, 'ready');
        } finally {
            globalThis.XMLHttpRequest = originalRequest;
        }
    });

    it('runs the local Ajax helper error callback for non-2xx responses', () => {
        const originalRequest = globalThis.XMLHttpRequest;

        class FakeRequest {
            open() {}

            send() {
                this.readyState = 4;
                this.status = 503;
                this.onreadystatechange();
            }
        }

        globalThis.XMLHttpRequest = FakeRequest;
        try {
            let status;
            game.localAjax({
                url: '/down',
                success() {
                    throw new Error('Expected error callback');
                },
                error(request) {
                    status = request.status;
                },
            });

            assert.equal(status, 503);
        } finally {
            globalThis.XMLHttpRequest = originalRequest;
        }
    });

    it('marks the subscription button disabled and schedules the ready message', () => {
        const document = createDocument();
        const ajax = createAjaxRecorder();
        const delays = [];

        game.subscribeStart({
            ajax: ajax.ajax,
            document,
            setTimeout(callback, delay) {
                delays.push(delay);
                callback();
            },
        });

        assert.equal(ajax.calls[0].type, 'GET');
        assert.equal(ajax.calls[0].url, game.backendUrl(game.SUBSCRIBE_START_PATH));
        assert.equal(document.elements['subscribe-button'].className, 'btn btn-primary button-position disabled');
        assert.equal(document.elements['subscribe-button'].attributes['aria-disabled'], 'true');
        assert.deepEqual(delays, [game.SUBSCRIBE_READY_DELAY_MS]);
        assert.equal(document.elements['wait-message'].innerText, 'Ready To Play');
        assert.equal(document.elements['wait-message'].style.color, 'green');
    });

    it('shows a subscription error when the backend request fails', () => {
        const document = createDocument();

        game.subscribeStart({
            ajax(options) {
                options.error();
            },
            document,
            setTimeout() {},
        });

        assert.equal(document.elements['wait-message'].innerText, 'Error Starting Subscription Service');
        assert.equal(document.elements['wait-message'].style.color, 'red');
    });

    it('sets success and failure response states', () => {
        const document = createDocument();

        game.switcher(3, document);
        assert.equal(document.elements['response-text'].className, 'alert alert-success display-margin');
        assert.equal(document.elements['response-text'].innerText, 'You Got It!');

        game.switcher(-1, document);
        assert.equal(document.elements['response-text'].className, 'alert alert-danger display-margin');
        assert.equal(document.elements['response-text'].innerText, 'You Are Incorrect');
    });

    it('matches requested letters as standalone classifier tokens', () => {
        assert.equal(game.findLetterMatch('classified letter: g', 'g') > -1, true);
        assert.equal(game.findLetterMatch('classified letter: g', 'a'), -1);
    });

    it('starts cloud classification and schedules the hand data lookup', () => {
        const document = createDocument();
        const ajax = createAjaxRecorder('cloud started');
        const delays = [];

        game.cloudStart('c', {
            ajax: ajax.ajax,
            document,
            setTimeout(callback, delay) {
                delays.push(delay);
            },
        });

        assert.equal(document.elements['response-text'].className, 'alert alert-warning display-margin');
        assert.equal(document.elements['response-text'].innerText, 'Waiting For Response');
        assert.equal(ajax.calls[0].url, game.backendUrl(game.CLOUD_START_PATH));
        assert.deepEqual(delays, [game.CLOUD_RESPONSE_DELAY_MS]);
    });

    it('shows a cloud start error when the backend request fails', () => {
        const document = createDocument();

        game.cloudStart('a', {
            ajax(options) {
                options.error();
            },
            document,
            setTimeout() {},
        });

        assert.equal(document.elements['wait-message'].innerText, 'Error Starting Subscription Service');
        assert.equal(document.elements['wait-message'].style.color, 'red');
    });

    it('reads hand data and marks matching letters correct', () => {
        const document = createDocument();

        class FakeRequest {
            open(method, url, async) {
                this.method = method;
                this.url = url;
                this.async = async;
            }

            send() {
                this.readyState = 4;
                this.status = 200;
                this.responseText = 'classified letter: d';
                this.onreadystatechange();
            }
        }

        game.mainLetterFind('d', {
            XMLHttpRequest: FakeRequest,
            document,
        });

        assert.equal(document.elements.output.innerHTML, 'classified letter: d');
        assert.equal(document.elements['response-text'].innerText, 'You Got It!');
    });

    it('reads hand data and marks non-matching letters incorrect', () => {
        const document = createDocument();

        class FakeRequest {
            open(method, url, async) {
                this.method = method;
                this.url = url;
                this.async = async;
            }

            send() {
                this.readyState = 4;
                this.status = 200;
                this.responseText = 'classified letter: g';
                this.onreadystatechange();
            }
        }

        game.mainLetterFind('a', {
            XMLHttpRequest: FakeRequest,
            document,
        });

        assert.equal(document.elements.output.innerHTML, 'classified letter: g');
        assert.equal(document.elements['response-text'].innerText, 'You Are Incorrect');
    });

    it('raises a helpful error when required page elements are missing', () => {
        const document = createDocument([]);

        assert.throws(() => game.readyToPlay(document), /Missing required element: wait-message/);
    });
});
