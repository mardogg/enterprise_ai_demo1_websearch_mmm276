import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css'; // Tailwind directives only
import App from './App';

createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
