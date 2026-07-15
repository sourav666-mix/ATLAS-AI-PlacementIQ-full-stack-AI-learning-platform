// resumeApi.js - [MOD] analyze / rebuild / builder draft+export / documents
// FILE: frontend/src/api/resumeApi.js
// BATCH 29 / v10 Resume AI (new) - analyze / rebuild / builder draft+export /
// documents. analyze() sends multipart (resume file + optional JD).

import api from "./axios";

const resumeApi = {
  // Mode A: upload resume (+ optional JD text or file) -> full report JSON.
  analyze: ({ resumeFile, jdText, jdFile }) => {
    const form = new FormData();
    if (resumeFile) form.append("resume", resumeFile);
    if (jdFile) form.append("job_description_file", jdFile);
    if (jdText) form.append("job_description", jdText);
    return api
      .post("/resume/analyze", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },

  // Analyzed resume -> improved ATS PDF (returns a url or base64).
  rebuild: (analysisId, template = "classic") =>
    api
      .post("/resume/rebuild", { analysis_id: analysisId, template })
      .then((r) => r.data),

  // Mode B: form fields -> AI-drafted, editable resume JSON.
  builderDraft: (form) =>
    api.post("/resume/builder/draft", form).then((r) => r.data),

  // Final edited JSON + template + pages -> PDF.
  builderExport: ({ draft, template, pages }) =>
    api
      .post("/resume/builder/export", {
        resume: draft,
        template,
        pages,
      })
      .then((r) => r.data),

  documents: () => api.get("/resume/documents").then((r) => r.data),
};

export default resumeApi;