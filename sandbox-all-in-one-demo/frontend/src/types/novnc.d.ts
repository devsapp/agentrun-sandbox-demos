declare module '@novnc/novnc/core/rfb' {
  export default class RFB {
    constructor(target: HTMLElement, url: string);
    scaleViewport: boolean;
    resizeSession: boolean;
    disconnect(): void;
    addEventListener(event: string, callback: () => void): void;
  }
}
