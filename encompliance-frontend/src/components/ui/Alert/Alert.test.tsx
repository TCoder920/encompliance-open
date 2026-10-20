import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Alert from './Alert';
import { testA11y } from '../../../tests/utils/a11y-test-utils';

/*
  Description: Test suite for the Alert component. Contains unit tests to verify rendering, different types, title inclusion, and close functionality.
  Purpose: Ensures the Alert component functions correctly and displays messages as expected across various configurations.
*/

describe('Alert Component', () => {
  const defaultProps = {
    children: 'This is an alert message',
  };

  it('renders with default info type', () => {
    render(<Alert {...defaultProps} />);
    
    expect(screen.getByText('This is an alert message')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('bg-blue-50');
    expect(screen.getByRole('alert')).toHaveClass('border-blue-200');
  });

  it('renders with success type', () => {
    render(<Alert {...defaultProps} type="success" />);
    
    expect(screen.getByRole('alert')).toHaveClass('bg-green-50');
    expect(screen.getByRole('alert')).toHaveClass('border-green-200');
  });

  it('renders with warning type', () => {
    render(<Alert {...defaultProps} type="warning" />);
    
    expect(screen.getByRole('alert')).toHaveClass('bg-yellow-50');
    expect(screen.getByRole('alert')).toHaveClass('border-yellow-200');
  });

  it('renders with error type', () => {
    render(<Alert {...defaultProps} type="error" />);
    
    expect(screen.getByRole('alert')).toHaveClass('bg-red-50');
    expect(screen.getByRole('alert')).toHaveClass('border-red-200');
  });

  it('renders with a title when provided', () => {
    render(<Alert {...defaultProps} title="Alert Title" />);
    
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = jest.fn();
    render(<Alert {...defaultProps} onClose={onClose} />);
    
    const closeButton = screen.getByLabelText('Close');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('does not render close button when onClose is not provided', () => {
    render(<Alert {...defaultProps} />);
    
    expect(screen.queryByLabelText('Close')).not.toBeInTheDocument();
  });

  it('applies additional className when provided', () => {
    render(<Alert {...defaultProps} className="custom-class" />);
    
    expect(screen.getByRole('alert')).toHaveClass('custom-class');
  });

  it('passes accessibility test', async () => {
    await testA11y(
      <Alert title="Accessible Alert">
        This is an accessible alert message
      </Alert>
    );
  });
}); 