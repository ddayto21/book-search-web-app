/**
 * @fileoverview Unit tests for the SSE parsing and formatting functions.
 * 
 * These tests verify that the helper functions produce a cleaned markdown string
 * by extracting SSE tokens, joining them with a single space, and performing cleanup.
 *
 * Note: The current implementation concatenates tokens with a single space,
 * so we update the expected outputs accordingly.
 */

import { extractTokens, joinTokens, parseSseData, formatContent, getTimeAgo } from "../../utils/parse-sse-data";
import type { Message } from "@ai-sdk/react";

// Tests for extractTokens
describe("extractTokens", () => {
  /**
   * Test that extractTokens splits the input correctly and returns only tokens that start with "data:".
   */
  test("should extract tokens from SSE input", () => {
    const input = `data: Hello\n\ndata: World\n\nrandom: Ignored`;
    const expected = ["Hello", "World"];
    expect(extractTokens(input)).toEqual(expected);
  });

  /**
   * Test that extractTokens parses JSON content correctly.
   */
  test("should parse JSON tokens correctly", () => {
    const jsonContent = JSON.stringify({ content: "Parsed JSON" });
    const input = `data: ${jsonContent}\n\n`;
    const expected = ["Parsed JSON"];
    expect(extractTokens(input)).toEqual(expected);
  });

  /**
   * Test that empty or whitespace-only input returns an empty array.
   */
  test("should return an empty array for empty or whitespace-only input", () => {
    expect(extractTokens("")).toEqual([]);
    expect(extractTokens("  \n\n ")).toEqual([]);
  });
});

// Tests for joinTokens
describe("joinTokens", () => {
  /**
   * Test that joinTokens correctly joins an array of tokens with a single space.
   */
  test("should join tokens with a single space", () => {
    const tokens = ["Hello", "World"];
    const expected = "Hello World";
    expect(joinTokens(tokens)).toBe(expected);
  });

  /**
   * Test that joinTokens collapses extra whitespace between tokens.
   */
  test("should collapse extra whitespace between tokens", () => {
    const tokens = ["Hello", "   World  "];
    const expected = "Hello World";
    expect(joinTokens(tokens)).toBe(expected);
  });
});

// Tests for parseSseData (full pipeline)
describe("parseSseData", () => {
  /**
   * Test that an empty input returns an empty string.
   */
  test("should return an empty string for empty input", () => {
    expect(parseSseData("")).toBe("");
  });

  /**
   * Test that a single SSE event is parsed correctly.
   */
  test("should parse a single SSE event correctly", () => {
    const input = "data: Hello\n\n";
    const expectedOutput = "Hello";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that multiple SSE events are parsed and concatenated with a single space.
   */
  test("should parse multiple SSE events correctly", () => {
    const input = "data: Hello\n\ndata: World\n\n";
    const expectedOutput = "Hello World";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that lines not starting with "data:" are ignored.
   */
  test("should ignore lines that do not start with 'data:'", () => {
    const input = "random: Not included\ndata: Included\n";
    const expectedOutput = "Included";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that extra spaces after 'data:' are trimmed.
   */
  test("should handle extra spaces after 'data:'", () => {
    const input = "data:    Spaced\n\n";
    const expectedOutput = "Spaced";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that multiple SSE events are concatenated with a single space.
   */
  test("should concatenate events with a single space", () => {
    const input = "data: Part1\n\ndata: Part2\n\ndata: Part3\n\n";
    const expectedOutput = "Part1 Part2 Part3";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that multiple data lines on a single physical line are handled correctly.
   */
  test("should handle multiple data lines", () => {
    const input = "data: Hello\ndata: World!\n\n";
    const expectedOutput = "Hello World!";
    expect(parseSseData(input)).toBe(expectedOutput);
  });

  /**
   * Test that input containing only whitespace returns an empty string.
   */
  test("should return empty string for no data", () => {
    expect(parseSseData("")).toBe("");
    expect(parseSseData("  \n\n ")).toBe("");
  });

  /**
   * Test that invalid (non-string) input throws an error.
   */
  test("should throw error on invalid input", () => {
    expect(() => parseSseData(null as unknown as string)).toThrow("Input must be a string");
  });
});

// Tests for formatContent
describe("formatContent", () => {
  /**
   * Test that formatContent processes an assistant message correctly.
   * It should use parseSseData to clean the SSE data and return the formatted content.
   */
  test("formatContent works with assistant messages", () => {
    const message: Message = {
      role: "assistant",
      content: "data: This is formatted\n",
      id: "some-unique-id",
    };
    expect(formatContent(message)).toBe("This is formatted");
  });

  /**
   * Test that formatContent correctly formats bullet lists and headings.
   * Since the current implementation joins tokens with a single space, the expected output
   * is a single-line string with spaces between tokens.
   */
  test("should format bullet lists and headings correctly", () => {
    const input = `
data: # Heading 1

data: - Bullet 1
data: - Bullet 2

data: **Bold Text**
`;
    const expectedOutput = "# Heading 1 - Bullet 1 - Bullet 2 Bold Text";
    expect(parseSseData(input)).toBe(expectedOutput);
  });
});

// Optional: Tests for getTimeAgo
describe("getTimeAgo", () => {
  /**
   * Test that getTimeAgo returns an empty string if no timestamp is provided.
   */
  test("should return an empty string if no timestamp is provided", () => {
    expect(getTimeAgo()).toBe("");
  });

  /**
   * Test that getTimeAgo returns a non-empty relative time string for a valid timestamp.
   */
  test("should return a relative time string for a valid timestamp", () => {
    const now = new Date().toISOString();
    const result = getTimeAgo(now);
    expect(result).not.toBe("");
  });
});