import React from "react";
import { createActorContext } from "@xstate/react";
import { machine } from "./machine";
import { createBrowserInspector } from "@statelyai/inspect";

export const MachineContext = createActorContext(
  machine,
  process.env.XSTATE_INSPECT === "true"
    ? {
        inspect: createBrowserInspector().inspect,
      }
    : undefined,
);

export function MachineProvider(props: { children: React.ReactNode }) {
  return <MachineContext.Provider>{props.children}</MachineContext.Provider>;
}
