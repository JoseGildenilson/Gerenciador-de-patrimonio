import '@testing-library/jest-dom';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Previne "Error: Not implemented: navigation (except hash changes)" no JSDOM ao testar downloads via link.click()
HTMLAnchorElement.prototype.click = vi.fn();

afterEach(() => {
  cleanup();
});
