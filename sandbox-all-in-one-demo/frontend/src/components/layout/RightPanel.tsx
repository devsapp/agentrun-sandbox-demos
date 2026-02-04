import { useState } from 'react';
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from '@/components/ui/resizable';
import { LogViewer } from '@/components/playground/LogViewer';
import { VNCViewer } from '@/components/playground/VNCViewer';

export function RightPanel() {
  const [isLogCollapsed, setIsLogCollapsed] = useState(false);

  return (
    <div className="flex flex-col h-full">
      {!isLogCollapsed ? (
        <ResizablePanelGroup orientation="vertical">
          {/* VNC 查看器面板 */}
          <ResizablePanel maxSize={80}>
            <VNCViewer />
          </ResizablePanel>

          {/* 可调整大小的分隔条 */}
          <ResizableHandle className="h-1 bg-border hover:bg-primary/50 transition-colors cursor-row-resize active:bg-primary" />

          {/* 执行日志面板 */}
          <ResizablePanel defaultSize={15} minSize={20} maxSize={50}>
            <LogViewer 
              isCollapsed={false}
              onToggleCollapse={() => setIsLogCollapsed(true)}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      ) : (
        // 日志折叠时
        <div className="flex flex-col h-full">
          {/* VNC 占据主要区域 */}
          <div className="flex-1 overflow-hidden">
            <VNCViewer />
          </div>

          {/* 底部的日志工具栏（折叠状态） */}
          <LogViewer 
            isCollapsed={true}
            onToggleCollapse={() => setIsLogCollapsed(false)}
          />
        </div>
      )}
    </div>
  );
}
