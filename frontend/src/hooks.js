import React from "react";

// Generic data-fetch hook driving loading / error / data states.
export function useFetch(fn, deps = []) {
  const [state, setState] = React.useState({ loading: true, error: null, data: null });
  const [nonce, setNonce] = React.useState(0);
  const reload = React.useCallback(() => setNonce((n) => n + 1), []);

  React.useEffect(() => {
    let alive = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    Promise.resolve(fn())
      .then((data) => alive && setState({ loading: false, error: null, data }))
      .catch((error) => alive && setState({ loading: false, error, data: null }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return { ...state, reload };
}
