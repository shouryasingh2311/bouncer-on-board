// DECOY: static analysis only, never execute or install
// This file is an inert test fixture designed to trigger static regex/packument detection.
// It contains NO functioning credential theft, network calls, or harmful payloads.

const payload = "console.log('BOB inert test decoy executed safely');";
const b64 = Buffer.from(payload).toString('base64');

// Static inspection trigger: Buffer base64 decode feeding eval
eval(Buffer.from(b64, 'base64').toString('utf-8'));

// Decoy text reference to localhost canary host
const canary = "http://127.0.0.1:8765/canary";
