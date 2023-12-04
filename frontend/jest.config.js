const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  preset: "ts-jest",
  collectCoverage: true, // Enable coverage collection
  collectCoverageFrom: [
    "**/*.{js,jsx,ts,tsx}", // Include all JavaScript and TypeScript files
    "!**/node_modules/**", // Exclude node_modules
    "!**/.next/**", // Exclude .next build output
    "!**/coverage/**", // Exclude coverage directory
    "!**/*.config.{js,ts}", // Exclude config files
    // Add more patterns to exclude files as needed
  ],
  coverageDirectory: "coverage", // Output directory for coverage reports
  coverageReporters: ["json", "lcov", "text", "clover"], // Report formats
};

module.exports = createJestConfig(customJestConfig);
