import type { Page } from "@playwright/test";
export async function deckClick(page: Page, x: number, y: number) {
  await page.evaluate(([x, y]) => {
    const deck = (window as any).__deck;
    if (!deck) {
      throw new Error('No deck instance on window');
    }

    let info;
    if (typeof deck.pickObject === 'function') {
      info = deck.pickObject({ x, y, radius: 2 });
    }

    if (!info) {
      info = {
        x,
        y,
        object: null,
        layer: null,
        index: -1,
        coordinate: [0, 0],
        pixel: [x, y]
      };
    }

    const srcEvent = new PointerEvent('click', {
      clientX: x,
      clientY: y,
      buttons: 1,
      pointerType: 'mouse',
      bubbles: true
    });
    const evt = {
      type: 'click',
      srcEvent,
      center: [x, y],
      offsetCenter: { x, y }
    };

    if (deck.props && deck.props.onClick) {
      deck.props.onClick(info, evt);
    }
  }, [x, y]);
}

export async function deckHover(page: Page, x: number, y: number) {
  await page.evaluate(([x, y]) => {
    const deck = (window as any).__deck;
    if (!deck) {
      throw new Error('No deck instance on window');
    }

    const info = deck.pickObject({ x, y, radius: 2 }) || {
      x,
      y,
      object: null,
      layer: null,
      index: -1,
      coordinate: undefined
    };

    const srcEvent = new PointerEvent('pointermove', {
      clientX: x,
      clientY: y,
      buttons: 0,
      pointerType: 'mouse',
      bubbles: true
    });
    const evt = {
      type: 'pointermove',
      srcEvent,
      center: [x, y],
      offsetCenter: { x, y }
    };

    if (deck.props.onHover) {
      deck.props.onHover(info, evt);
    }
  }, [x, y]);
}

export async function deckDrag(
  page: Page,
  start: { x: number; y: number },
  end: { x: number; y: number },
  steps: number = 5
) {
  await page.evaluate(([start, end, steps]) => {
    const deck = (window as any).__deck;
    if (!deck) {
      throw new Error('No deck instance on window');
    }

    const makeEvent = (type: string, x: number, y: number, buttons: number) => {
      const srcEvent = new PointerEvent(type, {
        clientX: x,
        clientY: y,
        buttons,
        pointerType: 'mouse',
        bubbles: true
      });
      return {
        type,
        srcEvent,
        center: [x, y],
        offsetCenter: { x, y }
      };
    };

    if (deck.props.onDragStart) {
      deck.props.onDragStart(makeEvent('pointerdown', start.x, start.y, 1));
    }

    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      const x = start.x + (end.x - start.x) * t;
      const y = start.y + (end.y - start.y) * t;

      if (deck.props.onDrag) {
        deck.props.onDrag(makeEvent('pointermove', x, y, 1));
      }
    }

    if (deck.props.onDragEnd) {
      deck.props.onDragEnd(makeEvent('pointerup', end.x, end.y, 0));
    }
  }, [start, end, steps]);
}

export async function waitForDeck(page: Page, timeout: number = 10000): Promise<void> {
  await page.waitForFunction(
    () => typeof (window as any).__deck !== 'undefined',
    { timeout }
  );
}
