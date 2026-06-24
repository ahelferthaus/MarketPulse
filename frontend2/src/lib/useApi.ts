import { useEffect, useState } from "react";

/**
 * Run an async data factory and return its latest result.
 *
 * Starts from `initial` (so the UI renders immediately, typically with mock
 * data) and swaps in the resolved value when the promise settles. Re-runs when
 * `deps` change and ignores results from stale runs.
 */
export function useAsync<T>(
  factory: () => Promise<T>,
  initial: T,
  deps: unknown[],
): T {
  const [value, setValue] = useState<T>(initial);

  useEffect(() => {
    let active = true;
    factory()
      .then((v) => {
        if (active) setValue(v);
      })
      .catch(() => {
        /* factories fall back to mock data internally */
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return value;
}
