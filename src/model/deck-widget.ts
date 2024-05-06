import { Deck, Widget, WidgetPlacement } from '@deck.gl/core';

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
    props.className = props.className || 'deck-widget-title';
    this.props = props;
  }

  setProps(props: Partial<TitleWidgetProps>) {
    Object.assign(this.props, props);
  }
  
  onAdd({deck}: {deck: Deck}): HTMLDivElement {
    const element = document.createElement('div');
    
    element.classList.add('deck-widget');
    if (this.props.className) element.classList.add(this.props.className);

    const titleElement = document.createElement('div');
    titleElement.innerText = this.props.title;

    const {style} = this.props;
    if (style) {
      Object.entries(style).map(([key, value]) => {
        titleElement.style.setProperty(key, value as string);
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
