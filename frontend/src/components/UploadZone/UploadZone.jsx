import { useState, useRef } from 'react';
import { Upload, FileCode, Play, AlertCircle } from 'lucide-react';
import { api } from '../../api/client';
import './UploadZone.css';

export default function UploadZone({ onUploadSuccess }) {
  const [file, setFile] = useState(null);
  const [strategy, setStrategy] = useState('unit_test');
  const [model, setModel] = useState('gpt-4o');
  const [customPrompt, setCustomPrompt] = useState('');
  const [temperature, setTemperature] = useState(0.2);
  
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const handleDragLeave = () => {
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.name.endsWith('.java') || droppedFile.name.endsWith('.zip')) {
        setFile(droppedFile);
        setError(null);
      } else {
        setError('Please select a valid .java file or a .zip archive of a Java project.');
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const triggerFileInput = () => {
    fileInputRef.current.click();
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('strategy', strategy);
    formData.append('model', model);
    formData.append('custom_prompt', customPrompt);
    formData.append('temperature', temperature.toString());

    try {
      const run = await api.uploadFiles(formData);
      setFile(null);
      setCustomPrompt('');
      if (onUploadSuccess) {
        onUploadSuccess(run);
      }
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-card">
      <h2 style={{ marginTop: 0, marginBottom: '1.5rem', fontSize: '1.25rem', fontWeight: 700 }}>
        Generate JUnit Tests
      </h2>

      <form onSubmit={handleSubmit}>
        {/* Dropzone Area */}
        <div
          className={`upload-area ${dragging ? 'dragging' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={triggerFileInput}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".java,.zip"
            style={{ display: 'none' }}
          />

          <div className="upload-icon">
            <Upload size={48} />
          </div>

          <div>
            <p style={{ margin: '0 0 0.25rem', fontWeight: 600 }}>
              Drag & drop your Java file or ZIP project
            </p>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
              Supports .java class files or structured .zip archives
            </p>
          </div>

          {file && (
            <div className="selected-file" onClick={(e) => e.stopPropagation()}>
              <FileCode size={16} />
              <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}
        </div>

        {error && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#ef4444', fontSize: '0.85rem', marginTop: '1rem' }}>
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Configuration Options */}
        <div className="config-grid">
          <div className="form-group">
            <label className="form-label">Generation Strategy</label>
            <select
              className="form-select"
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
            >
              <option value="unit_test">Standard Unit Test (JUnit 5)</option>
              <option value="integration_test">Integration Test (Spring Boot)</option>
              <option value="mock_heavy">Mock-Heavy (Mockito Isolation)</option>
              <option value="regression">Regression Assertions (Behavioral)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">AI Chat Model</label>
            <select
              className="form-select"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              <option value="gpt-4o">GPT-4o (Recommended)</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Temperature: {temperature}</label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              style={{ marginTop: '0.5rem' }}
            />
          </div>
        </div>

        <div className="form-group" style={{ marginBottom: '2rem' }}>
          <label className="form-label">Additional Instructions / System Prompt Context (Optional)</label>
          <textarea
            className="form-input"
            rows="3"
            placeholder="e.g. 'Use assertj assertions instead of standard JUnit assertNull. Focus on edge cases for null inputs.'"
            value={customPrompt}
            onChange={(e) => setCustomPrompt(e.target.value)}
            style={{ resize: 'vertical' }}
          />
        </div>

        <button
          type="submit"
          className="generate-btn"
          disabled={!file || uploading}
        >
          <Play size={18} fill="white" />
          <span>{uploading ? 'Processing & Queueing...' : 'Initiate Test Generation'}</span>
        </button>

        {uploading && (
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: '60%' }}></div>
          </div>
        )}
      </form>
    </div>
  );
}
