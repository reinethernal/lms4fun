import { useEffect, useRef } from 'react';
import Editor, { type Monaco } from '@monaco-editor/react';
import type { editor } from 'monaco-editor';
import { monacoLanguage } from '@/api/client';

interface CodeEditorProps {
  value: string;
  language: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  highlightLine?: number | null;
}

export function CodeEditor({
  value,
  language,
  onChange,
  readOnly = false,
  highlightLine = null,
}: CodeEditorProps) {
  const editorRef = useRef<editor.IStandaloneCodeEditor | null>(null);
  const monacoRef = useRef<Monaco | null>(null);
  const decorationRef = useRef<editor.IEditorDecorationsCollection | null>(null);

  useEffect(() => {
    const ed = editorRef.current;
    const monaco = monacoRef.current;
    if (!ed || !monaco) return;

    decorationRef.current?.clear();

    if (highlightLine != null && highlightLine > 0) {
      decorationRef.current = ed.createDecorationsCollection([
        {
          range: new monaco.Range(highlightLine, 1, highlightLine, 1),
          options: {
            isWholeLine: true,
            className: 'editor-error-line',
            glyphMarginClassName: 'editor-error-glyph',
          },
        },
      ]);
      ed.revealLineInCenter(highlightLine);
    }
  }, [highlightLine, value]);

  return (
    <div className="editor-wrap">
      <Editor
        height="100%"
        language={monacoLanguage(language)}
        value={value}
        onChange={(v) => onChange(v ?? '')}
        theme="vs-dark"
        onMount={(ed, monaco) => {
          editorRef.current = ed;
          monacoRef.current = monaco;
        }}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          readOnly,
          scrollBeyondLastLine: false,
          automaticLayout: true,
          tabSize: 4,
          glyphMargin: true,
        }}
      />
    </div>
  );
}
