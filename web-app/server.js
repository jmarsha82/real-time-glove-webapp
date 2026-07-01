const express = require('express');
const path = require('path');

require('dotenv').config();

const app = express();
const port = process.env.PORT || 8080;

const publicDirectory = path.join(__dirname, 'public');

app.use(express.static(publicDirectory));
app.use('/scripts', express.static(path.join(__dirname, 'node_modules')));

app.get('/health', (req, res) => {
    res.status(200).json({ status: 'ok' });
});

const errorHandler = (err, req, res, next) => {
    if (err.response) {
        // The request was made and the server responded with a status code
        // that falls out of the range of 2xx
        res.status(403).send({ title: 'Server responded with an error', message: err.message });
    } else if (err.request) {
        // The request was made but no response was received
        res.status(503).send({ title: 'Unable to communicate with server', message: err.message });
    } else {
        // Something happened in setting up the request that triggered an Error
        res.status(500).send({ title: 'An unexpected error occurred', message: err.message });
    }
};

app.use(errorHandler);

function startServer(listenPort = port) {
    return app.listen(listenPort, () => {
        // eslint-disable-next-line no-console
        console.log('listening on %d', listenPort);
    });
}

if (require.main === module) {
    startServer();
}

module.exports = {
    app,
    errorHandler,
    publicDirectory,
    startServer,
};
