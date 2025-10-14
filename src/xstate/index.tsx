import { createBrowserInspector } from "@statelyai/inspect";
import { createActorContext } from "@xstate/react";
import React from "react";

import { machine } from "./machine";


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
