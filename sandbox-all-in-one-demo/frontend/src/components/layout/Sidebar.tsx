import { Button } from '@/components/ui/button';
import { useChatStore } from '@/stores/chatStore';
import { RefreshCw, Info } from 'lucide-react';
import { useState } from 'react';
import { toast } from 'sonner';

export function Sidebar() {
  const { currentSession, rebuildSession } = useChatStore();
  const [isRebuilding, setIsRebuilding] = useState(false);
  
  const handleRebuild = async () => {
    if (!confirm('确定要重建会话吗？\n\n这将：\n• 清空所有消息历史\n• 关闭当前 Sandbox\n• 创建新的 Sandbox\n\n此操作不可撤销！')) {
      return;
    }
    
    setIsRebuilding(true);
    try {
      await rebuildSession();
      toast.success('会话已重建', {
        description: '已创建新的 Sandbox，所有状态已重置'
      });
    } catch (error) {
      console.error('重建会话失败:', error);
      toast.error('重建会话失败', {
        description: error instanceof Error ? error.message : '未知错误'
      });
    } finally {
      setIsRebuilding(false);
    }
  };
  
  return (
    <aside className="w-56 border-r border-border/50 bg-card/20 flex flex-col h-full">
      {/* 顶部标题 */}
      <div className="p-3 border-b border-border/50">
        <h2 className="text-sm font-semibold text-foreground">全局会话</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          单一会话模式
        </p>
      </div>
      
      {/* 会话信息 */}
      <div className="flex-1 p-3">
        {currentSession ? (
          <div className="bg-secondary/30 rounded-lg p-3 space-y-3">
            <div className="flex items-start gap-2">
              <Info className="w-4 h-4 text-primary mt-0.5 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground mb-1">会话信息</p>
                <div className="space-y-1.5 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <span className="text-foreground/70">消息数:</span>
                    <span className="font-medium">{currentSession.messages.length}</span>
                  </div>
                  {currentSession.sandbox_id && (
                    <div className="flex items-start gap-1">
                      <span className="text-foreground/70 flex-shrink-0">Sandbox:</span>
                      <span className="font-mono text-[10px] break-all">
                        {currentSession.sandbox_id.slice(0, 12)}...
                      </span>
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <span className="text-foreground/70">创建时间:</span>
                    <span className="text-[10px]">
                      {new Date(currentSession.created_at).toLocaleString('zh-CN', {
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            {/* 说明文本 */}
            <div className="pt-2 border-t border-border/30">
              <p className="text-[10px] text-muted-foreground leading-relaxed">
                当前为全局单一会话模式。所有对话和代码执行共享同一个 Sandbox 环境。
              </p>
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground/60 text-xs py-8">
            <p>正在初始化会话...</p>
          </div>
        )}
      </div>
      
      {/* 底部 - 重建会话按钮 */}
      <div className="p-2.5 border-t border-border/50">
        <Button 
          onClick={handleRebuild} 
          disabled={isRebuilding || !currentSession}
          variant="outline"
          className="w-full text-xs h-9 border-border/50 hover:bg-accent/50"
        >
          {isRebuilding ? (
            <>
              <span className="inline-block w-3 h-3 border-2 border-primary/30 border-t-primary rounded-full animate-spin mr-2"></span>
              重建中...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-1.5" />
              重建会话
            </>
          )}
        </Button>
        <p className="text-[10px] text-muted-foreground/70 text-center mt-2 px-1">
          重建会话将清空历史并创建新 Sandbox
        </p>
      </div>
    </aside>
  );
}
