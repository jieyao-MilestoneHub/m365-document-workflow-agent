import { vi } from "vitest";

type Listener = (event: { data: string }) => void;

/**
 * Minimal controllable EventSource for tests. The api boundary constructs `new EventSource`;
 * tests drive emitted server events through the recorded instance. Install with
 * `installMockEventSource()` and read the latest instance from `MockEventSource.last`.
 */
export class MockEventSource {
  static CONNECTING = 0 as const;
  static OPEN = 1 as const;
  static CLOSED = 2 as const;
  static instances: MockEventSource[] = [];

  url: string;
  readyState = 1;
  onerror: (() => void) | null = null;
  private listeners: Record<string, Listener[]> = {};

  constructor(url: string) {
    this.url = url;
    MockEventSource.instances.push(this);
  }

  static get last(): MockEventSource {
    return MockEventSource.instances[MockEventSource.instances.length - 1];
  }

  addEventListener(type: string, cb: Listener) {
    (this.listeners[type] ??= []).push(cb);
  }

  close() {
    this.readyState = MockEventSource.CLOSED;
  }

  emit(type: string, data: unknown) {
    (this.listeners[type] ?? []).forEach((cb) => cb({ data: JSON.stringify(data) }));
  }

  emitError() {
    this.onerror?.();
  }
}

export function installMockEventSource() {
  MockEventSource.instances = [];
  vi.stubGlobal("EventSource", MockEventSource);
}
