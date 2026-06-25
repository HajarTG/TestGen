import { useState, useEffect, useCallback } from 'react';
import { api } from './client';

export function useFetch(fetchFn, autoExecute = true) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(autoExecute);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchFn(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err.message || 'Something went wrong');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    if (autoExecute) {
      const timer = setTimeout(() => {
        execute();
      }, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [autoExecute, execute]);

  return { data, loading, error, execute, setData };
}

export function useRuns(page = 1, perPage = 20) {
  const fetchFn = useCallback(async () => {
    const res = await api.getRuns(page, perPage);
    return res.runs || [];
  }, [page, perPage]);
  return useFetch(fetchFn);
}

export function usePaginatedRuns(page = 1, perPage = 20) {
  const fetchFn = useCallback(async () => {
    return await api.getRuns(page, perPage);
  }, [page, perPage]);
  return useFetch(fetchFn);
}

export function useRunDetails(runId) {
  const fetchRun = useCallback(() => api.getRun(runId), [runId]);
  const fetchReports = useCallback(async () => {
    const res = await api.getReports(runId);
    return res.reports || [];
  }, [runId]);
  const fetchMetrics = useCallback(() => api.getMetrics(runId), [runId]);

  const [run, setRun] = useState(null);
  const [reports, setReports] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadAll = useCallback(async () => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    try {
      const [runData, reportsData, metricsData] = await Promise.all([
        fetchRun(),
        fetchReports(),
        fetchMetrics().catch(() => null), // metrics might not exist yet if run is not completed
      ]);
      setRun(runData);
      setReports(reportsData);
      setMetrics(metricsData);
    } catch (err) {
      setError(err.message || 'Failed to load run details');
    } finally {
      setLoading(false);
    }
  }, [runId, fetchRun, fetchReports, fetchMetrics]);

  useEffect(() => {
    const timer = setTimeout(() => {
      loadAll();
    }, 0);
    return () => clearTimeout(timer);
  }, [loadAll]);

  return { run, reports, metrics, loading, error, refetch: loadAll };
}

export function useGlobalStats() {
  const fetchFn = useCallback(() => api.getGlobalMetrics(), []);
  return useFetch(fetchFn);
}

export function useHealth(pollIntervalMs = 15000) {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const check = async () => {
      try {
        const h = await api.getHealth();
        if (active) setHealth(h);
      } catch (err) {
        if (active) setHealth({ status: 'unhealthy', error: err.message });
      } finally {
        if (active) setLoading(false);
      }
    };

    check();
    const timer = setInterval(check, pollIntervalMs);

    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [pollIntervalMs]);

  return { health, loading };
}
