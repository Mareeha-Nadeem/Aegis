import { useState } from 'react';
import './styles/root.css';
import './styles/main.css';
import BgCanvas from './components/BgCanvas';
import Page1 from './components/Page1';
import Page2 from './components/Page2';
import { useTheme } from './hooks/useTheme';
import { useStats } from './hooks/useStats';

export default function App() {
  const [page, setPage]        = useState(1);
  const { theme, toggleTheme } = useTheme();
  const stats                  = useStats();

  function handleLaunch() {
    setPage(2);
    setTimeout(() => {
      const p2 = document.getElementById('page2');
      if (p2) p2.scrollTop = 0;
    }, 50);
  }

  function handleBack() {
    setPage(1);
    setTimeout(() => {
      const p1 = document.getElementById('page1');
      if (p1) p1.scrollTop = 0;
    }, 50);
  }

  return (
    <>
      <BgCanvas theme={theme} />
      <div className={`pages-track${page === 2 ? ' show-page2' : ''}`} id="pagesTrack">
        <Page1 onLaunch={handleLaunch} onToggleTheme={toggleTheme} stats={stats} />
        <Page2 onBack={handleBack}    onToggleTheme={toggleTheme} stats={stats} />
      </div>
    </>
  );
}
