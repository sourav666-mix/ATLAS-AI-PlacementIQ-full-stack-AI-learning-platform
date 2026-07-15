// frontend/src/components/Viz/VizMount.jsx
/**
 * ATLAS AI 4.0 - v12 viz pack: the mount point.
 *
 * <VizMount kind={learn.viz_kind} /> resolves the topic's viz_kind
 * (served by the Learn endpoint, defined in curriculum_registry.py) to
 * an interactive component. Three-tier resolution, so this NEVER breaks
 * a Learn page (the v11 optional-dependency lesson, applied to our own
 * components):
 *
 *   1. exact registry hit          -> the built visualization
 *   2. alias hit                   -> the pedagogically-closest built one
 *   3. anything else               -> a graceful "hands-on in the Lab"
 *                                     card (never an error, never blank)
 *
 * Adding a new viz later = one import + one registry line. No page edits.
 */

import LoopViz from "./LoopViz";
import ArrayViz from "./ArrayViz";
import DataFrameViz from "./DataFrameViz";
import JoinViz from "./JoinViz";
import DistributionViz from "./DistributionViz";
import GradientDescentViz from "./GradientDescentViz";
import NetworkViz from "./NetworkViz";
import TokenViz from "./TokenViz";

const REGISTRY = {
  loop_viz: LoopViz,
  array_viz: ArrayViz,
  dataframe_viz: DataFrameViz,
  join_viz: JoinViz,
  distribution_viz: DistributionViz,
  gradient_descent_viz: GradientDescentViz,
  network_viz: NetworkViz,
  token_viz: TokenViz,
};

// Aliases: only where the built viz genuinely teaches the aliased idea.
const ALIASES = {
  chart_viz: "distribution_viz",       // Data Visualization -> live curve
  loss_curve_viz: "gradient_descent_viz", // Fine-Tuning -> descent on loss
  prompt_viz: "token_viz",             // Prompt Engineering -> tokens first
  attention_viz: "token_viz",          // Transformer -> token-level intuition
  feature_viz: "dataframe_viz",        // Feature Engineering -> column ops
  rl_grid_viz: "network_viz",          // RL intro -> the function approximator
};

function FallbackViz({ kind }) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-700 bg-zinc-950 p-4
                    text-xs text-zinc-400">
      <p>
        🎛️ The interactive <code className="text-sky-300">{kind}</code>{" "}
        visualization ships in a later viz pack.
      </p>
      <p className="mt-1 text-zinc-500">
        Until then this topic is fully hands-on in{" "}
        <span className="text-zinc-300">Live Lab Pro</span> - open the Lab
        from the button above and experiment with the worked examples.
      </p>
    </div>
  );
}

export default function VizMount({ kind }) {
  if (!kind) return null;
  const Resolved = REGISTRY[kind] || REGISTRY[ALIASES[kind]] || null;
  if (!Resolved) return <FallbackViz kind={kind} />;
  return <Resolved />;
}

export { REGISTRY, ALIASES };