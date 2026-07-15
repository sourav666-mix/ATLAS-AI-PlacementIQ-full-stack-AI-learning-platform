// FILE: frontend/src/store/labStore.js
// BATCH 21 / v11 Phase 13 (new) - Zustand store for the Live Lab: current
// lab, editor code, dataset name, task results. State only — no network.

import { create } from "zustand";

const useLabStore = create((set) => ({
  lab: null,               // the lab object from GET /lab/{id}
  code: "",                // current Monaco buffer
  datasetName: null,       // uploaded file in the virtual FS (local only)
  taskResults: {},         // {taskId: bool} from the last in-browser grade
  grading: false,
  completed: false,
  pointsAwarded: 0,

  setLab: (lab) =>
    set({
      lab,
      code:
        (lab && lab.session && lab.session.code_snapshot) ||
        (lab && lab.starter_code) ||
        "",
      taskResults: (lab && lab.session && lab.session.tasks_passed) || {},
      completed: !!(lab && lab.session && lab.session.status === "completed"),
      pointsAwarded: (lab && lab.session && lab.session.points_awarded) || 0,
      datasetName: null,
    }),
  setCode: (code) => set({ code }),
  setDatasetName: (datasetName) => set({ datasetName }),
  setGrading: (grading) => set({ grading }),
  setTaskResults: (taskResults) => set({ taskResults }),
  markCompleted: (pointsAwarded) =>
    set({ completed: true, pointsAwarded }),
  reset: () =>
    set({
      lab: null, code: "", datasetName: null, taskResults: {},
      grading: false, completed: false, pointsAwarded: 0,
    }),
}));

export default useLabStore;