const { spawn } = require('child_process');

console.log('Starting Uvicorn via Node.js...');

const pyProcess = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'], {
  stdio: 'inherit',
  shell: true,
  env: { ...process.env, PYTHONPATH: __dirname }
});

pyProcess.on('close', (code) => {
  console.log(`python process exited with code ${code}`);
});
