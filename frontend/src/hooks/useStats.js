import { useState, useCallback } from 'react';

export function useStats() {
  const [blockedCount, setBlockedCount] = useState(0);
  const [queryCount, setQueryCount]     = useState(0);
  const [riskLevel, setRiskLevel]       = useState('LOW');

  const incrementQuery   = useCallback(() => setQueryCount(c => c + 1), []);
  const incrementBlocked = useCallback(() => {
    setBlockedCount(c => {
      const next = c + 1;
      if (next >= 5) setRiskLevel('HIGH');
      else if (next >= 2) setRiskLevel('MEDIUM');
      return next;
    });
  }, []);

  return { blockedCount, queryCount, riskLevel, incrementQuery, incrementBlocked };
}
