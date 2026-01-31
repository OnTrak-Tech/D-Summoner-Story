/**
 * Performance optimization hooks for better user experience.
 * Includes image lazy loading, component preloading, and resource management.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

// Hook for lazy loading images
export const useLazyImage = (src: string, placeholder?: string) => {
  const [imageSrc, setImageSrc] = useState(placeholder || '');
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const img = imgRef.current;
    if (!img) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const image = new Image();
            image.onload = () => {
              setImageSrc(src);
              setIsLoaded(true);
            };
            image.onerror = () => {
              setIsError(true);
            };
            image.src = src;
            observer.unobserve(img);
          }
        });
      },
      { threshold: 0.1 }
    );

    observer.observe(img);

    return () => {
      observer.disconnect();
    };
  }, [src]);

  return { imageSrc, isLoaded, isError, imgRef };
};

// Hook for debouncing values (useful for search inputs)
export const useDebounce = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
};

// Hook for intersection observer (useful for animations and lazy loading)
export const useIntersectionObserver = (options: IntersectionObserverInit = {}) => {
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [hasIntersected, setHasIntersected] = useState(false);
  const elementRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          setIsIntersecting(entry.isIntersecting);
          if (entry.isIntersecting && !hasIntersected) {
            setHasIntersected(true);
          }
        });
      },
      { threshold: 0.1, ...options }
    );

    observer.observe(element);

    return () => {
      observer.disconnect();
    };
  }, [hasIntersected, options]);

  return { isIntersecting, hasIntersected, elementRef };
};

// Hook for preloading components
export const useComponentPreloader = () => {
  const preloadedComponents = useRef(new Set<string>());

  const preloadComponent = useCallback(
    async (componentName: string, loader: () => Promise<any>) => {
      if (preloadedComponents.current.has(componentName)) {
        return;
      }

      try {
        await loader();
        preloadedComponents.current.add(componentName);
      } catch (error) {
        console.warn(`Failed to preload component ${componentName}:`, error);
      }
    },
    []
  );

  return { preloadComponent };
};

// Hook for managing loading states with minimum duration
export const useLoadingState = (minDuration: number = 500) => {
  const [isLoading, setIsLoading] = useState(false);
  const startTimeRef = useRef<number>(0);

  const startLoading = useCallback(() => {
    startTimeRef.current = Date.now();
    setIsLoading(true);
  }, []);

  const stopLoading = useCallback(() => {
    const elapsed = Date.now() - startTimeRef.current;
    const remaining = Math.max(0, minDuration - elapsed);

    setTimeout(() => {
      setIsLoading(false);
    }, remaining);
  }, [minDuration]);

  return { isLoading, startLoading, stopLoading };
};

// Hook for optimizing re-renders with shallow comparison
export const useShallowMemo = <T extends Record<string, any>>(obj: T): T => {
  const ref = useRef<T>(obj);

  // Shallow comparison
  const hasChanged =
    Object.keys(obj).some((key) => obj[key] !== ref.current[key]) ||
    Object.keys(ref.current).length !== Object.keys(obj).length;

  if (hasChanged) {
    ref.current = obj;
  }

  return ref.current;
};

// Hook for managing focus trap (useful for modals)
export const useFocusTrap = (isActive: boolean) => {
  const containerRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!isActive) return;

    const container = containerRef.current;
    if (!container) return;

    const focusableElements = container.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0] as HTMLElement;
    const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    };

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        // You can add escape handler here
      }
    };

    document.addEventListener('keydown', handleTabKey);
    document.addEventListener('keydown', handleEscapeKey);

    // Focus first element when trap becomes active
    firstElement?.focus();

    return () => {
      document.removeEventListener('keydown', handleTabKey);
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [isActive]);

  return containerRef;
};

// Hook for managing viewport size
export const useViewport = () => {
  const [viewport, setViewport] = useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 0,
    height: typeof window !== 'undefined' ? window.innerHeight : 0,
  });

  useEffect(() => {
    const handleResize = () => {
      setViewport({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return {
    ...viewport,
    isMobile: viewport.width < 768,
    isTablet: viewport.width >= 768 && viewport.width < 1024,
    isDesktop: viewport.width >= 1024,
  };
};
