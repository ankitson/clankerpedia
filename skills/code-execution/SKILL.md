---
name: code-execution
description: combine multiple MCP tools in one tool call with typescript code, avoid long content in context, multi-step workflows with code
---

# SKILL.md: code_execution

## 🎯 CORE PRINCIPLES
* **Purpose:** Sandboxed computation. Use for math, data transformation, and logic.
* **Objective:** Return structured, parsed results.
* **Mode:** Single-turn, atomic execution.

## 🛠️ PATTERNS (The Right Way)

### 1. Defensive Wrapping
Wrap all logic in `try/catch` blocks to prevent runtime exceptions from crashing the agentic loop.
```javascript
const task = () => {
  try {
    return { status: "ok", data: 1 + 1 };
  } catch (e) {
    return { status: "error", msg: e.message };
  }
};
task();
```

### 2. Structured Returns
Return JSON-serializable objects. Avoid raw strings; favor key-value pairs for easier downstream parsing.
```javascript
// GOOD
return { success: true, value: 42 };

// BAD
return "The answer is 42"; 
```

### 3. The Data Pipeline (Orchestration)
Use functions to encapsulate complex, multi-step logic within a single call.
```javascript
const pipeline = () => {
  const raw = [5, 12, 8];
  const step1 = raw.map(x => x * 2);
  const step2 = step1.reduce((a, b) => a + b, 0);
  return { final_sum: step2 };
};
pipeline();
```

## ⚠️ ANTI-PATTERNS (Gotchas)

*   **🚫 NO NETWORK:** No `fetch`, no `axios`, no `requests`. Sandbox is air-gapped.
*   **🚫 NO DISK:** No `fs.writeFile`. Filesystem access is restricted.
*   **🚫 NO ASYNC/AWAIT (Usually):** Runtime is synchronous. Do not use `await` unless the environment specifically supports the async wrapper.
*   **🚫 NO HEAVY LOOPS:** Avoid $O(n^2)$ or higher on large datasets. Execution timeouts will kill the process.
*   **🚫 NO GLOBAL STATE:** Assume every `code_execution` call starts with a clean, empty slate. No persistence between calls.
