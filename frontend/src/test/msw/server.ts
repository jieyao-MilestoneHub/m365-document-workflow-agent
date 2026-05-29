import { setupServer } from "msw/node";

// Empty by default — each test declares the responses it expects with server.use(...).
// This keeps the API contract explicit per surface and surfaces accidental extra calls.
export const server = setupServer();
