// FILE: frontend/src/components/Common/ErrorBoundary.jsx
// Catches render/runtime errors anywhere below it so ONE broken component can't
// blank the whole app to a black screen. Shows the actual error + stack (in dev)
// so the real culprit is visible instead of silently unmounting the tree.

import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    // Keep it in the console too, with the component stack.
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary] caught:", error, info?.componentStack);
    this.setState({ info });
  }

  handleReload = () => {
    this.setState({ error: null, info: null });
    window.location.reload();
  };

  render() {
    const { error, info } = this.state;
    if (!error) return this.props.children;

    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-gray-950 text-gray-100">
        <div className="max-w-2xl w-full rounded-2xl border border-red-900 bg-red-950/30 p-6">
          <h1 className="text-lg font-bold text-red-300">Something crashed while rendering</h1>
          <p className="mt-1 text-sm text-red-200/80">
            The screen below the error was unmounted. Here's what threw — send this
            to fix the root cause.
          </p>
          <pre className="mt-4 max-h-40 overflow-auto rounded-lg bg-black/40 p-3 text-xs text-red-200 whitespace-pre-wrap">
            {String(error?.stack || error?.message || error)}
          </pre>
          {info?.componentStack && (
            <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-black/40 p-3 text-[11px] text-gray-400 whitespace-pre-wrap">
              {info.componentStack}
            </pre>
          )}
          <button
            onClick={this.handleReload}
            className="mt-4 rounded-lg border border-gray-700 px-4 py-2 text-sm text-gray-200 hover:border-gray-500 transition"
          >
            Reload page
          </button>
        </div>
      </div>
    );
  }
}
