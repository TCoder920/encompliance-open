/*
  Description: Test suite for the Modal component. Contains unit tests to verify the modal's rendering, open/close behavior, size variations, and accessibility.
  Purpose: Ensures the Modal component functions correctly and displays content as expected in various scenarios.
*/
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Modal from './Modal';
import { testA11y } from '../../../tests/utils/a11y-test-utils';

describe('Modal Component', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    title: 'Test Modal',
    children: <div>Modal content</div>,
  };

  beforeEach(() => {
    // Reset mocks before each test
    jest.clearAllMocks();
  });

  it('renders when isOpen is true', () => {
    render(<Modal {...defaultProps} />);
    
    expect(screen.getByText('Test Modal')).toBeInTheDocument();
    expect(screen.getByText('Modal content')).toBeInTheDocument();
  });

  it('does not render when isOpen is false', () => {
    render(<Modal {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText('Test Modal')).not.toBeInTheDocument();
    expect(screen.queryByText('Modal content')).not.toBeInTheDocument();
  });

  it('calls onClose when close button is clicked', () => {
    render(<Modal {...defaultProps} />);
    
    const closeButton = screen.getByLabelText('Close');
    fireEvent.click(closeButton);
    
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
  });

  it('renders with footer when provided', () => {
    const footer = <button>Submit</button>;
    render(<Modal {...defaultProps} footer={footer} />);
    
    expect(screen.getByText('Submit')).toBeInTheDocument();
  });

  it('uses correct size class based on size prop', () => {
    const { container, rerender } = render(<Modal {...defaultProps} size="sm" />);
    expect(container.querySelector('.max-w-md')).toBeInTheDocument();
    
    rerender(<Modal {...defaultProps} size="lg" />);
    expect(container.querySelector('.max-w-2xl')).toBeInTheDocument();
  });

  it('has correct accessibility attributes', () => {
    render(<Modal {...defaultProps} />);
    
    const dialog = screen.getByRole('dialog');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('aria-labelledby', 'modal-title');
  });

  it('passes accessibility test', async () => {
    await testA11y(
      <Modal
        isOpen={true}
        onClose={() => {}}
        title="Accessible Modal"
      >
        <p>This is an accessible modal dialog</p>
      </Modal>
    );
  });
}); 