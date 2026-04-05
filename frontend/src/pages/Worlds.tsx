import { Routes, Route } from 'react-router-dom';
import WorldsList from './WorldsList';
import WorldDetail from './WorldDetail';
import CreateWorld from './CreateWorld';

const Worlds = () => {
  return (
    <div className="worlds-container page-enter">
      <Routes>
        <Route path="/" element={<WorldsList />} />
        <Route path="/new" element={<CreateWorld />} />
        <Route path="/:id" element={<WorldDetail />} />
      </Routes>
    </div>
  );
};

export default Worlds;
