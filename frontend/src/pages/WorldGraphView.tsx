import { useEffect } from 'react';
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
  type Edge,
  type Node,
  type NodeProps,
  type NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import type { EntityGraphNode, RelationshipGraphEdge } from '../lib/worldGraph';

interface WorldGraphViewProps {
  nodes: EntityGraphNode[];
  edges: RelationshipGraphEdge[];
  onSelectEntity: (entityId: string) => void;
  onSelectRelationship: (relationshipId: string) => void;
  onPositionsChange: (positions: Record<string, { x: number; y: number }>) => void;
  resetKey: number;
}

const EntityNode = ({ data }: NodeProps<EntityGraphNode>) => (
  <div className="entity-graph-node-content">
    <Handle type="target" position={Position.Left} />
    <strong>{data.label}</strong>
    <span>{data.entityType} · {data.relationshipCount} links</span>
    <Handle type="source" position={Position.Right} />
  </div>
);

const nodeTypes: NodeTypes = {
  entity: EntityNode,
};

const WorldGraphView = ({
  nodes,
  edges,
  onSelectEntity,
  onSelectRelationship,
  onPositionsChange,
  resetKey,
}: WorldGraphViewProps) => {
  const [flowNodes, setNodes, onNodesChange] = useNodesState<Node>(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState<Edge>(edges);

  useEffect(() => {
    setNodes(nodes);
  }, [nodes, resetKey, setNodes]);

  useEffect(() => {
    setEdges(edges);
  }, [edges, setEdges]);

  if (nodes.length === 0) {
    return (
      <div className="graph-empty-state" role="status">
        <h3>No entities yet</h3>
        <p className="text-muted">Create entities in the editor to populate the graph.</p>
      </div>
    );
  }

  return (
    <ReactFlow
      aria-label="Supplemental visual world graph. Use the accessible graph summary below for keyboard selection."
      nodes={flowNodes}
      edges={flowEdges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={(_, node) => onSelectEntity(node.id)}
      onEdgeClick={(_, edge) => onSelectRelationship(edge.id)}
      onNodeDragStop={(_, node) => {
        const nextPositions = Object.fromEntries(
          flowNodes
            .map((flowNode) => (
              flowNode.id === node.id
                ? { ...flowNode, position: node.position }
                : flowNode
            ))
            .map((flowNode) => [flowNode.id, flowNode.position]),
        );
        onPositionsChange(nextPositions);
      }}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.18 }}
      minZoom={0.25}
      maxZoom={1.8}
      nodesDraggable
      proOptions={{ hideAttribution: true }}
    >
      <Background color="rgba(148, 163, 184, 0.22)" gap={24} />
      <MiniMap
        pannable
        zoomable
        nodeColor={(node) => {
          if (node.className?.toString().includes('selected')) return '#3b82f6';
          if (node.className?.toString().includes('highlighted')) return '#ec4899';
          return '#7c3aed';
        }}
      />
      <Controls />
    </ReactFlow>
  );
};

export default WorldGraphView;
