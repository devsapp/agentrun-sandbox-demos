import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Play, Loader2, CheckCircle2, XCircle, Edit3, Save, X } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { apiClient, WS_BASE_URL } from '@/lib/api/client';
import { useUIStore } from '@/stores/uiStore';
import { Editor } from '@monaco-editor/react';

interface ExecutableCodeBlockProps {
  code: string;
  language: string;
  stepTitle?: string;
  sessionId: string;
  messageId: string;
}

export function ExecutableCodeBlock({ 
  code: initialCode, 
  language, 
  stepTitle, 
  sessionId,
  messageId 
}: ExecutableCodeBlockProps) {
  const { theme } = useUIStore();
  const [code, setCode] = useState(initialCode);
  const [isEditing, setIsEditing] = useState(false);
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<{
    status: 'success' | 'failed';
    stdout?: string;
    stderr?: string;
    error?: string;
  } | null>(null);
  const currentExecutionIdRef = useRef<string | null>(null);

  // 监听 WebSocket 接收执行结果
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${sessionId}`);
    
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        
        // 处理执行完成消息
        if (message.type === 'execution_complete') {
          const { execution_id, status, result } = message.data;
          
          // 检查是否是当前代码块的执行结果
          if (currentExecutionIdRef.current === execution_id) {
            setIsExecuting(false);
            
            setExecutionResult({
              status: status === 'success' ? 'success' : 'failed',
              stdout: result?.stdout || '',
              stderr: result?.stderr || '',
              error: result?.error || message.data.error,
            });
            
            currentExecutionIdRef.current = null;
          }
        }
      } catch (error) {
        console.error('解析 WebSocket 消息失败:', error);
      }
    };
    
    return () => {
      ws.close();
    };
  }, [sessionId]);

  const handleExecute = async () => {
    setIsExecuting(true);
    setExecutionResult(null);

    try {
      // 映射 language 到后端支持的类型
      let mappedLanguage: 'javascript' | 'shell' | 'python' = 'javascript';
      
      if (language === 'bash' || language === 'sh' || isShellCommand) {
        mappedLanguage = 'shell';
      } else if (language === 'javascript' || language === 'js' || language === 'typescript' || language === 'ts') {
        mappedLanguage = 'javascript';
      } else if (language === 'python' || language === 'py') {
        mappedLanguage = 'python';
      }

      // 调用后端执行代码
      const response = await apiClient.post('/api/chat/execute', {
        session_id: sessionId,
        message_id: messageId,
        code: code,
        language: mappedLanguage,
        context_id: null,
      });

      // 保存执行 ID 用于匹配结果
      if (response.data?.execution_id) {
        currentExecutionIdRef.current = response.data.execution_id;
      }
    } catch (error: any) {
      setExecutionResult({
        status: 'failed',
        error: error.message || '执行失败',
      });
      setIsExecuting(false);
    }
  };

  // 判断是否是 shell 命令
  const isShellCommand = code.trim().startsWith('pip ') || 
                         code.trim().startsWith('apt-get ') ||
                         code.trim().startsWith('npm ') ||
                         code.trim().startsWith('git ');

  return (
    <Card className="my-3 overflow-hidden border-border/50 bg-card/30">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-muted/30 border-b border-border/50">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted-foreground">
            {stepTitle || (isShellCommand ? 'Shell 命令' : `${language} 代码`)}
          </span>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button
                onClick={() => setIsEditing(false)}
                size="sm"
                variant="outline"
                className="h-6 px-2 text-xs"
              >
                <Save className="w-3 h-3 mr-1" />
                保存
              </Button>
              <Button
                onClick={() => {
                  setCode(initialCode);
                  setIsEditing(false);
                }}
                size="sm"
                variant="ghost"
                className="h-6 px-2 text-xs"
              >
                <X className="w-3 h-3" />
              </Button>
            </>
          ) : (
            <>
              <Button
                onClick={() => setIsEditing(true)}
                size="sm"
                variant="outline"
                disabled={isExecuting}
                className="h-6 px-2 text-xs"
              >
                <Edit3 className="w-3 h-3 mr-1" />
                编辑
              </Button>
              <Button
                onClick={handleExecute}
                disabled={isExecuting}
                size="sm"
                className="h-6 px-2 text-xs bg-gradient-to-br from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white border-0"
              >
                {isExecuting ? (
                  <>
                    <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                    执行中...
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 mr-1" />
                    执行
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Code Editor */}
      <div className="border-b border-border/50">
        {isShellCommand ? (
          <div className="p-3 font-mono text-xs bg-black/20">
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              disabled={!isEditing}
              className={`w-full bg-transparent border-none outline-none ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              } ${!isEditing ? 'cursor-default' : ''}`}
            />
          </div>
        ) : (
          <Editor
            height="200px"
            language={language}
            value={code}
            onChange={(value) => setCode(value || '')}
            theme={theme === 'dark' ? 'vs-dark' : 'light'}
            options={{
              minimap: { enabled: false },
              fontSize: 12,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 4,
              readOnly: !isEditing,  //  根据编辑状态控制只读
            }}
          />
        )}
      </div>

      {/* Execution Result */}
      {executionResult && (
        <div className={`px-3 py-2 text-xs ${
          executionResult.status === 'success' 
            ? 'bg-emerald-500/10 text-emerald-400 border-t border-emerald-500/20' 
            : 'bg-red-500/10 text-red-400 border-t border-red-500/20'
        }`}>
          <div className="flex items-start gap-2">
            {executionResult.status === 'success' ? (
              <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
            ) : (
              <XCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            )}
            <div className="flex-1 space-y-2">
              <div className="font-medium">
                {executionResult.status === 'success' ? '执行成功' : '执行失败'}
              </div>
              {executionResult.stdout && (
                <div>
                  <div className="text-[10px] opacity-60 mb-1">标准输出:</div>
                  <pre className="whitespace-pre-wrap font-mono text-[11px] opacity-90 bg-black/20 p-2 rounded">
                    {executionResult.stdout}
                  </pre>
                </div>
              )}
              {executionResult.stderr && (
                <div>
                  <div className="text-[10px] opacity-60 mb-1">标准错误:</div>
                  <pre className="whitespace-pre-wrap font-mono text-[11px] opacity-90 text-amber-400 bg-black/20 p-2 rounded">
                    {executionResult.stderr}
                  </pre>
                </div>
              )}
              {executionResult.error && (
                <div>
                  <div className="text-[10px] opacity-60 mb-1">错误信息:</div>
                  <pre className="whitespace-pre-wrap font-mono text-[11px] opacity-90 bg-black/20 p-2 rounded">
                    {executionResult.error}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
