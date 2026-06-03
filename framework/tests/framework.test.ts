import { describe, expect, it } from "vitest";

import { DEVEX_VERSION } from "../src/index.js";

describe("devex-framework", () => {
  it("exports DEVEX_VERSION", () => {
    expect(DEVEX_VERSION).toBe("0.1.0");
  });
});
