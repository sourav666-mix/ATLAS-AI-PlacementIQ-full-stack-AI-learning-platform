// GoogleSignInButton.jsx - "Continue with Google" via Google Identity Services
// FILE: frontend/src/components/Auth/GoogleSignInButton.jsx
// Loads the GIS script once, renders the official Google button, and on a
// successful credential hands the ID token to authStore.loginWithGoogle.
// Renders nothing when VITE_GOOGLE_CLIENT_ID is not configured, so the
// email/password flow keeps working without any Google setup.

import React, { useEffect, useRef, useState } from "react";
import useAuthStore from "../../store/authStore";

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const GSI_SRC = "https://accounts.google.com/gsi/client";

let gsiPromise = null;
function loadGsi() {
  if (window.google?.accounts?.id) return Promise.resolve();
  if (gsiPromise) return gsiPromise;
  gsiPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => {
      gsiPromise = null;
      reject(new Error("Could not load Google Sign-In."));
    };
    document.head.appendChild(script);
  });
  return gsiPromise;
}

export default function GoogleSignInButton({ onSuccess }) {
  const slotRef = useRef(null);
  const [failed, setFailed] = useState(false);
  const loginWithGoogle = useAuthStore((s) => s.loginWithGoogle);

  useEffect(() => {
    if (!CLIENT_ID) return;
    let cancelled = false;

    loadGsi()
      .then(() => {
        if (cancelled || !slotRef.current) return;
        window.google.accounts.id.initialize({
          client_id: CLIENT_ID,
          callback: async (response) => {
            const ok = await loginWithGoogle(response.credential);
            if (ok && onSuccess) onSuccess();
          },
        });
        window.google.accounts.id.renderButton(slotRef.current, {
          theme: "filled_black",
          size: "large",
          text: "continue_with",
          shape: "pill",
          width: 320,
        });
      })
      .catch(() => !cancelled && setFailed(true));

    return () => {
      cancelled = true;
    };
  }, [loginWithGoogle, onSuccess]);

  if (!CLIENT_ID || failed) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3 text-[11px] uppercase tracking-widest text-gray-600">
        <span className="h-px flex-1 bg-gray-800" />
        or
        <span className="h-px flex-1 bg-gray-800" />
      </div>
      <div ref={slotRef} className="flex justify-center" />
    </div>
  );
}
