/**
 * Formats API errors (including FastAPI/Pydantic validation errors) into a human-readable string.
 * This guarantees that React will never receive an object or array in error JSX.
 */
export function formatApiError(err: any, fallbackMessage: string = 'Ocorreu um erro na requisição'): string {
  if (!err) return fallbackMessage;

  const detail = err.response?.data?.detail;

  if (typeof detail === 'string' && detail.trim().length > 0) {
    return detail;
  }

  if (Array.isArray(detail)) {
    // Pydantic validation error list: [{ type, loc, msg, input }, ...]
    const messages = detail
      .map((item: any) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object') {
          const field = Array.isArray(item.loc) ? item.loc[item.loc.length - 1] : '';
          const msg = item.msg || JSON.stringify(item);
          return field && field !== 'body' ? `${field}: ${msg}` : msg;
        }
        return String(item);
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join('; ');
    }
  }

  if (detail && typeof detail === 'object') {
    if (detail.message && typeof detail.message === 'string') {
      return detail.message;
    }
    try {
      return JSON.stringify(detail);
    } catch {
      return fallbackMessage;
    }
  }

  return fallbackMessage;
}
