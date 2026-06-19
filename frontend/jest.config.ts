/* Sprint S1 - jest configuration
 * Uses next/jest for SWC-powered TS/JSX transform (no ts-jest needed).
 * Test pattern: __tests__/*.test.{ts,tsx} co-located with source.
 */
import type { Config } from 'jest'
import nextJest from 'next/jest.js'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'jsdom',
  // Sprint S1 ui-scaffold: corrected typo from sprint-scaffold output
  // (was 'setupFilesAfterEach' — not a valid jest config key).
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testPathIgnorePatterns: ['/node_modules/', '/.next/'],
}

export default createJestConfig(config)
