import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { CodeEditor } from '@/components/playground/CodeEditor';
import { Terminal } from '@/components/playground/Terminal';
import { MessageSquare, Code2, Terminal as TerminalIcon } from 'lucide-react';
import { useUIStore } from '@/stores/uiStore';

export function LeftPanel() {
  const { activeLeftTab, setActiveLeftTab } = useUIStore();
  
  return (
    <Tabs 
      value={activeLeftTab} 
      onValueChange={(v) => setActiveLeftTab(v as 'chat' | 'playground' | 'terminal')} 
      className="flex flex-col h-full"
    >
      <div className="border-b border-border bg-card/30 backdrop-blur-sm px-3">
        <TabsList className="w-full h-11 bg-transparent p-0 gap-1 rounded-none">
          <TabsTrigger 
            value="chat" 
            className="flex-1 h-full text-sm font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary transition-all"
          >
            <MessageSquare className="w-4 h-4 mr-2" />
            对话
          </TabsTrigger>
          <TabsTrigger 
            value="playground" 
            className="flex-1 h-full text-sm font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary transition-all"
          >
            <Code2 className="w-4 h-4 mr-2" />
            Playground
          </TabsTrigger>
          <TabsTrigger 
            value="terminal" 
            className="flex-1 h-full text-sm font-medium data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm rounded-b-none border-b-2 border-transparent data-[state=active]:border-primary transition-all"
          >
            <TerminalIcon className="w-4 h-4 mr-2" />
            终端
          </TabsTrigger>
        </TabsList>
      </div>
      
      <TabsContent value="chat" className="flex-1 overflow-hidden m-0 p-0 data-[state=active]:flex data-[state=active]:flex-col">
        <ChatPanel />
      </TabsContent>
      
      <TabsContent value="playground" className="flex-1 overflow-hidden m-0 p-0 data-[state=active]:flex data-[state=active]:flex-col">
        <CodeEditor />
      </TabsContent>
      
      <TabsContent value="terminal" className="flex-1 overflow-hidden m-0 p-0 data-[state=active]:flex data-[state=active]:flex-col">
        <Terminal />
      </TabsContent>
    </Tabs>
  );
}
