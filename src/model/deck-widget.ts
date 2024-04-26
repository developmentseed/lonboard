import { Deck, Widget, WidgetPlacement } from '@deck.gl/core';

interface TitleWidgetProps {
  id: string;
  title: string,
  
  placement?: WidgetPlacement;
  style?: Partial<CSSStyleDeclaration>;
}

export class TitleWidget implements Widget<TitleWidgetProps> {

  id = "title";
  props: TitleWidgetProps;
  placement: WidgetPlacement = 'top-right';
  deck?: Deck;
  element?: HTMLDivElement;

  constructor(props: TitleWidgetProps) {
    this.id = props.id || 'title';
    this.placement = props.placement || 'top-right';
    props.title = props.title;
    props.style = props.style || {};

    this.props = props;
  }

  setProps(props: Partial<TitleWidgetProps>) {
    Object.assign(this.props, props);
  }
  
  onAdd({deck}: {deck: Deck}): HTMLDivElement {
    const element = document.createElement('div');
    element.className = 'Title-Widget';

    const titleElement = document.createElement('p');
    titleElement.innerText = this.props.title;

    const {style} = this.props;
    if (style) {
      Object.entries(style).map(([key, value]) => {
        //titleElement.style.setProperty(key, value as string);
        titleElement.style[key] = value as string;
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
