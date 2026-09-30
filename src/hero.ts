import { heroui } from "@heroui/react";

const plugin = heroui();

// HeroUI's base styles set `color` and `background-color` on `:root`, which
// would restyle the page that the widget is embedded in. We set them on
// `div.lonboard` instead, in globals.css.
const ROOT_COLORS_SELECTOR = ":root, [data-theme]";

const handler: typeof plugin.handler = (api) =>
  plugin.handler({
    ...api,
    addBase: (base) => {
      const { [ROOT_COLORS_SELECTOR]: _rootColors, ...rest } = base as Record<
        string,
        unknown
      >;
      api.addBase(rest as typeof base);
    },
  });

export default { ...plugin, handler };
