import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FormField from './FormField';
import { testA11y } from '../../../tests/utils/a11y-test-utils';

describe('FormField Component', () => {
  const defaultProps = {
    id: 'test-field',
    label: 'Test Field',
    value: '',
    onChange: jest.fn(),
  };

  it('renders correctly with default props', () => {
    render(<FormField {...defaultProps} />);
    
    expect(screen.getByLabelText('Test Field')).toBeInTheDocument();
    expect(screen.getByLabelText('Test Field')).toHaveAttribute('type', 'text');
    expect(screen.getByLabelText('Test Field')).not.toBeRequired();
  });

  it('shows required indicator when required is true', () => {
    render(<FormField {...defaultProps} required={true} />);
    
    expect(screen.getByText('*')).toBeInTheDocument();
    expect(screen.getByLabelText('Test Field')).toBeRequired();
  });

  it('shows error message when error is provided', () => {
    const errorMessage = 'This field is required';
    render(<FormField {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
    expect(screen.getByLabelText('Test Field')).toHaveAttribute('aria-invalid', 'true');
  });

  it('calls onChange handler when input value changes', () => {
    render(<FormField {...defaultProps} />);
    
    fireEvent.change(screen.getByLabelText('Test Field'), {
      target: { value: 'New value' }
    });
    
    expect(defaultProps.onChange).toHaveBeenCalledTimes(1);
  });

  it('renders textarea when type is textarea', () => {
    render(<FormField {...defaultProps} type="textarea" />);
    
    const textarea = screen.getByLabelText('Test Field');
    expect(textarea.tagName).toBe('TEXTAREA');
  });

  it('applies disabled state when disabled prop is true', () => {
    render(<FormField {...defaultProps} disabled={true} />);
    
    expect(screen.getByLabelText('Test Field')).toBeDisabled();
  });

  it('passes accessibility test', async () => {
    await testA11y(
      <FormField 
        id="a11y-test" 
        label="Accessible Field" 
        value="Test value" 
        onChange={jest.fn()} 
      />
    );
  });
}); 