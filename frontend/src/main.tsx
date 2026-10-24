import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import App from './App'
import { AboutPage } from './pages/AboutPage'
import { IngredientsPage } from './pages/IngredientsPage'
import { MethodologyPage } from './pages/MethodologyPage'
import { StressTestPage } from './pages/StressTestPage'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/ingredients" element={<IngredientsPage />} />
        <Route path="/stress-test" element={<StressTestPage />} />
        <Route path="/methodology" element={<MethodologyPage />} />
        <Route path="/about" element={<AboutPage />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
