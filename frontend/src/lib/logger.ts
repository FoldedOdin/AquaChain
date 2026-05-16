/**
 * Structured Logger
 *
 * Provides leveled logging that is:
 * - Silent in production (info/debug/warn calls are no-ops)
 * - Always active for errors (errors are always surfaced)
 * - Strips token values and sensitive payloads automatically
 *
 * WHY: The previous dataService.ts logged raw token substrings and full
 * request/response bodies to the browser console, which are visible to
 * any user who opens DevTools on a production deployment. This violates
 * OWASP A02 (Cryptographic Failures) and is a credential exposure risk.
 */

const IS_DEV = process.env.NODE_ENV === 'development';

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  level: LogLevel;
  message: string;
  context?: Record<string, unknown>;
}

/** Redact known sensitive field names from an object before logging. */
function redact(obj?: Record<string, unknown>): Record<string, unknown> | undefined {
  if (!obj) return undefined;
  const SENSITIVE_KEYS = /token|secret|password|authorization|key|credential/i;
  return Object.fromEntries(
    Object.entries(obj).map(([k, v]) => [
      k,
      SENSITIVE_KEYS.test(k) ? '[REDACTED]' : v,
    ])
  );
}

function log(level: LogLevel, message: string, context?: Record<string, unknown>): void {
  if (!IS_DEV && level !== 'error') return;

  const entry: LogEntry = { level, message, context: redact(context) };

  switch (level) {
    case 'debug':
      // eslint-disable-next-line no-console
      console.debug(`[${level.toUpperCase()}]`, message, entry.context ?? '');
      break;
    case 'info':
      // eslint-disable-next-line no-console
      console.info(`[${level.toUpperCase()}]`, message, entry.context ?? '');
      break;
    case 'warn':
      // eslint-disable-next-line no-console
      console.warn(`[${level.toUpperCase()}]`, message, entry.context ?? '');
      break;
    case 'error':
      // eslint-disable-next-line no-console
      console.error(`[${level.toUpperCase()}]`, message, entry.context ?? '');
      break;
  }
}

export const logger = {
  debug: (message: string, context?: Record<string, unknown>) => log('debug', message, context),
  info: (message: string, context?: Record<string, unknown>) => log('info', message, context),
  warn: (message: string, context?: Record<string, unknown>) => log('warn', message, context),
  error: (message: string, context?: Record<string, unknown>) => log('error', message, context),
};

export default logger;
