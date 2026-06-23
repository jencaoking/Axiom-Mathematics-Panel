import * as monaco from 'monaco-editor';

export class MathLabEditor {
    public editor: monaco.editor.IStandaloneCodeEditor;

    constructor(containerId: string) {
        // 1. 注册 MathLab 专属赛博朋克深色主题
        this.registerCustomTheme();
        
        // 2. 注册 MathLab 专属智能提示与悬浮文档引擎
        this.registerMathLabProviders();

        // 3. 初始化编辑器实例 (开启极客级丝滑配置)
        this.editor = monaco.editor.create(document.getElementById(containerId)!, {
            value: '# 🚀 欢迎来到 MathLab 极客沙盒\n# 尝试输入 cs_ 看看底层的 C# 魔法吧...\n\n',
            language: 'python',
            theme: 'mathlab-dark',
            automaticLayout: true,
            fontSize: 14,
            fontFamily: 'Consolas, "Courier New", monospace',
            minimap: { enabled: false },        // 关闭右侧小地图以节省空间
            suggestOnTriggerCharacters: true,   // 开启输入触发提示
            smoothScrolling: true,              // 丝滑滚动
            cursorBlinking: 'smooth',           // 呼吸灯光标
            cursorSmoothCaretAnimation: 'on',   // 开启光标平滑移动动画 (VS Code 招牌体验)
            padding: { top: 16 }
        });
    }

    private registerCustomTheme() {
        monaco.editor.defineTheme('mathlab-dark', {
            base: 'vs-dark',
            inherit: true,
            rules: [
                { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
                { token: 'keyword', foreground: 'C586C0', fontStyle: 'bold' },
                { token: 'string', foreground: 'CE9178' },
                { token: 'number', foreground: 'B5CEA8' },
                // 赋予我们自定义的 C# 引擎命名空间专属的高亮颜色 (薄荷绿)
                { token: 'identifier.mathlab', foreground: '4EC9B0', fontStyle: 'bold' } 
            ],
            colors: {
                'editor.background': '#0f172a', // 深沉的蓝黑底色 (Slate-900)
                'editor.lineHighlightBackground': '#1e293b',
                'editorCursor.foreground': '#38bdf8', // 亮蓝色的光标
            }
        });
    }

    private registerMathLabProviders() {
        // --- A. 注册自动补全 (IntelliSense) ---
        monaco.languages.registerCompletionItemProvider('python', {
            provideCompletionItems: (model, position) => {
                const word = model.getWordUntilPosition(position);
                const range = {
                    startLineNumber: position.lineNumber,
                    endLineNumber: position.lineNumber,
                    startColumn: word.startColumn,
                    endColumn: word.endColumn
                };

                const suggestions: monaco.languages.CompletionItem[] = [
                    {
                        label: 'cs_calculus.integrate_adaptive',
                        kind: monaco.languages.CompletionItemKind.Method,
                        detail: '⚡ 自适应高精度积分 (C# Math.NET)',
                        documentation: { value: '调用底层 C# 引擎进行极速高斯-克朗罗德积分。\n\n**参数:**\n- `func`: Python 函数 (如 lambda)\n- `a`: 下限\n- `b`: 上限' },
                        // Snippet 魔法：输入后光标会自动跳到 ${1} 的位置，按 Tab 键切换到 ${2}
                        insertText: 'cs_calculus.integrate_adaptive(${1:lambda x: x**2}, ${2:0}, ${3:1})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range: range
                    },
                    {
                        label: 'cs_fft.analyze_spectrum',
                        kind: monaco.languages.CompletionItemKind.Method,
                        detail: '🌊 快速傅里叶变换 (FFT)',
                        documentation: { value: '对输入信号进行原地 FFT 极速解析，返回频率和幅值数组。' },
                        insertText: 'cs_fft.analyze_spectrum(${1:signal_array}, ${2:sample_rate})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range: range
                    },
                    {
                        label: 'cs_geometry.solve_line_circle',
                        kind: monaco.languages.CompletionItemKind.Method,
                        detail: '⭕ 极速线圆求交 (零GC)',
                        documentation: { value: '利用 C# 内存复用池计算直线与圆的交点。' },
                        insertText: 'cs_geometry.solve_line_circle(${1:a}, ${2:b}, ${3:c}, ${4:cx}, ${5:cy}, ${6:r})',
                        insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
                        range: range
                    }
                ];
                return { suggestions: suggestions };
            }
        });

        // --- B. 注册悬浮提示 (Hover Docs) ---
        monaco.languages.registerHoverProvider('python', {
            provideHover: (model, position) => {
                const word = model.getWordAtPosition(position);
                if (word && word.word === 'cs_calculus') {
                    return {
                        range: new monaco.Range(position.lineNumber, word.startColumn, position.lineNumber, word.endColumn),
                        contents: [
                            { value: '### ⚡ MathLab C# Calculus Engine' },
                            { value: '通过 `pythonnet` 实现内存级直调的微积分算力底座。\n\n提供超越 Python 原生的并行计算能力与高精度自适应算法。' }
                        ]
                    };
                }
                return null;
            }
        });
    }

    // ==========================================
    // 暴露给 Python (PySide6 QWebChannel) 的接口
    // ==========================================

    public getCode(): string {
        return this.editor.getValue();
    }

    public setCode(code: string): void {
        this.editor.setValue(code);
    }
    
    // 动态语法/错误诊断标红 (Diagnostics)
    public setDiagnostics(errors: Array<{line: number, message: string}>): void {
        const markers = errors.map(err => ({
            severity: monaco.MarkerSeverity.Error, // 设为 Error 会显示红波浪线
            startLineNumber: err.line,
            startColumn: 1,
            endLineNumber: err.line,
            endColumn: 1000,
            message: err.message
        }));
        monaco.editor.setModelMarkers(this.editor.getModel()!, "mathlab", markers);
    }
}

// 将初始化方法挂载到全局 window 对象，供外部 HTML 调用
(window as any).initMathLabEditor = (containerId: string) => {
    (window as any).mathEditor = new MathLabEditor(containerId);
};
