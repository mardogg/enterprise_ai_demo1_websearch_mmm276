import React from 'react';
import { createRoot } from 'react-dom/client';
import './index.css'; // Tailwind directives only
import AITechAssistant from './components/AITechAssistant';

createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <AITechAssistant />
  </React.StrictMode>
);
