/* ==================================================================
   API ADDRESS
   ------------------------------------------------------------------
   Running locally  -> leave this file alone. The backend serves these
                       pages itself, so same-origin requests just work.

   Going live       -> paste your Cloud Run URL into PRODUCTION_API
                       below, then deploy this folder to Netlify.
   ================================================================== */

const PRODUCTION_API = "https://REPLACE-WITH-YOUR-CLOUD-RUN-URL.a.run.app";

const _isLocal = ["localhost", "127.0.0.1", ""].includes(window.location.hostname);

// Local: same origin (empty string). Deployed: the Cloud Run service.
window.API_BASE = _isLocal ? "" : PRODUCTION_API;
