// From https://www.joshwcomeau.com/snippets/javascript/debounce/
export const debounce = (callback: (args) => void, wait: number) => {
  let timeoutId = null;
  return (...args) => {
    window.clearTimeout(timeoutId);
    timeoutId = window.setTimeout(() => {
      callback.apply(null, args);
    }, wait);
  };
};
