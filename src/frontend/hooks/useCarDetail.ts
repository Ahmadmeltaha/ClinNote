import { useState, useEffect } from 'react';
import { CarDetailResponse } from '@/api/validators/cars';
import type { z } from 'zod';

type CarDetailData = z.infer<typeof CarDetailResponse>;

export function useCarDetail(carId: string): {
  data: CarDetailData | null;
  loading: boolean;
  error: string | null;
} {
  const [data, setData] = useState<CarDetailData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchCar() {
      if (!cancelled) {
        setLoading(true);
        setError(null);
      }

      try {
        const res = await fetch(`/api/cars/${carId}`);

        if (res.status === 404) {
          if (!cancelled) {
            setError('Car not found.');
            setData(null);
            setLoading(false);
          }
          return;
        }

        if (!res.ok) {
          if (!cancelled) {
            setError('Failed to fetch car details.');
            setData(null);
            setLoading(false);
          }
          return;
        }

        const parsed: CarDetailData = await res.json();

        if (!cancelled) {
          setData(parsed);
          setLoading(false);
        }
      } catch {
        if (!cancelled) {
          setError('Network error. Please try again.');
          setData(null);
          setLoading(false);
        }
      }
    }

    fetchCar();

    return () => {
      cancelled = true;
    };
  }, [carId]);

  return { data, loading, error };
}

export { CarDetailResponse } from '@/api/validators/cars';