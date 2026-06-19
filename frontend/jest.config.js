/* Sprint S1 - jest configuration (CJS form to avoid ts-node dep).
 * Uses next/jest for SWC-powered TS/JSX transform (no ts-jest needed).
 * Test pattern: __tests__/*.test.{ts,tsx} co-located with source.
 */
const nextJest = require('next/jest.js');

const createJestConfig = nextJest({ dir: './' });

/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['/node_modules/', '/.next/'],
};

module.exports = createJestConfig(config);
