import { spawn } from 'node:child_process'
import { resolve } from 'node:path'
const python = resolve('..', '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python')
const child = spawn(python, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8001'], {
  cwd: resolve('../backend'), stdio: 'inherit', env: { ...process.env, UNDO_DB: resolve('../.runtime/e2e.db'), UNDO_ORIGINS: 'http://127.0.0.1:5174' },
})
for (const signal of ['SIGINT', 'SIGTERM']) process.on(signal, () => child.kill())
child.on('exit', code => process.exit(code ?? 1))
