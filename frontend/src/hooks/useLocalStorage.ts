/**
 * React hook for managing localStorage with TypeScript support.
 * Provides caching for recap data and user preferences.
 */

import { useState, useEffect, useCallback } from 'react';

type SetValue<T> = T | ((val: T) => T);

interface UseLocalStorageReturn<T> {
  storedValue: T;
  setValue: (value: SetValue<T>) => void;
  removeValue: () => void;
  isLoading: boolean;
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options?: {
    serialize?: (value: T) => string;
    deserialize?: (value: string) => T;
    ttl?: number; // Time to live in milliseconds
  }
): UseLocalStorageReturn<T> {
  const [isLoading, setIsLoading] = useState(true);
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  const serialize = options?.serialize || JSON.stringify;
  const deserialize = options?.deserialize || JSON.parse;

  // Read from localStorage on mount
  useEffect(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        const parsed = deserialize(item);
        
        // Check TTL if provided
        if (options?.ttl && parsed && typeof parsed === 'object' && 'timestamp' in parsed) {
          const now = Date.now();
          const itemTime = (parsed as any).timestamp;
          
          if (now - itemTime > options.ttl) {
            // Item has expired, remove it
            window.localStorage.removeItem(key);
            setStoredValue(initialValue);
          } else {
            // Item is still valid, use the data
            setStoredValue((parsed as any).data);
          }
        } else {
          setStoredValue(parsed);
        }
      }
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      setStoredValue(initialValue);
    } finally {
      setIsLoading(false);
    }
  }, [key, initialValue, deserialize, options?.ttl]);

  const setValue = useCallback(
    (value: SetValue<T>) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);

        // Prepare data for storage
        let dataToStore: any = valueToStore;
        
        // Add timestamp if TTL is specified
        if (options?.ttl) {
          dataToStore = {
            data: valueToStore,
            timestamp: Date.now(),
          };
        }

        window.localStorage.setItem(key, serialize(dataToStore));
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, serialize, storedValue, options?.ttl]
  );

  const removeValue = useCallback(() => {
    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return {
    storedValue,
    setValue,
    removeValue,
    isLoading,
  };
}

// Specific hooks for common use cases
export const useRecapCache = () => {
  return useLocalStorage('recap-cache', null, {
    ttl: 24 * 60 * 60 * 1000, // 24 hours
  });
};

export const useUserPreferences = () => {
  return useLocalStorage('user-preferences', {
    theme: 'light',
    region: 'na1',
    lastSummonerName: '',
    showAnimations: true,
    autoSave: true,
  });
};

export const useRecentSearches = () => {
  return useLocalStorage('recent-searches', [] as Array<{
    summonerName: string;
    region: string;
    timestamp: number;
  }>, {
    ttl: 7 * 24 * 60 * 60 * 1000, // 7 days
  });
};