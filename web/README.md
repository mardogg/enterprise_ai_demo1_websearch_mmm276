# AI Tech Assistant Web (Vite + React + Tailwind)

Development scaffold providing a standalone front-end for the AI Tech Assistant workflow.

## Quick Start

```powershell
cd web
npm install
npm run dev
```

Open http://localhost:5173

## Structure
- `src/components/AITechAssistant.tsx` – React component wrapper importing the main logic from the project root `src/AITechAssistant.tsx`.
- `src/main.tsx` – App entry mounting the assistant.
- `tailwind.config.ts` + `postcss.config.js` – Tailwind setup.

## Customization
Replace stub functions in `src/AITechAssistant.tsx` (root project) `generatePlan` and `searchYoutube` with real API calls.

## Build
```powershell
npm run build
npm run preview
```

## Notes
- Tailwind JIT will tree-shake unused classes in production build.
- Keep accessibility: form inputs have labels, dynamic regions use `aria-live`.
