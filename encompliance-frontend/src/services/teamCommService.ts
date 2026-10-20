import api from './api';

/*
  Description: Team communication service for channels, messages, and email campaigns.
  Purpose: Wraps new backend endpoints powering team chat and outreach.
*/

export interface TeamChannel {
  id: number;
  name: string;
  description?: string;
  is_private: boolean;
  facility_id: number;
  created_by: number;
  created_at: string;
}

export interface TeamChannelPayload {
  name: string;
  description?: string;
  is_private?: boolean;
}

export interface TeamMessage {
  id: number;
  channel_id: number;
  facility_id: number;
  sender_id: number;
  content: string;
  attachments?: Record<string, unknown>[] | null;
  mentions?: number[] | null;
  created_at: string;
}

export interface TeamMessagePayload {
  content: string;
  attachments?: Record<string, unknown>[];
  mentions?: number[];
}

export interface EmailCampaignPayload {
  subject: string;
  body: string;
  template_type?: string;
  target_roles?: string[];
  scheduled_for?: string | null;
}

export interface EmailCampaign {
  id: number;
  facility_id: number;
  subject: string;
  body: string;
  template_type?: string;
  target_roles?: string[];
  status: string;
  created_at: string;
}

export const teamCommService = {
  async getChannels(): Promise<TeamChannel[]> {
    const response = await api.get<TeamChannel[]>('/team-comms/channels');
    return response.data;
  },

  async createChannel(payload: TeamChannelPayload): Promise<TeamChannel> {
    const response = await api.post<TeamChannel>('/team-comms/channels', payload);
    return response.data;
  },

  async getMessages(channelId: number, limit = 50): Promise<TeamMessage[]> {
    const response = await api.get<TeamMessage[]>(
      `/team-comms/channels/${channelId}/messages`,
      { params: { limit } }
    );
    return response.data;
  },

  async postMessage(channelId: number, payload: TeamMessagePayload): Promise<TeamMessage> {
    const response = await api.post<TeamMessage>(
      `/team-comms/channels/${channelId}/messages`,
      payload
    );
    return response.data;
  },

  async createEmailCampaign(payload: EmailCampaignPayload): Promise<EmailCampaign> {
    const response = await api.post<EmailCampaign>('/team-comms/email-campaigns', payload);
    return response.data;
  },
};

export default teamCommService;

