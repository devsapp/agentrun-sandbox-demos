import Split from 'react-split';
import { LeftPanel } from '@/components/layout/LeftPanel';
import { RightPanel } from '@/components/layout/RightPanel';
import { useUIStore } from '@/stores/uiStore';

export function ChatPage() {
  const { splitSizes, setSplitSizes } = useUIStore();
  
  return (
    <Split
      sizes={splitSizes}
      minSize={[400, 400]}
      gutterSize={6}
      onDragEnd={(sizes) => setSplitSizes(sizes as [number, number])}
      className="flex h-full"
      style={{ display: 'flex' }}
    >
      <div className="overflow-hidden">
        <LeftPanel />
      </div>
      <div className="overflow-hidden">
        <RightPanel />
      </div>
    </Split>
  );
}
