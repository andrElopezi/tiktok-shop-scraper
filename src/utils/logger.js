function formatMessage(level, args) {
  const ts = new Date().toISOString();
  return [`[${ts}] [${level}]`, ...args];
}

export const logger = {
  info: (...args) => {
    console.log(...formatMessage('INFO', args));
  },
  error: (...args) => {
    console.error(...formatMessage('ERROR', args));
  },
  debug: (...args) => {
    if (process.env.DEBUG === '1') {
      console.log(...formatMessage('DEBUG', args));
    }
  }
};