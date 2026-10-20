import '@testing-library/jest-dom';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from '../Sidebar';

expect.extend(toHaveNoViolations);

jest.mock('../../contexts/AuthContext', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    user: {
      subscription_status: 'pro',
      user_role: 'facility_admin'
    }
  })
}));

describe('Sidebar accessibility', () => {
  it('has no detectable axe violations', async () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Sidebar />
      </MemoryRouter>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

