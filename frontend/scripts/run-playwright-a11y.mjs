import { spawn } from 'node:child_process';

const env = { ...process.env };

delete env.FORCE_COLOR;
delete env.NO_COLOR;
env.PW_DISABLE_TS_ESM = '1';

const child = spawn(
  'playwright',
  ['test', '--config', 'playwright.config.cjs'],
  {
    env,
    shell: process.platform === 'win32',
    stdio: 'inherit',
  },
);

child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }

  process.exit(code ?? 1);
});
