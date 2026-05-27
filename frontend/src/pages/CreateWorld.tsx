import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { createWorld } from '../lib/api';
import './CreateWorld.css';

const CreateWorld = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [formData, setFormData] = useState({
    title: '',
    tone: '',
    era_notes: '',
    seed: ''
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMessage('');
    try {
      const result = await createWorld({
        title: formData.title,
        tone: formData.tone || null,
        era_notes: formData.era_notes || null,
        seed: formData.seed || null,
      });
      navigate(`/worlds/${result.id}`);
    } catch (err) {
      console.error(err);
      setErrorMessage('Unable to create this world. Review the form and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="create-world-container">
      <div className="create-header">
        <h1>Forge a New World</h1>
        <p className="text-secondary">Define the foundational properties of your universe.</p>
      </div>

      {errorMessage && (
        <div className="workspace-alert error" role="alert">
          {errorMessage}
        </div>
      )}

      <form className="glass create-form" onSubmit={handleSubmit} aria-describedby="create-world-help">
        <p id="create-world-help" className="form-help">Required fields are marked with an asterisk.</p>
        <div className="form-group">
          <label htmlFor="title">World Title <span className="required">*</span></label>
          <input 
            type="text" 
            id="title" 
            name="title" 
            value={formData.title} 
            onChange={handleChange} 
            placeholder="e.g., The Ashen Wastes, Chronos Prime" 
            required 
            aria-required="true"
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="tone">Tone</label>
          <input 
            type="text" 
            id="tone" 
            name="tone" 
            value={formData.tone} 
            onChange={handleChange} 
            placeholder="e.g., Grimdark, High Fantasy, Cyberpunk noir" 
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="era_notes">Era Notes</label>
          <textarea 
            id="era_notes" 
            name="era_notes" 
            value={formData.era_notes} 
            onChange={handleChange} 
            placeholder="Describe the current state of the world, major events, or historical context..." 
            rows={5}
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="seed">Seed</label>
          <input 
            type="text" 
            id="seed" 
            name="seed" 
            value={formData.seed} 
            onChange={handleChange} 
            placeholder="Random seed or specific prompt seed for generation" 
            className="form-input"
          />
        </div>

        <div className="form-actions">
          <button type="button" className="btn btn-secondary" onClick={() => navigate('/worlds')}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={loading || !formData.title}>
            {loading ? 'Forging...' : 'Create World'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateWorld;
