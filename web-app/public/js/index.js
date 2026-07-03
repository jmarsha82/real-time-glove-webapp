(function bootstrapGame(root) {
    'use strict';

    const BACKEND_ORIGIN = 'http://127.0.0.1:5000';
    const SUBSCRIBE_START_PATH = '/subscribe-start';
    const CLOUD_START_PATH = '/cloud-start';
    const HAND_DATA_PATH = 'hand_data.txt';
    const SUBSCRIBE_READY_DELAY_MS = 3000;
    const CLOUD_RESPONSE_DELAY_MS = 5000;

    function getElement(doc, id) {
        const element = doc.getElementById(id);
        if (!element) {
            throw new Error(`Missing required element: ${id}`);
        }
        return element;
    }

    function backendUrl(path) {
        return `${BACKEND_ORIGIN}${path}`;
    }

    function localAjax(options) {
        const request = new root.XMLHttpRequest();
        request.open(options.type || 'GET', options.url, true);
        request.onreadystatechange = function onAjaxReadyStateChange() {
            if (request.readyState !== 4) {
                return;
            }

            if (request.status >= 200 && request.status < 300) {
                options.success(request.responseText);
                return;
            }

            options.error(request);
        };
        request.send(null);
    }

    function defaultDependencies() {
        return {
            ajax: root.$ && root.$.ajax ? root.$.ajax : localAjax,
            document: root.document,
            setTimeout: root.setTimeout,
            XMLHttpRequest: root.XMLHttpRequest,
        };
    }

    function setMessage(doc, id, text, color) {
        const element = getElement(doc, id);
        element.innerText = text;
        if (color) {
            element.style.color = color;
        }
        return element;
    }

    function readyToPlay(doc = root.document) {
        return setMessage(doc, 'wait-message', 'Ready To Play', 'green');
    }

    function showError(doc, message = 'Error Starting Subscription Service') {
        return setMessage(doc, 'wait-message', message, 'red');
    }

    function setResponse(doc, className, text) {
        const response = getElement(doc, 'response-text');
        response.className = className;
        response.innerText = text;
        return response;
    }

    function escapeRegex(value) {
        return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function findLetterMatch(text, letter) {
        const letterPattern = new RegExp(`\\b${escapeRegex(letter)}\\b`, 'i');
        return text.search(letterPattern);
    }

    function subscribeStart(dependencies = defaultDependencies()) {
        const { ajax, document: doc, setTimeout: schedule } = dependencies;

        ajax({
            type: 'GET',
            url: backendUrl(SUBSCRIBE_START_PATH),
            crossDomain: true,
            success: function onSubscribeSuccess() {
                const subButton = getElement(doc, 'subscribe-button');
                subButton.className = 'btn btn-primary button-position disabled';
                subButton.setAttribute('aria-disabled', 'true');
                schedule(function markReady() {
                    readyToPlay(doc);
                }, SUBSCRIBE_READY_DELAY_MS);
            },
            error: function onSubscribeError() {
                showError(doc);
            },
        });
    }

    function cloudStart(letter, dependencies = defaultDependencies()) {
        const { ajax, document: doc, setTimeout: schedule } = dependencies;

        setResponse(doc, 'alert alert-warning display-margin', 'Waiting For Response');
        ajax({
            type: 'GET',
            url: backendUrl(CLOUD_START_PATH),
            crossDomain: true,
            success: function onCloudSuccess(data) {
                schedule(function readResponse() {
                    mainLetterFind(letter, dependencies);
                }, CLOUD_RESPONSE_DELAY_MS);
                if (root.console) {
                    root.console.log(data);
                    root.console.log('Inside success for Cloud Start');
                }
            },
            error: function onCloudError() {
                showError(doc);
            },
        });
    }

    function switcher(value, doc = root.document) {
        if (value === -1) {
            return setResponse(doc, 'alert alert-danger display-margin', 'You Are Incorrect');
        }
        return setResponse(doc, 'alert alert-success display-margin', 'You Got It!');
    }

    function mainLetterFind(letter, dependencies = defaultDependencies()) {
        const { XMLHttpRequest: Request, document: doc } = dependencies;
        const rawFile = new Request();

        if (root.console) {
            root.console.log('Inside Main Letter Find');
        }

        rawFile.open('GET', HAND_DATA_PATH, true);
        rawFile.onreadystatechange = function onReadyStateChange() {
            if (rawFile.readyState === 4 && (rawFile.status === 200 || rawFile.status === 0)) {
                if (root.console) {
                    root.console.log('Found txt file');
                }
                const allText = rawFile.responseText;
                const textAreaTag = getElement(doc, 'output');
                textAreaTag.innerHTML = allText;
                switcher(findLetterMatch(allText, letter), doc);
            }

            if (root.console) {
                root.console.log(rawFile.status);
            }
        };
        rawFile.send(null);
    }

    const api = {
        BACKEND_ORIGIN,
        CLOUD_RESPONSE_DELAY_MS,
        CLOUD_START_PATH,
        HAND_DATA_PATH,
        SUBSCRIBE_READY_DELAY_MS,
        SUBSCRIBE_START_PATH,
        backendUrl,
        cloudStart,
        findLetterMatch,
        localAjax,
        mainLetterFind,
        readyToPlay,
        showError,
        subscribeStart,
        switcher,
    };

    root.subscribeStart = subscribeStart;
    root.readyToPlay = readyToPlay;
    root.cloudStart = cloudStart;
    root.switcher = switcher;
    root.mainLetterFind = mainLetterFind;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    }
}(typeof window !== 'undefined' ? window : globalThis));
