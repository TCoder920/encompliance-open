/**
 * Description: Tooltip display manager for tracking and limiting tooltip appearances.
 * Purpose: Manages how many times informational tooltips are shown to users before being permanently dismissed.
 */

interface TooltipState {
  showCount: number;
  isDismissed: boolean;
  lastShown: string;
}

const TOOLTIP_STORAGE_KEY = 'encompliance_tooltips';
const MAX_SHOW_COUNT = 3; // Show tooltip maximum 3 times

class TooltipManager {
  private getTooltipState(tooltipId: string): TooltipState {
    try {
      const stored = localStorage.getItem(TOOLTIP_STORAGE_KEY);
      const tooltips = stored ? JSON.parse(stored) : {};
      return tooltips[tooltipId] || {
        showCount: 0,
        isDismissed: false,
        lastShown: ''
      };
    } catch (error) {
      console.warn('Failed to read tooltip state from localStorage:', error);
      return {
        showCount: 0,
        isDismissed: false,
        lastShown: ''
      };
    }
  }

  private setTooltipState(tooltipId: string, state: TooltipState): void {
    try {
      const stored = localStorage.getItem(TOOLTIP_STORAGE_KEY);
      const tooltips = stored ? JSON.parse(stored) : {};
      tooltips[tooltipId] = state;
      localStorage.setItem(TOOLTIP_STORAGE_KEY, JSON.stringify(tooltips));
    } catch (error) {
      console.warn('Failed to save tooltip state to localStorage:', error);
    }
  }

  /**
   * Check if a tooltip should be shown
   */
  shouldShowTooltip(tooltipId: string): boolean {
    const state = this.getTooltipState(tooltipId);
    
    // Don't show if permanently dismissed
    if (state.isDismissed) {
      return false;
    }
    
    // Don't show if max count reached
    if (state.showCount >= MAX_SHOW_COUNT) {
      return false;
    }
    
    // Don't show if shown recently (within last 24 hours)
    if (state.lastShown) {
      const lastShown = new Date(state.lastShown);
      const now = new Date();
      const hoursSinceLastShown = (now.getTime() - lastShown.getTime()) / (1000 * 60 * 60);
      
      if (hoursSinceLastShown < 24) {
        return false;
      }
    }
    
    return true;
  }

  /**
   * Mark tooltip as shown (increment count)
   */
  markTooltipShown(tooltipId: string): void {
    const state = this.getTooltipState(tooltipId);
    state.showCount += 1;
    state.lastShown = new Date().toISOString();
    this.setTooltipState(tooltipId, state);
  }

  /**
   * Permanently dismiss a tooltip
   */
  dismissTooltip(tooltipId: string): void {
    const state = this.getTooltipState(tooltipId);
    state.isDismissed = true;
    this.setTooltipState(tooltipId, state);
  }

  /**
   * Reset tooltip state (for testing/debugging)
   */
  resetTooltip(tooltipId: string): void {
    const state: TooltipState = {
      showCount: 0,
      isDismissed: false,
      lastShown: ''
    };
    this.setTooltipState(tooltipId, state);
  }

  /**
   * Get tooltip statistics
   */
  getTooltipStats(tooltipId: string): TooltipState {
    return this.getTooltipState(tooltipId);
  }

  /**
   * Development helper: Reset all tooltips (for testing)
   */
  resetAllTooltips(): void {
    try {
      localStorage.removeItem(TOOLTIP_STORAGE_KEY);
    } catch (error) {
      console.warn('Failed to reset all tooltips:', error);
    }
  }
}

export const tooltipManager = new TooltipManager();
export default tooltipManager; 