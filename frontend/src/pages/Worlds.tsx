import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';

const WorldsList = lazy(() => import('./WorldsList'));
const WorldDetail = lazy(() => import('./WorldDetail'));
const WorldDm = lazy(() => import('./WorldDm'));
const CreateWorld = lazy(() => import('./CreateWorld'));

const Worlds = () => {
  return (
    <div className="worlds-container page-enter">
      <Suspense fallback={<div className="loading-state" role="status">Loading worlds...</div>}>
        <Routes>
          <Route path="/" element={<WorldsList />} />
          <Route path="/new" element={<CreateWorld />} />
          <Route path="/:id/dm" element={<WorldDm />} />
          <Route path="/:id" element={<WorldDetail />} />
        </Routes>
      </Suspense>
    </div>
  );
};

export default Worlds;
