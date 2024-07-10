import { Action, baseReducer, State } from ".";

export function logReducer(reducer: typeof baseReducer) {
  console.log(process.env);
  /* eslint-disable no-console */
  return (state: State, action: Action) => {
    const nextState = reducer(state, action);

    console.log(state, action);
    console.groupCollapsed(action.type);
    console.log("%c%s", "color: gray; font-weight: bold", "prev state ", state);
    console.log("%c%s", "color: cyan; font-weight: bold", "action ", action);
    console.log(
      "%c%s",
      "color: green; font-weight: bold",
      "next state ",
      nextState,
    );
    console.groupEnd();
    return nextState;
  };
  /* eslint-enable no-console */
}
