import { useEffect, useState, useRef } from 'react';
import { Editor } from '@monaco-editor/react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Play, Edit3, Save, X, Check, ChevronRight, Code2, Terminal, AlertCircle, CheckCircle2, XCircle } from 'lucide-react';
import { useChatStore } from '@/stores/chatStore';
import { useUIStore } from '@/stores/uiStore';
import { WS_BASE_URL } from '@/lib/api/client';
import { useSandboxStore } from '@/stores/sandboxStore';
import { playgroundExamples, type CodeStep, type PlaygroundExample } from '@/data/playgroundExamples';
import axios from 'axios';


export function CodeEditor() {
  const { currentSession } = useChatStore();
  const { currentSandbox } = useSandboxStore();
  const { theme } = useUIStore();  //  获取当前主题
  
  const [selectedExample, setSelectedExample] = useState<PlaygroundExample | null>(null);
  const [steps, setSteps] = useState<CodeStep[]>([]);
  const [editingStepIndex, setEditingStepIndex] = useState<number | null>(null);
  const [editedCode, setEditedCode] = useState('');
  const [executingStepIndex, setExecutingStepIndex] = useState<number | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [stepContextIds, setStepContextIds] = useState<Record<number, string>>({});
  //  执行结果存储：{stepIndex: {status, stdout, stderr, error, timestamp}}
  const [stepResults, setStepResults] = useState<Record<number, {
    status: 'success' | 'failed' | 'error';
    stdout?: string;
    stderr?: string;
    error?: string;
    timestamp: number;
  }>>({});
  // 控制手风琴展开状态：'examples' 或 'steps'
  const [activeSection, setActiveSection] = useState<string>('steps');
  
  //  使用 ref 避免闭包陷阱
  const executingStepIndexRef = useRef<number | null>(null);
  
  // 初始化：选择第一个示例
  useEffect(() => {
    if (playgroundExamples.length > 0 && !selectedExample) {
      selectExample(playgroundExamples[0]);
    }
  }, []);
  
  //  监听 WebSocket 消息以接收执行结果
  useEffect(() => {
    if (!currentSession) return;
    
    const ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${currentSession.session_id}`);
    
    ws.onopen = () => {
      console.log('[OK] [Playground] WebSocket connected');
      console.log('   Session ID:', currentSession.session_id);
    };
    
    ws.onmessage = (event) => {
      console.log('📨 [Playground] WebSocket message received:', event.data);
      try {
        const message = JSON.parse(event.data);
        console.log('   Parsed message:', message);
        
        // 处理执行完成消息
        if (message.type === 'execution_complete') {
          console.log('[完成] [Playground] Execution complete message received');
          const { data } = message;
          const { status, stdout, stderr, error } = data;
          console.log('   Status:', status);
          console.log('   executingStepIndexRef.current:', executingStepIndexRef.current);
          
          //  使用 ref 获取当前执行的步骤索引
          const currentExecutingIndex = executingStepIndexRef.current;
          
          // 找到对应的步骤
          if (currentExecutingIndex !== null) {
            console.log('   [完成] Updating step result for index:', currentExecutingIndex);
            //  保存执行结果
            setStepResults(prev => ({
              ...prev,
              [currentExecutingIndex]: {
                status: status === 'success' ? 'success' : status === 'failed' ? 'failed' : 'error',
                stdout: stdout || '',
                stderr: stderr || '',
                error: error || '',
                timestamp: Date.now()
              }
            }));
            
            // 标记为已完成（仅成功时）
            if (status === 'success') {
              setCompletedSteps(prev => new Set([...prev, currentExecutingIndex]));
            }
            
            // 清除执行状态
            setExecutingStepIndex(null);
            executingStepIndexRef.current = null;
            console.log('   [完成] Execution state cleared');
          } else {
            console.warn('   [WARNING] currentExecutingIndex is null, ignoring message');
          }
        }
      } catch (err) {
        console.error('[ERROR] [Playground] Failed to parse WebSocket message:', err);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
      console.log('WebSocket closed for playground');
    };
    
    return () => {
      ws.close();
    };
  }, [currentSession]);  //  只依赖 currentSession，保持 WebSocket 连接稳定
  
  // 选择示例
  const selectExample = (example: PlaygroundExample) => {
    setSelectedExample(example);
    setSteps([...example.steps]);
    setEditingStepIndex(null);
    setCompletedSteps(new Set());
    setStepContextIds({});
    setStepResults({});  //  清空执行结果
  };
  
  // 开始编辑步骤
  const startEdit = (stepIndex: number) => {
    setEditingStepIndex(stepIndex);
    setEditedCode(steps[stepIndex].code);
  };
  
  // 保存编辑
  const saveEdit = () => {
    if (editingStepIndex !== null) {
      const newSteps = [...steps];
      newSteps[editingStepIndex] = {
        ...newSteps[editingStepIndex],
        code: editedCode
      };
      setSteps(newSteps);
      setEditingStepIndex(null);
    }
  };
  
  // 取消编辑
  const cancelEdit = () => {
    setEditingStepIndex(null);
    setEditedCode('');
  };
  
  // 执行步骤
  const executeStep = async (stepIndex: number) => {
    if (!currentSession || !currentSession.sandbox_id) {
      alert('请先创建会话和 Sandbox');
      return;
    }
    
    setExecutingStepIndex(stepIndex);
    executingStepIndexRef.current = stepIndex;  //  同步更新 ref
    
    //  清空之前的结果
    setStepResults(prev => {
      const newResults = { ...prev };
      delete newResults[stepIndex];
      return newResults;
    });
    
    try {
      const step = steps[stepIndex];
      const previousContextId = stepIndex > 0 ? stepContextIds[stepIndex - 1] : null;
      
      // 替换代码中的占位符
      let code = step.code;
      if (currentSandbox?.cdp_url) {
        code = code.replace('{{CDP_URL}}', currentSandbox.cdp_url);
      }
      
      // 调用执行 API
      const response = await axios.post('/api/chat/execute', {
        session_id: currentSession.session_id,
        message_id: `playground_${selectedExample?.id}_${Date.now()}`,
        code: code,
        language: step.language,  //  传递语言类型
        context_id: previousContextId
      });
      
      if (response.data) {
        // 保存当前步骤的 context_id
        const contextId = response.data.context_id || response.data.execution_id;
        setStepContextIds(prev => ({
          ...prev,
          [stepIndex]: contextId
        }));
      
        //  初始状态：执行中（等待 WebSocket 结果）
        console.log('执行已启动，等待 WebSocket 结果...');
      }
    } catch (error) {
      console.error('Execute step failed:', error);
      
      //  保存错误结果
      setStepResults(prev => ({
        ...prev,
        [stepIndex]: {
          status: 'error',
          error: error instanceof Error ? error.message : '未知错误',
          timestamp: Date.now()
        }
      }));
      
      alert(`执行失败: ${error instanceof Error ? error.message : '未知错误'}`);
      setExecutingStepIndex(null);
    }
  };
  
  if (!currentSession) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6 py-8 bg-background">
        <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-primary/40 flex items-center justify-center mb-4 shadow-lg">
          <Code2 className="w-8 h-8 text-primary" />
        </div>
        <h3 className="text-lg font-semibold mb-2 text-foreground">代码编辑器</h3>
        <p className="text-muted-foreground max-w-md text-sm mb-4">
          请先创建或选择一个会话，每个会话都有独立的代码执行环境
        </p>
        <div className="text-xs text-muted-foreground/70 bg-muted/30 p-3 rounded-lg max-w-lg space-y-1.5">
          <p className="font-medium flex items-center gap-1.5">
            <span>[提示]</span>
            <span>提示</span>
          </p>
          <p>• 点击下方"新建会话"按钮创建新会话</p>
          <p>• Playground 支持多步骤代码执行</p>
          <p>• 每个步骤可以独立编辑和运行</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="flex flex-col h-full bg-background overflow-hidden">
      {/* 使用单一手风琴控制整个布局 */}
      <Accordion 
        type="single" 
        collapsible 
        value={activeSection}
        onValueChange={(value) => setActiveSection(value || '')}
        className="flex flex-col h-full overflow-hidden"
      >
        {/* 顶部：示例列表（手风琴） */}
        <AccordionItem value="examples" className="border-b border-border bg-card/30 flex-shrink-0">
          <AccordionTrigger className="px-3 py-3 hover:no-underline hover:bg-muted/30">
            <div className="flex items-center justify-between w-full pr-2">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-primary" />
                <div className="text-left">
                  <h3 className="text-sm font-semibold text-foreground">Playground 代码示例</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">选择一个示例开始多步骤编程</p>
                </div>
              </div>
              {selectedExample && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground mr-2">
                  <span>会话: {currentSession.session_id.slice(-8)}</span>
                  {currentSession.sandbox_id && (
                    <>
                      <span>•</span>
                      <span>Sandbox: {currentSession.sandbox_id.slice(0, 8)}...</span>
                    </>
                  )}
                </div>
              )}
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <ScrollArea className="w-full max-h-[300px]">
              <div className="px-3 pb-3 flex gap-3 min-w-max">
                {playgroundExamples.map((example) => (
                  <button
                    key={example.id}
                    onClick={() => {
                      selectExample(example);
                      // 选择示例后，切换到步骤视图
                      setActiveSection('steps');
                    }}
                    className={`flex-shrink-0 w-64 text-left p-3 rounded-lg transition-all ${
                      selectedExample?.id === example.id
                        ? 'bg-primary/10 border-primary/50 border-2 shadow-md'
                        : 'bg-card hover:bg-accent border border-border hover:shadow-sm'
                    }`}
                  >
                    <div className="font-medium text-sm text-foreground mb-1.5 flex items-center gap-2">
                      <Code2 className="w-4 h-4 text-primary" />
                      {example.title}
                    </div>
                    <div className="text-xs text-muted-foreground line-clamp-2 mb-2">
                      {example.description}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-0.5 rounded">
                        {example.steps.length} 个步骤
                      </span>
                      {selectedExample?.id === example.id && (
                        <span className="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          已选择
                        </span>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </AccordionContent>
        </AccordionItem>
        
        {/* 下方：具体示例步骤（手风琴） */}
        {selectedExample && (
          <AccordionItem value="steps" className="flex-1 flex flex-col border-none" style={{ minHeight: 0 }}>
            <AccordionTrigger className="px-3 py-3 border-b border-border bg-card/20 hover:no-underline hover:bg-muted/30 flex-shrink-0">
              <div className="flex items-center gap-2 w-full pr-2">
                <ChevronRight className="w-4 h-4 text-primary" />
                <div className="text-left flex-1">
                  <h3 className="text-sm font-semibold text-foreground">{selectedExample.title}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{selectedExample.description}</p>
                </div>
                <span className="text-xs font-medium text-primary bg-primary/10 px-2 py-1 rounded">
                  {selectedExample.steps.length} 个步骤
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="flex-1 p-0" style={{ minHeight: 0 }}>
              <div className="h-full overflow-y-auto" style={{ maxHeight: 'calc(100vh - 250px)' }}>
                <div className="p-4">
                <Accordion type="multiple" defaultValue={steps.map((_, i) => `step-${i}`)} className="space-y-4">
                  {steps.map((step, stepIndex) => (
                    <AccordionItem 
                      key={stepIndex} 
                      value={`step-${stepIndex}`}
                      className="bg-card border border-border rounded-lg overflow-hidden hover:shadow-md transition-shadow"
                    >
                      {/* 步骤标题 - 手风琴触发器 */}
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 px-4 py-3 bg-muted/30">
                        <AccordionTrigger className="flex-1 hover:no-underline py-0">
                          <div className="flex items-start gap-3 flex-1 min-w-0 pr-2">
                            <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold shadow-sm ${
                              completedSteps.has(stepIndex)
                                ? 'bg-green-500 text-white'
                                : 'bg-primary text-primary-foreground'
                            }`}>
                              {completedSteps.has(stepIndex) ? <Check className="w-4 h-4" /> : stepIndex + 1}
                            </div>
                            <div className="flex-1 min-w-0 text-left">
                              <div className="font-semibold text-sm text-foreground">
                                {step.title}
                              </div>
                              {step.description && (
                                <div className="text-xs text-muted-foreground mt-1 line-clamp-2">
                                  {step.description}
                                </div>
                              )}
                            </div>
                          </div>
                        </AccordionTrigger>
                        <div className="flex gap-2 flex-shrink-0 sm:ml-auto pl-4 sm:pl-0">
                          {editingStepIndex === stepIndex ? (
                            <>
                              <Button 
                                size="sm"
                                variant="outline" 
                                onClick={saveEdit}
                                className="h-8 gap-1.5 flex-1 sm:flex-initial"
                              >
                                <Save className="w-3.5 h-3.5" />
                                <span>保存</span>
                              </Button>
                              <Button
                                size="sm" 
                                variant="ghost"
                                onClick={cancelEdit}
                                className="h-8 px-3"
                              >
                                <X className="w-3.5 h-3.5" />
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button 
                                size="sm"
                                variant="outline" 
                                onClick={() => startEdit(stepIndex)}
                                className="h-8 gap-1.5 flex-1 sm:flex-initial"
                                disabled={executingStepIndex !== null}
                              >
                                <Edit3 className="w-3.5 h-3.5" />
                                <span>编辑</span>
                              </Button>
                              <Button 
                                size="sm"
                                onClick={() => executeStep(stepIndex)}
                                disabled={executingStepIndex !== null}
                                className="h-8 gap-1.5 bg-gradient-to-br from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white flex-1 sm:flex-initial"
                              >
                                {executingStepIndex === stepIndex ? (
                                  <>
                                    <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    <span>执行中...</span>
                                  </>
                                ) : completedSteps.has(stepIndex) ? (
                                  <>
                                    <Check className="w-3.5 h-3.5" />
                                    <span>已完成</span>
                                  </>
                                ) : (
                                  <>
                                    <Play className="w-3.5 h-3.5" />
                                    <span>运行</span>
                                  </>
                                )}
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
        
                      {/* 代码区域 - 手风琴内容 */}
                      <AccordionContent>
                        <div className="px-4 pb-4">
                          <div className="w-full">
                            {editingStepIndex === stepIndex ? (
                              //  编辑模式：使用 Monaco Editor
                              <div className="w-full border border-border rounded-lg overflow-hidden">
                                <Editor
                                  height="300px"
                                  language={step.language === 'shell' ? 'shell' : step.language}
                                  value={editedCode}
                                  onChange={(value) => setEditedCode(value || '')}
                                  theme={theme === 'dark' ? 'vs-dark' : 'light'}
                                  options={{
                                    minimap: { enabled: false },
                                    fontSize: 13,
                                    lineNumbers: 'on',
                                    scrollBeyondLastLine: false,
                                    automaticLayout: true,
                                    tabSize: 2,
                                    wordWrap: 'on',
                                  }}
                                />
                              </div>
                            ) : (
                              //  显示模式：使用 Syntax Highlighter
                              <div className="w-full rounded-lg border border-border overflow-hidden">
                                <div className="overflow-x-auto max-w-full">
                                  <SyntaxHighlighter
                                    language={step.language === 'shell' ? 'bash' : step.language}
                                    style={theme === 'dark' ? oneDark : oneLight}
                                    customStyle={{
                                      margin: 0,
                                      padding: '16px',
                                      fontSize: '13px',
                                      lineHeight: '1.6',
                                      borderRadius: 0,
                                      border: 'none',
                                      backgroundColor: theme === 'dark' ? '#1e1e1e' : '#fafafa',
                                      maxWidth: '100%',
                                      overflowX: 'auto',
                                    }}
                                    codeTagProps={{
                                      style: {
                                        fontFamily: 'ui-monospace, SFMono-Regular, SF Mono, Consolas, Liberation Mono, Menlo, monospace',
                                        wordBreak: 'break-word',
                                        whiteSpace: 'pre-wrap',
                                      }
                                    }}
                                    showLineNumbers={true}
                                    wrapLongLines={true}
                                    lineNumberStyle={{
                                      minWidth: '3em',
                                      paddingRight: '1em',
                                      color: theme === 'dark' ? '#858585' : '#999',
                                      opacity: 0.6,
                                      userSelect: 'none',
                                    }}
                                  >
                                    {step.code}
                                  </SyntaxHighlighter>
                                </div>
                              </div>
                            )}
                          </div>
                          <div className="mt-3 text-xs text-muted-foreground flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-3">
                              <span className="flex items-center gap-1">
                                <Code2 className="w-3 h-3" />
                                {step.code.split('\n').length} 行代码
                              </span>
                            </div>
                            {stepContextIds[stepIndex] && (
                              <span className="flex items-center gap-1 bg-primary/10 px-2 py-1 rounded">
                                <ChevronRight className="w-3 h-3" />
                                Context: {stepContextIds[stepIndex].slice(0, 8)}...
                              </span>
                            )}
                          </div>
                          
                          {/*  执行结果显示区域 */}
                          {stepResults[stepIndex] && (
                            <div className="mt-4 rounded-lg border border-border overflow-hidden">
                              {/* 结果状态标题 */}
                              <div className={`px-4 py-2 flex items-center gap-2 text-sm font-medium ${
                                stepResults[stepIndex].status === 'success'
                                  ? 'bg-green-50 text-green-700 border-b border-green-200'
                                  : stepResults[stepIndex].status === 'failed'
                                  ? 'bg-yellow-50 text-yellow-700 border-b border-yellow-200'
                                  : 'bg-red-50 text-red-700 border-b border-red-200'
                              }`}>
                                {stepResults[stepIndex].status === 'success' && (
                                  <>
                                    <CheckCircle2 className="w-4 h-4" />
                                    <span>执行成功</span>
                                  </>
                                )}
                                {stepResults[stepIndex].status === 'failed' && (
                                  <>
                                    <AlertCircle className="w-4 h-4" />
                                    <span>执行失败</span>
                                  </>
                                )}
                                {stepResults[stepIndex].status === 'error' && (
                                  <>
                                    <XCircle className="w-4 h-4" />
                                    <span>执行错误</span>
                                  </>
                                )}
                                <span className="ml-auto text-xs text-muted-foreground">
                                  {new Date(stepResults[stepIndex].timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                              
                              {/* 输出内容 */}
                              <div className="bg-slate-950 text-slate-100 p-4 font-mono text-xs max-h-96 overflow-y-auto overflow-x-hidden">
                                {/* 标准输出 */}
                                {stepResults[stepIndex].stdout && (
                                  <div className="mb-3">
                                    <div className="flex items-center gap-2 text-green-400 mb-2">
                                      <Terminal className="w-3.5 h-3.5" />
                                      <span className="font-semibold">输出:</span>
                                    </div>
                                    <pre className="whitespace-pre-wrap break-words break-all text-slate-200">
                                      {stepResults[stepIndex].stdout}
                                    </pre>
                                  </div>
                                )}
                                
                                {/* 标准错误 */}
                                {stepResults[stepIndex].stderr && (
                                  <div className="mb-3">
                                    <div className="flex items-center gap-2 text-yellow-400 mb-2">
                                      <AlertCircle className="w-3.5 h-3.5" />
                                      <span className="font-semibold">警告:</span>
                                    </div>
                                    <pre className="whitespace-pre-wrap break-words break-all text-yellow-200">
                                      {stepResults[stepIndex].stderr}
                                    </pre>
                                  </div>
                                )}
                                
                                {/* 错误信息 */}
                                {stepResults[stepIndex].error && (
                                  <div>
                                    <div className="flex items-center gap-2 text-red-400 mb-2">
                                      <XCircle className="w-3.5 h-3.5" />
                                      <span className="font-semibold">错误:</span>
                                    </div>
                                    <pre className="whitespace-pre-wrap break-words break-all text-red-200">
                                      {stepResults[stepIndex].error}
                                    </pre>
                                  </div>
                                )}
                                
                                {/* 如果没有任何输出 */}
                                {!stepResults[stepIndex].stdout && 
                                 !stepResults[stepIndex].stderr && 
                                 !stepResults[stepIndex].error && (
                                  <div className="text-slate-400 italic">
                                    执行完成，无输出内容
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </div>
          </AccordionContent>
        </AccordionItem>
        )}
      </Accordion>
    </div>
  );
}
