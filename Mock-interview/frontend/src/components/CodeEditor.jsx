// Deliberately a styled <textarea>, not a full editor - keeps the project
// dependency-light. Swap in @monaco-editor/react or CodeMirror here if you
// want syntax highlighting; nothing else in the app needs to change since
// this component's contract is just (value, onChange) -> plain text.
export default function CodeEditor({ value, onChange, placeholder }) {
  function handleKeyDown(e) {
    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart, selectionEnd } = e.target;
      const newValue = value.slice(0, selectionStart) + "  " + value.slice(selectionEnd);
      onChange(newValue);
      requestAnimationFrame(() => {
        e.target.selectionStart = e.target.selectionEnd = selectionStart + 2;
      });
    }
  }

  return (
    <textarea
      className="code-editor"
      spellCheck={false}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={handleKeyDown}
      placeholder={placeholder || "// Write your solution here"}
    />
  );
}
