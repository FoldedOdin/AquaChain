import { useState, useEffect, useRef } from 'react';

interface MaintenanceStatus {
  enabled: boolean;
  message: string;
  allowedRoles: string[];
}

const API_BASE_URL = process.env.REACT_APP_API_ENDPOINT || '';
const POLL_INTERVAL_MS = 60_000; // re-check every 60 seconds

export function useMaintenanceMode(userRole: string | undefined) {
  const [status, setStatus] = useState<MaintenanceStatus>({
    enabled: false,
    message: '',
    allowedRoles: ['admin', 'administrator'],
  });
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/system/maintenance`);
      if (!res.ok) return;
      const data: MaintenanceStatus = await res.json();
      setStatus(data);
    } catch {
      // Fail open — don't block users if the endpoint is unreachable
    }
  };

  useEffect(() => {
    fetchStatus();
    timerRef.current = setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const isBlocked =
    status.enabled &&
    !!userRole &&
    !status.allowedRoles.some(
      (r) => r.toLowerCase().replace(/s$/, '') === userRole.toLowerCase().replace(/s$/, '')
    );

  return { isBlocked, message: status.message, status };
}
