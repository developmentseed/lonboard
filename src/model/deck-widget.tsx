import { Deck, Viewport, WebMercatorViewport, Widget, WidgetPlacement } from '@deck.gl/core';
import { CompassWidget } from '@deck.gl/widgets';
import React from 'react';
import { Root, createRoot } from 'react-dom/client';
import { toPng } from 'html-to-image';

interface TitleWidgetProps {
  id: string;
  title: string,
  
  placement?: WidgetPlacement;
  style?: Partial<CSSStyleDeclaration>;
  className?: string;
}

export class TitleWidget implements Widget<TitleWidgetProps> {

  id = "title";
  props: TitleWidgetProps;
  placement: WidgetPlacement = 'top-right';
  deck?: Deck;
  element?: HTMLDivElement;
  className: string = 'deck-widget-title';

  constructor(props: TitleWidgetProps) {
    this.id = props.id || 'title';
    this.placement = props.placement || 'top-right';
    props.title = props.title;
    props.style = props.style || {};
    this.className = props.className || 'deck-widget-title';
    this.props = props;
  }

  setProps(props: Partial<TitleWidgetProps>) {
    Object.assign(this.props, props);
  }
  
  onAdd({deck}: {deck: Deck}): HTMLDivElement {
    const element = document.createElement('div');
    
    element.classList.add('deck-widget');
    if (this.className) element.classList.add(this.className);

    const titleElement = document.createElement('div');
    titleElement.innerText = this.props.title;

    const {style} = this.props;
    if (style) {
      Object.entries(style).map(([key, value]) => {
        element.style.setProperty(key, value as string);
      } );
    }
    element.appendChild(titleElement);
    
    this.deck = deck;
    this.element = element;
    return element;
  }
  
  onRemove() {
    this.deck = undefined;
    this.element = undefined;
  }
}

interface LegendWidgetProps {
  id: string;
  title: string,
  legend: Map<string, string>,
  placement?: WidgetPlacement;
  style?: Partial<CSSStyleDeclaration>;
  className?: string;
}

export class LegendWidget implements Widget<LegendWidgetProps> {

  id = "legend";
  props: LegendWidgetProps;
  placement: WidgetPlacement = "bottom-right";

  deck?: Deck;
  element?: HTMLDivElement;
  className: string = "deck-widget-legend";

  constructor(props: LegendWidgetProps) {
    this.id = props.id || 'legend';
    this.placement = props.placement || 'bottom-right';
    props.title = props.title || 'Legend';
    props.legend = props.legend;
    props.style = props.style || {};
    this.className = props.className || 'deck-widget-legend';
    this.props = props;
  }

  setProps(props: Partial<LegendWidgetProps>) {
    Object.assign(this.props, props);
  }
  
  onAdd({deck}: {deck: Deck}): HTMLDivElement {
    const element = document.createElement('div');
    
    element.classList.add('deck-widget');
    if (this.className) element.classList.add(this.className);

    const titleElement = document.createElement('div');
    titleElement.innerText = this.props.title;
    titleElement.classList.add("legend-title");

    const legendElement = document.createElement('div');
    legendElement.classList.add("legend-scale");

    const ul = document.createElement('ul');
    ul.classList.add("legend-labels");

    this.props.legend.forEach((color, label) => {
      const li = document.createElement('li');
      const span = document.createElement('span');

      span.style.setProperty("background", color )
      li.innerText = label;

      li.appendChild(span);
      ul.appendChild(li);
    });

    legendElement.appendChild(ul);

    const {style} = this.props;
    if (style) {
      Object.entries(style).map(([key, value]) => {
        element.style.setProperty(key, value as string);
      } );
    }
    element.appendChild(titleElement);
    element.appendChild(legendElement);

    this.deck = deck;
    this.element = element;
    return element;
  }
  
  onRemove() {
    this.deck = undefined;
    this.element = undefined;
  }
}

export class NorthArrowWidget extends CompassWidget {

  root?: Root;

  onAdd({deck}: {deck: Deck<any>}): HTMLDivElement {
    const {style, className} = this.props;
    const element = document.createElement('div');
    element.classList.add('deck-widget', 'deck-widget-north-arrow');
    if (className) element.classList.add(className);
    if (style) {
      Object.entries(style).map(([key, value]) => element.style.setProperty(key, value as string));
    }
    this.deck = deck;
    this.element = element;

    this.root = createRoot(element);

    this.update();
    return element;
  }

  update() {
    const [rz, rx] = this.getRotation();
    const element = this.element;
    if (!element) {
      return;
    }
    const ui = (
      <div style={{transform: `rotateX(${rx}deg)`}}>
        <svg transform={`rotate(${rz})`}width="100px" height="100px" viewBox="0 0 773 798">
          <path transform={`translate(0 798) scale(1 -1)`} d="m674 403-161 48q-17 48-66 70l-46 166-46-167q-22-9-38-25t-29-45l-159-47 159-49q15-44 67-68l46-164 48 164q39 17 64 69zm-163 0q0-49-32-81-33-34-78-34-46 0-77 34-31 31-31 81 0 46 31 80t77 34q45 0 78-34 32-34 32-80zm-12 1q-5 7-7.5 17.5t-4 21.5-4.5 21-9 16q-7 6-17 9.5t-20.5 6-20 6-15.5 9.5v-107h98zm-98-108v108h-99l3-3 23-75q6-6 16.5-9.5t21-5.5 20-5.5 15.5-9.5zm-280 152h-26v-2q5 0 6-1 3-3 3-6 0-2-0.5-4t-1.5-7l-18-48-16 47q-3 9-3 12 0 7 7 7h2v2h-34v-2q2 0 3-1l3-3q2 0 2-2 2-1 4-5l5-15-12-42-17 50q-3 9-3 11 0 7 6 7h2v2h-33v-2q8 0 10-6 1-2 3-9l27-74h5l15 53 19-53h2l27 71q2 10 3 11 5 7 10 7v2zm325 350h-29v-3q7 0 10-4 1-1 1-11v-35l-42 53h-32v-3q7-2 12-6l2-3v-62q0-13-12-13v-2h29v2h-2q-4 0-7 2.5t-3 10.5v55l58-72h3v73q0 9 1 10.5t8 3.5l3 1v3zm207-395h-130q0 16-6 42zm-212-119-40-141v135q9 0 19 1t21 5zm-154 78-137 41h130q0-10 2-19.5t5-21.5zm114 168q-25 0-39-8l39 142v-134zm372-148h-3q-3-4-5-7.5t-4-5.5q-5-5-17-5h-19q-3 0-3 5v35h20q8 0 10-6 1-1 1-3 0-3 1-4h3v30h-3q-2-9-4-11t-8-2h-20v35h24q7 0 8-1 4-1 9-14h3l-1 20h-69v-2h3q7 0 8-4 2-2 2-9v-58q0-11-4-12-1-1-6-1h-3v-3h68zm-340-358q0 9-5.5 14.5t-20.5 14.5q-9 5-13 9l-5 5q-3 10-3 7 0 14 14 14 18 0 24-26h2v31h-2q-2-6-5-6-4 0-5 1-8 5-15 5-11 0-17.5-7t-6.5-17q0-13 9-19 6-4 16.5-10.5t12.5-8.5q8-7 8-13 0-14-18-14-13 0-18 5.5t-7 20.5h-2v-30h2q0 5 3 5l16-5h8q12 0 20 7t8 17z"/>
        </svg>
      </div>
    );

    if (this.root)
      this.root.render(ui);
  }
}

interface ScaleWidgetProps {
  id: string;
  maxWidth: number;
  useImperial: boolean;
  viewId?: string | null;
  placement?: WidgetPlacement;
  style?: Partial<CSSStyleDeclaration>;
  className?: string;
}
export class ScaleWidget implements Widget<ScaleWidgetProps> {

  root?: Root;

  id = "scale";
  props: ScaleWidgetProps;

  viewId?: string | null = null;
  viewport?: Viewport;
  placement: WidgetPlacement = "bottom-left";
  deck?: Deck;
  element?: HTMLDivElement;
  className: string = "deck-widget-scale";

  constructor(props: ScaleWidgetProps) {
    this.id = props.id || 'scale';
    this.placement = props.placement || 'bottom-left';
    this.viewId = props.viewId || null;
    props.maxWidth = props.maxWidth || 300;
    props.useImperial = props.useImperial || false;
    props.style = props.style || {};
    this.className = props.className || 'deck-widget-scale';
    this.props = props;
  }

  setProps(props: Partial<ScaleWidgetProps>) {
    Object.assign(this.props, props);
  }

  onViewportChange(viewport: Viewport) {
    this.viewport = viewport;
    this.update();
  }
  
  onAdd({deck}: {deck: Deck<any>}): HTMLDivElement {
    const {style, className} = this.props;
    const element = document.createElement('div');
    element.classList.add('deck-widget', 'deck-widget-scale');
    if (className) element.classList.add(className);
    if (style) {
      Object.entries(style).map(([key, value]) => element.style.setProperty(key, value as string));
    }
    this.deck = deck;
    this.element = element;

    this.root = createRoot(element);

    this.update();
    return element;
  }

  update() {
    if (this.viewport instanceof WebMercatorViewport) {
      
      const meters = this.viewport.metersPerPixel * this.props.maxWidth;
      let distance, label, ratio;
      
      if (this.props.useImperial) {
        const feet = meters * 3.2808399;
        if (feet > 5280) {
            distance = feet / 5280;
            label = "mi";

        } else {
          distance = feet;
          label = "ft";
        }
      }
      else{
        distance = meters < 1000 ? meters : meters / 1000;
        label = meters < 1000 ? `m` : `km`;
      }
      
      ratio = this.roundNumber(distance) / distance;
      distance = this.roundNumber(distance);
      const width = `${Math.round(this.props.maxWidth * ratio * (4/3))}px`;

      const element = this.element;
      if (!element) {
        return;
      }
      const ui = (
        <div>
            <svg id="test" style={{width:width,height:'40px'}}>
              <rect id="border" style={{stroke:'#000',fill:'#FFF'}} height="40%" width="75%" x="5%" y="2%"/>
              <rect id="first_block" style={{fill:'#000'}} height="20%" width="37.5%" x="5%" y="2%"/>
              <rect id="second_block" style={{fill:'#000'}} height="20%" width="37.5%" x="42.5%" y="22%"/>
              <text id="zero" text-anchor="middle" font-size="20" x="5%" y="95%">0</text>
              <text id="half_scale" font-size="20" text-anchor="middle" x="42.5%" y="95%">{distance/2}</text>
              <text id="scale" font-size="20" text-anchor="middle" x="80%" y="95%">{distance}</text>
              <text id="unit" font-size="20" x="82%" y="42%">{label}</text></svg>
        </div>
      );

      if (this.root)
        this.root.render(ui);
    }
  }

  roundNumber(number: number) {
    const pow10 = Math.pow(10, (`${Math.floor(number)}`).length - 1);
		let d = number / pow10;

		d = d >= 10 ? 10 :
		    d >= 5 ? 5 :
		    d >= 3 ? 3 :
		    d >= 2 ? 2 : 1;

		return pow10 * d;
  }
  
  onRemove() {
    this.deck = undefined;
    this.element = undefined;
  }
}

interface SaveImageWidgetProps {
  id: string;
  label?: string;
  
  placement?: WidgetPlacement;
  style?: Partial<CSSStyleDeclaration>;
  className?: string;
}

export class SaveImageWidget implements Widget<SaveImageWidgetProps> {
  root?: Root;

  id = 'save-image';
  props: SaveImageWidgetProps;
  placement: WidgetPlacement = 'top-right';
  viewId?: string | null = null;
  viewport?: Viewport;
  deck?: Deck<any>;
  element?: HTMLDivElement;

  constructor(props: SaveImageWidgetProps) {
    this.id = props.id || 'save-image';
    this.placement = props.placement || 'top-right';
    props.label = props.label || 'Save as Image';
    props.style = props.style || {};
    this.props = props;
  }

  onAdd({deck}: {deck: Deck<any>}): HTMLDivElement {
    const {style, className} = this.props;
    const element = document.createElement('div');
    element.classList.add('deck-widget', 'deck-widget-save-image');
    if (className) element.classList.add(className);
    if (style) {
      Object.entries(style).map(([key, value]) => element.style.setProperty(key, value as string));
    }
    this.root = createRoot(element);
    
    const ui = (
      <div className="deck-widget-button">
      <button
        className={`deck-widget-icon-button ${className}`}
        type="button"
        onClick={() => this.onClick.bind(this)}
        title={this.props.label}
      >
        <svg fill="#000000" version="1.1" width="85%" height="85%" viewBox="0 0 492.676 492.676">
          <g>
            <g>
              <path d="M492.676,121.6H346.715l-23.494-74.789h-40.795H210.25h-40.794L145.961,121.6H0v324.266h492.676V121.6L492.676,121.6z
                M246.338,415.533c-72.791,0-131.799-59.009-131.799-131.799c0-72.792,59.008-131.8,131.799-131.8s131.799,59.008,131.799,131.8
                C378.137,356.525,319.129,415.533,246.338,415.533z"/>
              <path d="M246.338,199.006c-46.72,0-84.728,38.008-84.728,84.729c0,46.72,38.008,84.728,84.728,84.728
                c46.721,0,84.728-38.008,84.728-84.728C331.065,237.014,293.059,199.006,246.338,199.006z"/>
            </g>
          </g>
        </svg>
      </button>
    </div>
    );
    
    if (this.root)
      this.root.render(ui);

    this.deck = deck;
    this.element = element;

    return element;
  }

  async onClick() {
    if (this.deck) {
    
      this.deck.redraw("true");
      const deck_wrapper = this.deck?.getCanvas()?.parentElement;
      console.log(deck_wrapper);
      
     if(deck_wrapper) {
        toPng(deck_wrapper, )
        .then(function (dataUrl) {
          var img = new Image();
          img.src = dataUrl;

          const a = document.createElement('a');
          a.href = dataUrl;
          a.download = 'map.png';
          a.click();
        })
        .catch(function (error) {
          console.error('Failed to export PNG', error);
        });
      }
    }
  }

  onRemove() {
    this.deck = undefined;
    this.element = undefined;
  }

  setProps(props: Partial<SaveImageWidgetProps>) {
    Object.assign(this.props, props);
  }
}
