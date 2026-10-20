/*
  Description: Team Communication & Email Campaign page.
  Purpose: Provides lightweight Slack-like chat plus admin email tooling.
*/

import React, { useEffect, useState } from 'react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import teamCommService, {
  TeamChannel,
  TeamMessage,
  TeamChannelPayload,
  TeamMessagePayload,
  EmailCampaignPayload,
} from '../services/teamCommService';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';
import { Send, Mail, MessageSquare } from 'lucide-react';

const TeamCommunicationPage: React.FC = () => {
  const { user } = useAuth();
  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'team_communication');

  const [channels, setChannels] = useState<TeamChannel[]>([]);
  const [selectedChannel, setSelectedChannel] = useState<TeamChannel | null>(null);
  const [messages, setMessages] = useState<TeamMessage[]>([]);
  const [messageContent, setMessageContent] = useState('');
  const [channelForm, setChannelForm] = useState<TeamChannelPayload>({ name: '', description: '' });
  const [campaignForm, setCampaignForm] = useState<EmailCampaignPayload>({
    subject: '',
    body: '',
    template_type: 'announcement',
    target_roles: ['staff'],
  });
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (canUse) {
      loadChannels();
    } else {
      setChannels([]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canUse]);

  const loadChannels = async () => {
    try {
      const response = await teamCommService.getChannels();
      setChannels(response);
      if (response.length > 0) {
        setSelectedChannel(response[0]);
        loadMessages(response[0].id);
      }
    } catch (err) {
      console.error('Failed to load channels', err);
      setError('Unable to load channels.');
    }
  };

  const loadMessages = async (channelId: number) => {
    try {
      const response = await teamCommService.getMessages(channelId);
      setMessages(response);
    } catch (err) {
      console.error('Failed to load messages', err);
      setError('Unable to load messages.');
    }
  };

  const handleChannelSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse) return;
    try {
      await teamCommService.createChannel(channelForm);
      setChannelForm({ name: '', description: '' });
      loadChannels();
    } catch (err) {
      console.error('Channel creation failed', err);
      setError('Unable to create channel.');
    }
  };

  const handleMessageSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse || !selectedChannel || !messageContent.trim()) return;
    try {
      const payload: TeamMessagePayload = { content: messageContent };
      await teamCommService.postMessage(selectedChannel.id, payload);
      setMessageContent('');
      loadMessages(selectedChannel.id);
    } catch (err) {
      console.error('Message send failed', err);
      setError('Unable to send message.');
    }
  };

  const handleCampaignSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse) return;
    try {
      await teamCommService.createEmailCampaign({
        ...campaignForm,
        target_roles: campaignForm.target_roles?.filter(Boolean),
      });
      setStatusMessage('Campaign queued for delivery.');
      setCampaignForm({
        subject: '',
        body: '',
        template_type: 'announcement',
        target_roles: ['staff'],
      });
    } catch (err) {
      console.error('Campaign creation failed', err);
      setError('Unable to create email campaign.');
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Team Communication</h1>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Collaborate across channels and send compliant announcements.
        </p>
      </div>

      {error && <ErrorMessage message={error} />}
      {statusMessage && <div className="text-sm text-emerald-600">{statusMessage}</div>}

      <FeaturePreview featureKey="team_communication">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <section className="lg:col-span-2 bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="w-5 h-5 text-blue-500" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Channels</h2>
            </div>
            <div className="flex gap-4">
              <div className="w-48 space-y-2">
                {channels.map((channel) => (
                  <button
                    key={channel.id}
                    onClick={() => {
                      setSelectedChannel(channel);
                      loadMessages(channel.id);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm ${
                      selectedChannel?.id === channel.id
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200'
                    }`}
                    disabled={!canUse}
                  >
                    {channel.name}
                  </button>
                ))}
                <form className="space-y-2" onSubmit={handleChannelSubmit}>
                  <input
                    type="text"
                    placeholder="New channel name"
                    className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-2 py-1 text-sm"
                    value={channelForm.name}
                    onChange={(e) => setChannelForm((prev) => ({ ...prev, name: e.target.value }))}
                    disabled={!canUse}
                    required
                  />
                  <button
                    type="submit"
                    className="w-full bg-blue-600 text-white rounded-lg py-1 text-sm font-semibold disabled:opacity-50"
                    disabled={!canUse}
                  >
                    Create
                  </button>
                </form>
              </div>
              <div className="flex-1">
                <div className="h-64 overflow-y-auto border border-gray-100 dark:border-gray-800 rounded-lg p-3 bg-gray-50 dark:bg-gray-800/40">
                  {messages.length === 0 && (
                    <p className="text-sm text-gray-500">No messages yet.</p>
                  )}
                  {messages.map((message) => (
                    <div key={message.id} className="mb-3">
                      <p className="text-sm text-gray-700 dark:text-gray-200">{message.content}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(message.created_at).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
                <form className="mt-3 flex gap-2" onSubmit={handleMessageSubmit}>
                  <input
                    type="text"
                    placeholder="Write a message"
                    className="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                    value={messageContent}
                    onChange={(e) => setMessageContent(e.target.value)}
                    disabled={!canUse || !selectedChannel}
                    required
                  />
                  <button
                    type="submit"
                    className="inline-flex items-center gap-2 px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:opacity-50"
                    disabled={!canUse || !selectedChannel}
                  >
                    <Send className="w-4 h-4" />
                    Send
                  </button>
                </form>
              </div>
            </div>
          </section>

          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-4">
              <Mail className="w-5 h-5 text-emerald-500" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Email Campaign</h2>
            </div>

            <form className="space-y-3" onSubmit={handleCampaignSubmit}>
              <input
                type="text"
                placeholder="Subject"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                value={campaignForm.subject}
                onChange={(e) => setCampaignForm((prev) => ({ ...prev, subject: e.target.value }))}
                required
                disabled={!canUse}
              />
              <textarea
                placeholder="Body"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[120px]"
                value={campaignForm.body}
                onChange={(e) => setCampaignForm((prev) => ({ ...prev, body: e.target.value }))}
                required
                disabled={!canUse}
              />
              <input
                type="text"
                placeholder="Target roles (comma separated)"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                value={campaignForm.target_roles?.join(', ') || ''}
                onChange={(e) =>
                  setCampaignForm((prev) => ({
                    ...prev,
                    target_roles: e.target.value.split(',').map((tag) => tag.trim()),
                  }))
                }
                disabled={!canUse}
              />
              <button
                type="submit"
                className="w-full bg-emerald-600 text-white rounded-lg py-2 text-sm font-semibold disabled:opacity-50"
                disabled={!canUse}
              >
                Queue Campaign
              </button>
            </form>
          </section>
        </div>
      </FeaturePreview>
    </div>
  );
};

export default TeamCommunicationPage;

