const http = require('http');
const { execSync } = require('child_process');

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        try {
            console.log('Running python test...');
            // Need absolute paths for require
            const output = execSync('python test_ml_pipeline.py', { 
                cwd: __dirname,
                env: { ...process.env, PYTHONPATH: __dirname },
                encoding: 'utf-8'
            });
            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end(`SUCCESS:\n${output}`);
        } catch (error) {
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end(`ERROR:\nStatus: ${error.status}\nStdout: ${error.stdout}\nStderr: ${error.stderr}\nMessage: ${error.message}`);
        }
    } else {
        res.writeHead(404);
        res.end();
    }
});

server.listen(3000, '0.0.0.0', () => {
    console.log('Test proxy running on http://localhost:3000');
});
