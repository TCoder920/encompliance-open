import api from './api';

export interface GoogleOAuthConfig {
  clientId: string;
  scopes: string[];
}

export const googleIntegrationService = {
  async getConfig(): Promise<GoogleOAuthConfig> {
    const response = await api.get<GoogleOAuthConfig>('/auth/google/config');
    return response.data;
  },
};

export default googleIntegrationService;

