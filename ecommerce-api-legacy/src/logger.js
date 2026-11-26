const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger(level = 'info') {
  const min = LEVELS[level] || LEVELS.info;
  const log = (lvl, out) => (...args) => {
    if (LEVELS[lvl] >= min) out(`[${lvl.toUpperCase()}]`, ...args);
  };
  return {
    debug: log('debug', console.log),
    info: log('info', console.log),
    warn: log('warn', console.warn),
    error: log('error', console.error),
  };
}

module.exports = { createLogger };
