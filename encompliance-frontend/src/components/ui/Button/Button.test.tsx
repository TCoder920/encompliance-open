/*
  Description: Test suite for the Button component. Contains unit tests to verify the component's rendering, variants, sizes, states, and event handling.
  Purpose: Ensures the Button component functions as expected across different configurations and user interactions.
*/
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { testA11y } from '../../../tests/utils/a11y-test-utils';
import { Button } from './Button';

describe('Button Component', () => {
  it('renders correctly with default props', () => {
    render(<Button>Test Button</Button>);
    
    const button = screen.getByText('Test Button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('type', 'button');
    expect(button).not.toBeDisabled();
    expect(button).toHaveClass('bg-blue-600'); // Default primary variant
  });

  it('renders different variants correctly', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByText('Primary')).toHaveClass('bg-blue-600');
    
    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByText('Secondary')).toHaveClass('bg-gray-200');
    
    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByText('Outline')).toHaveClass('border-gray-300');
    
    rerender(<Button variant="text">Text</Button>);
    expect(screen.getByText('Text')).toHaveClass('bg-transparent');
    
    rerender(<Button variant="danger">Danger</Button>);
    expect(screen.getByText('Danger')).toHaveClass('bg-red-600');
  });

  it('renders different sizes correctly', () => {
    const { rerender } = render(<Button size="sm">Small</Button>);
    expect(screen.getByText('Small')).toHaveClass('text-sm');
    
    rerender(<Button size="md">Medium</Button>);
    expect(screen.getByText('Medium')).toHaveClass('text-base');
    
    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByText('Large')).toHaveClass('text-lg');
  });

  it('applies fullWidth style when fullWidth is true', () => {
    render(<Button fullWidth>Full Width</Button>);
    expect(screen.getByText('Full Width')).toHaveClass('w-full');
  });

  it('shows loading state when isLoading is true', () => {
    render(<Button isLoading>Loading</Button>);
    
    expect(screen.getByText('Loading')).toBeInTheDocument();
    expect(screen.getByText('Loading').parentElement).toContainElement(
      screen.getByRole('img', { hidden: true }) // SVG loading spinner
    );
  });

  it('renders with left icon when leftIcon is provided', () => {
    const leftIcon = <span data-testid="left-icon">🔍</span>;
    render(<Button leftIcon={leftIcon}>With Left Icon</Button>);
    
    expect(screen.getByTestId('left-icon')).toBeInTheDocument();
    expect(screen.getByText('With Left Icon')).toBeInTheDocument();
  });

  it('renders with right icon when rightIcon is provided', () => {
    const rightIcon = <span data-testid="right-icon">➡️</span>;
    render(<Button rightIcon={rightIcon}>With Right Icon</Button>);
    
    expect(screen.getByTestId('right-icon')).toBeInTheDocument();
    expect(screen.getByText('With Right Icon')).toBeInTheDocument();
  });

  it('applies disabled state when disabled is true', () => {
    render(<Button disabled>Disabled</Button>);
    
    expect(screen.getByText('Disabled')).toBeDisabled();
    expect(screen.getByText('Disabled')).toHaveClass('opacity-60');
  });

  it('calls onClick handler when clicked', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click Me</Button>);
    
    fireEvent.click(screen.getByText('Click Me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('passes custom type attribute', () => {
    render(<Button type="submit">Submit</Button>);
    expect(screen.getByText('Submit')).toHaveAttribute('type', 'submit');
  });

  it('merges custom className with default classes', () => {
    render(<Button className="custom-class">Custom</Button>);
    expect(screen.getByText('Custom')).toHaveClass('custom-class');
    expect(screen.getByText('Custom')).toHaveClass('bg-blue-600'); // Still has default classes
  });

  it('passes accessibility test', async () => {
    await testA11y(<Button>Accessible Button</Button>);
  });

  it('passes accessibility test when disabled', async () => {
    await testA11y(<Button disabled>Disabled Button</Button>);
  });
}); 