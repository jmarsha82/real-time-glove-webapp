require('dotenv').config();
const requirejs = require('requirejs');
const PythonShell = require('python-shell');
const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const port = process.env.PORT || 8080;

// Set public folder as root
app.use(express.static('public'));

app.use('/scripts', express.static(`/node_modules/`));


const errorHandler = (err, req, res) => {
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

app.listen(port, () => {
    // eslint-disable-next-line no-console
    console.log('listening on %d', port);
});
