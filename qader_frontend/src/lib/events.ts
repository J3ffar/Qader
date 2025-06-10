type EventHandler = (data?: any) => void;

class AppEventEmitter {
  private events: { [key: string]: EventHandler[] } = {};

  on(eventName: string, handler: EventHandler): void {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    this.events[eventName].push(handler);
  }

  off(eventName: string, handler: EventHandler): void {
    const eventHandlers = this.events[eventName];
    if (eventHandlers) {
      this.events[eventName] = eventHandlers.filter((h) => h !== handler);
    }
  }

  dispatch(eventName: string, data?: any): void {
    const eventHandlers = this.events[eventName];
    if (eventHandlers) {
      eventHandlers.forEach((handler) => handler(data));
    }
  }
}

// Export a singleton instance to be used throughout the app
export const appEvents = new AppEventEmitter();
