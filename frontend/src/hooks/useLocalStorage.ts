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

// Helper interface for TTL storage
interface StorageItem<T> {
  data: T;
  timestamp: number;
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
        if (options?.ttl) {
          // Check if parsed object fits StorageItem shape
          if (parsed && typeof parsed === 'object' && 'timestamp' in parsed && 'data' in parsed) {
            const storageItem = parsed as StorageItem<T>; // Safe cast after check
            const now = Date.now();

            if (now - storageItem.timestamp > options.ttl) {
              // Item has expired, remove it
              window.localStorage.removeItem(key);
              setStoredValue(initialValue);
            } else {
              // Item is still valid
              setStoredValue(storageItem.data);
            }
          } else {
            // If structure doesn't match expected TTL format but TTL requested, fall back or treat as invalid
            // Here assuming if TTL is set, we strictly expect StorageItem
            setStoredValue(initialValue);
          }
        } else {
          // No TTL, just use the parsed value
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

        let finalValueToStore: T | StorageItem<T> = valueToStore;

        // Add timestamp if TTL is specified
        if (options?.ttl) {
          finalValueToStore = {
            data: valueToStore,
            timestamp: Date.now(),
          };
        }

        window.localStorage.setItem(key, serialize(finalValueToStore as T));
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
  return useLocalStorage(
    'recent-searches',
    [] as Array<{
      summonerName: string;
      region: string;
      timestamp: number;
    }>,
    {
      ttl: 7 * 24 * 60 * 60 * 1000, // 7 days
    }
  );
};
