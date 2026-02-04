import { useParams } from 'react-router-dom';

export function ViewerPage() {
  const { sandboxId } = useParams();
  
  return (
    <div className="flex items-center justify-center h-full">
      <h1 className="text-2xl font-bold">Sandbox Viewer: {sandboxId}</h1>
    </div>
  );
}
