# Encompliance Frontend Utilities

## Theme System

The Encompliance application uses a consistent theme system that supports both light and dark modes. This document explains how to use the theme system when creating new pages or components.

### Using Theme Classes

The `themeUtils.ts` file provides a set of predefined theme classes that can be used across the application. These classes automatically handle both light and dark mode styling.

#### Basic Usage

```tsx
import { themeClasses } from '../utils/themeUtils';

const MyComponent = () => {
  return (
    <div className={themeClasses.layout.container}>
      <h1 className={themeClasses.text.primary}>My Page Title</h1>
      <div className={themeClasses.components.card}>
        <p className={themeClasses.text.secondary}>This is a card with automatic dark mode support.</p>
        <button className={themeClasses.components.button.primary}>Primary Button</button>
      </div>
    </div>
  );
};
```

#### Using Helper Functions

For more complex combinations, you can use the helper functions:

```tsx
import { getThemeClasses, combineThemeClasses } from '../utils/themeUtils';

const MyComponent = () => {
  // Get a single class set
  const buttonClass = getThemeClasses('button', 'danger');
  
  // Combine multiple class sets
  const cardClasses = combineThemeClasses([
    { type: 'bg', variant: 'secondary' },
    { type: 'border', variant: 'accent' }
  ]);
  
  return (
    <div>
      <button className={buttonClass}>Danger Button</button>
      <div className={`p-4 rounded-lg ${cardClasses}`}>
        Custom card with combined classes
      </div>
    </div>
  );
};
```

### Available Theme Classes

#### Text Colors
- `text.primary`: Main text color (navy-blue in light mode, white in dark mode)
- `text.secondary`: Secondary text color
- `text.muted`: Muted/subtle text color
- `text.link`: Link text with hover states
- `text.danger`: Error/danger text
- `text.success`: Success text

#### Background Colors
- `bg.primary`: Primary background (white in light mode, dark surface in dark mode)
- `bg.secondary`: Secondary background
- `bg.accent`: Accent background (navy-blue/blue)
- `bg.danger`: Danger/error background
- `bg.success`: Success background
- `bg.warning`: Warning background

#### Border Colors
- `border.primary`: Primary border color
- `border.secondary`: Secondary border color
- `border.accent`: Accent border color

#### Components
- `components.card`: Card component styling
- `components.input`: Input field styling
- `components.button.primary`: Primary button
- `components.button.secondary`: Secondary button
- `components.button.danger`: Danger/delete button
- `components.divider`: Divider line
- `components.loader`: Loading spinner

#### Layout
- `layout.container`: Page container
- `layout.section`: Section container
- `layout.header`: Header section

### Best Practices

1. **Always use theme classes for new pages**: This ensures consistent styling and automatic dark mode support.
2. **Add transition effects**: All theme classes include `transition-colors duration-300` for smooth theme transitions.
3. **Test in both modes**: Always test your UI in both light and dark modes.
4. **Extend the theme system**: If you need new theme classes, add them to the `themeUtils.ts` file rather than creating one-off styles.

### Creating New Pages

When creating a new page, start with this template to ensure proper theme support:

```tsx
import React from 'react';
import { themeClasses } from '../utils/themeUtils';

interface MyPageProps {
  // Your props here
}

const MyPage: React.FC<MyPageProps> = (props) => {
  return (
    <div className={themeClasses.layout.container}>
      <h1 className={themeClasses.text.primary}>My Page Title</h1>
      
      <div className={themeClasses.components.card}>
        {/* Your content here */}
      </div>
      
      {/* More content */}
    </div>
  );
};

export default MyPage;
``` 