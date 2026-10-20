# Accessibility Guide

This guide outlines our approach to ensuring the EnCompliance application meets WCAG AA standards for accessibility.

## Testing Approach

### 1. Automated Testing with axe-core

We use the [axe-core](https://github.com/dequelabs/axe-core) library to automatically detect accessibility issues in our React components. 

#### Unit Test Integration

- Each UI component has an accessibility test using jest-axe
- Tests can be run with `npm test` or specifically with `npm run test:a11y`

#### Cypress Integration

- End-to-end tests check accessibility on key pages
- Uses cypress-axe to detect violations
- Run with `npm run cypress:a11y`

### 2. Manual Testing 

For a comprehensive accessibility review, manual testing should also be performed:

- Keyboard navigation testing
- Screen reader testing (VoiceOver, NVDA, JAWS)
- Color contrast verification
- Focus state verification

#### Release Sign-off Checklist

Before every release, complete and record the following in the sprint retro or release ticket:

- [ ] Keyboard-only smoke of public pages (`/`, `/login`, `/support`)
- [ ] Authenticated journey review for facility admin and team member personas (dashboard → tasks, notes → activities)
- [ ] Screen reader spot check (VoiceOver or NVDA) covering navigation, live regions, and modal interactions
- [ ] Contrast validation for all newly introduced palettes using the WebAIM checker
- [ ] Documentation of findings and remediation owners in the release changelog

## Responsive Layout Testing

We test the responsive behavior of our application across a range of viewport sizes from 320px to 2560px.

### Automated Testing

- Cypress tests verify layouts at different breakpoints
- Run with `npm run cypress:responsive`

### Manual Testing

For development and manual verification:

1. Use the ResponsiveTester tool included in development mode:
   - Click the "RWD" button that appears in the bottom right corner
   - Use the buttons to switch between different viewport sizes

2. Use browser developer tools to test different viewport sizes

## WCAG AA Compliance Checklist

When developing or reviewing components, ensure they meet these basic requirements:

### Perceivable
- Text has sufficient color contrast (4.5:1 for normal text, 3:1 for large text)
- Images have alt text
- Content is not conveyed through color alone
- UI is responsive across device sizes (320px → 2560px)

### Operable
- All functionality is available via keyboard
- Focus order is logical and intuitive
- Focus states are visible
- No content flashes more than 3 times per second

### Understandable
- Labels are descriptive and associated with their controls
- Error messages are clear and suggest corrections
- Navigation is consistent throughout the application

### Robust
- HTML is valid and properly nested
- ARIA roles, states, and properties are used correctly
- Custom UI components have appropriate ARIA markup

## Resources

- [WCAG 2.1 AA Guidelines](https://www.w3.org/WAI/WCAG21/quickref/?currentsidebar=%23col_customize&levels=aaa)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/master/doc/rule-descriptions.md)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/) 