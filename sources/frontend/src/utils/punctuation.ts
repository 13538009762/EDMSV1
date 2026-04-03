/** Lightweight punctuation normalization for Chinese text. */
export function checkPunctuationIssues(text: string): string[] {
  const issues: string[] = [];
  const stack: string[] = [];
  const pairs: Record<string, string> = { "（": "）", "【": "】", "「": "」", "《": "》" };
  const closeToOpen: Record<string, string> = Object.fromEntries(
    Object.entries(pairs).map(([a, b]) => [b, a]),
  );
  for (let i = 0; i < text.length; i++) {
    const c = text[i]!;
    if (c in pairs) stack.push(c);
    else if (c in closeToOpen) {
      const expect = pairs[stack.pop() || ""];
      if (expect !== c) issues.push(`Position ${i}: mismatched bracket`);
    }
  }
  if (stack.length) issues.push("Unclosed opening brackets");
  if (/，{2,}/.test(text)) issues.push("Repeated commas");
  if (/。{2,}/.test(text)) issues.push("Repeated periods");
  return issues;
}

export function fixPunctuation(text: string): string {
  return text.replace(/，{2,}/g, "，").replace(/。{2,}/g, "。");
}
