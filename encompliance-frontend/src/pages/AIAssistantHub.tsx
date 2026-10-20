/*
  Description: Central hub for AI-assisted tooling (forms, multimodal chat, customer service).
  Purpose: Provides facility admins a single workspace to leverage new AI endpoints safely.
*/

import React, { useState } from 'react';
import { Paperclip, FileText, Mic, AlertTriangle, Send } from 'lucide-react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import {
  requestFormBlueprint,
  FormBlueprintResponse,
  FormBlueprintPayload,
  sendMultimodalMessage,
  MultimodalAttachment,
  MultimodalChatResponse,
  MultimodalChatPayload,
  triageCustomerTicket,
  CustomerServiceAssistantResponse,
} from '../services/aiService';
import { useAuth } from '../contexts/AuthContext';
import { getTierFromSubscriptionStatus } from '../utils/tiers';
import { canUseFeature } from '../utils/accessControl';

const MAX_ATTACHMENT_BYTES = 1024 * 1024 * 2; // 2MB

const AIAssistantHub: React.FC = () => {
  const { user } = useAuth();
  const userTier = getTierFromSubscriptionStatus(user?.subscription_status);
  const canUse = canUseFeature(userTier, 'ai_pro_mode');

  const [formPayload, setFormPayload] = useState<FormBlueprintPayload>({
    form_name: '',
    form_goal: '',
    facility_type: '',
    jurisdiction: '',
    context_summary: '',
  });
  const [formResult, setFormResult] = useState<FormBlueprintResponse | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [chatPrompt, setChatPrompt] = useState('');
  const [chatAttachments, setChatAttachments] = useState<MultimodalAttachment[]>([]);
  const [chatResponse, setChatResponse] = useState<MultimodalChatResponse | null>(null);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState<string | null>(null);

  const [ticketForm, setTicketForm] = useState({
    subject: '',
    description: '',
    priority: 'low',
    tags: '',
  });
  const [ticketResponse, setTicketResponse] = useState<CustomerServiceAssistantResponse | null>(null);
  const [ticketLoading, setTicketLoading] = useState(false);
  const [ticketError, setTicketError] = useState<string | null>(null);

  const handleFormChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = event.target;
    setFormPayload((prev) => ({ ...prev, [name]: value }));
  };

  const handleFormSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse) return;
    setFormLoading(true);
    setFormError(null);
    try {
      const payload: FormBlueprintPayload = {
        ...formPayload,
        facility_type: formPayload.facility_type || undefined,
        jurisdiction: formPayload.jurisdiction || undefined,
        context_summary: formPayload.context_summary || undefined,
      };
      const response = await requestFormBlueprint(payload);
      setFormResult(response);
    } catch (error) {
      console.error('Failed to generate form blueprint', error);
      setFormError('Unable to generate form blueprint at this time.');
    } finally {
      setFormLoading(false);
    }
  };

  const toBase64 = (file: File) => {
    return new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = reader.result?.toString() || '';
        const base64 = result.includes(',') ? result.split(',')[1] : result;
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleAttachmentUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;
    setChatError(null);
    const newAttachments: MultimodalAttachment[] = [];

    for (const file of Array.from(files)) {
      if (file.size > MAX_ATTACHMENT_BYTES) {
        setChatError(`Attachment ${file.name} exceeds 2MB limit.`);
        continue;
      }
      if (!file.type.startsWith('image/') && !file.type.startsWith('audio/')) {
        setChatError('Only image or audio files are supported.');
        continue;
      }

      const base64 = await toBase64(file);
      newAttachments.push({
        kind: file.type.startsWith('image/') ? 'image' : 'audio',
        filename: file.name,
        mime_type: file.type,
        content_base64: base64,
      });
    }

    setChatAttachments(newAttachments);
  };

  const handleChatSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse || !chatPrompt.trim()) return;
    setChatLoading(true);
    setChatError(null);
    try {
      const payload: MultimodalChatPayload = {
        prompt: chatPrompt,
        facility_type: formPayload.facility_type || undefined,
        attachments: chatAttachments,
      };
      const response = await sendMultimodalMessage(payload);
      setChatResponse(response);
    } catch (error) {
      console.error('Multimodal chat failed', error);
      setChatError('Unable to reach the AI assistant. Please retry.');
    } finally {
      setChatLoading(false);
    }
  };

  const handleTicketChange = (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    setTicketForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleTicketSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canUse) return;
    setTicketLoading(true);
    setTicketError(null);
    try {
      const tags = ticketForm.tags
        .split(',')
        .map((tag) => tag.trim())
        .filter(Boolean);
      const response = await triageCustomerTicket({
        subject: ticketForm.subject,
        description: ticketForm.description,
        priority: ticketForm.priority as 'low' | 'medium' | 'high' | 'urgent',
        tags,
      });
      setTicketResponse(response);
    } catch (error) {
      console.error('Customer service triage failed', error);
      setTicketError('Unable to triage ticket. Please try again later.');
    } finally {
      setTicketLoading(false);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Assistant Hub</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Generate compliant forms, handle multimodal conversations, and triage support requests.
          </p>
        </div>
      </div>

      {!canUse && (
        <ErrorMessage message="Upgrade to the Pro tier to unlock AI Assistant tools." />
      )}

      <FeaturePreview featureKey="ai_pro_mode">
        <div className="space-y-6">
          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <FileText className="w-5 h-5 text-blue-500" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Form Assistant</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Describe the form goal and receive recommended sections and fields.
                </p>
              </div>
            </div>

            {formError && <ErrorMessage message={formError} />}

            <form className="grid gap-4" onSubmit={handleFormSubmit}>
              <input
                type="text"
                name="form_name"
                placeholder="Form name (e.g., Incident Report)"
                className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                value={formPayload.form_name}
                onChange={handleFormChange}
                required
                disabled={!canUse || formLoading}
              />
              <textarea
                name="form_goal"
                placeholder="Describe the compliance goal and required outcomes"
                className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[80px]"
                value={formPayload.form_goal}
                onChange={handleFormChange}
                required
                disabled={!canUse || formLoading}
              />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <input
                  type="text"
                  name="facility_type"
                  placeholder="Facility type (optional)"
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  value={formPayload.facility_type}
                  onChange={handleFormChange}
                  disabled={!canUse || formLoading}
                />
                <input
                  type="text"
                  name="jurisdiction"
                  placeholder="Jurisdiction (optional)"
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  value={formPayload.jurisdiction}
                  onChange={handleFormChange}
                  disabled={!canUse || formLoading}
                />
                <textarea
                  name="context_summary"
                  placeholder="Additional context (optional)"
                  className="md:col-span-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[60px]"
                  value={formPayload.context_summary}
                  onChange={handleFormChange}
                  disabled={!canUse || formLoading}
                />
              </div>

              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold shadow hover:bg-blue-500 disabled:opacity-50"
                disabled={!canUse || formLoading}
              >
                Generate Blueprint
              </button>
            </form>

            {formResult && (
              <div className="mt-6 space-y-4">
                <p className="text-sm text-gray-700 dark:text-gray-200">{formResult.summary}</p>
                {formResult.sections.map((section) => (
                  <div key={section.title} className="border border-gray-100 dark:border-gray-800 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 dark:text-white">{section.title}</h3>
                    {section.description && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">{section.description}</p>
                    )}
                    <ul className="mt-3 space-y-2">
                      {section.fields.map((field) => (
                        <li key={field.name} className="text-sm text-gray-700 dark:text-gray-200">
                          <span className="font-medium">{field.label}</span> • {field.data_type}
                          {field.required ? ' (required)' : ''}
                          {field.helper_text && <p className="text-xs text-gray-500">{field.helper_text}</p>}
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Paperclip className="w-5 h-5 text-purple-500" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Multimodal Chat</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Send text with optional images or audio for richer analysis.
                </p>
              </div>
            </div>

            {chatError && <ErrorMessage message={chatError} />}

            <form className="space-y-3" onSubmit={handleChatSubmit}>
              <textarea
                value={chatPrompt}
                onChange={(e) => setChatPrompt(e.target.value)}
                placeholder="Describe your question and reference any attached context."
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[100px]"
                disabled={!canUse || chatLoading}
                required
              />
              <input
                type="file"
                accept="image/*,audio/*"
                multiple
                onChange={handleAttachmentUpload}
                disabled={!canUse || chatLoading}
                className="text-sm text-gray-600 dark:text-gray-300"
              />
              {chatAttachments.length > 0 && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  {chatAttachments.length} attachment(s) ready.
                </div>
              )}
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-purple-600 text-white text-sm font-semibold shadow hover:bg-purple-500 disabled:opacity-50"
                disabled={!canUse || chatLoading}
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </form>

            {chatResponse && (
              <div className="mt-4 border border-gray-100 dark:border-gray-800 rounded-lg p-4">
                <p className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-line">
                  {chatResponse.reply}
                </p>
                {chatResponse.safety_notes.length > 0 && (
                  <div className="mt-3 flex items-center gap-2 text-xs text-amber-600 dark:text-amber-300">
                    <AlertTriangle className="w-4 h-4" />
                    {chatResponse.safety_notes.join(' ')}
                  </div>
                )}
              </div>
            )}
          </section>

          <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <Mic className="w-5 h-5 text-emerald-500" />
              <div>
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Customer Service Triage</h2>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Get AI-backed recommendations before escalating to staff.
                </p>
              </div>
            </div>

            {ticketError && <ErrorMessage message={ticketError} />}

            <form className="space-y-3" onSubmit={handleTicketSubmit}>
              <input
                type="text"
                name="subject"
                placeholder="Ticket subject"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                value={ticketForm.subject}
                onChange={handleTicketChange}
                required
                disabled={!canUse || ticketLoading}
              />
              <textarea
                name="description"
                placeholder="Describe the customer issue or compliance request"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[90px]"
                value={ticketForm.description}
                onChange={handleTicketChange}
                required
                disabled={!canUse || ticketLoading}
              />
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <select
                  name="priority"
                  value={ticketForm.priority}
                  onChange={handleTicketChange}
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  disabled={!canUse || ticketLoading}
                >
                  <option value="low">Low priority</option>
                  <option value="medium">Medium priority</option>
                  <option value="high">High priority</option>
                  <option value="urgent">Urgent</option>
                </select>
                <input
                  type="text"
                  name="tags"
                  placeholder="Tags (comma separated)"
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
                  value={ticketForm.tags}
                  onChange={handleTicketChange}
                  disabled={!canUse || ticketLoading}
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 text-white text-sm font-semibold shadow hover:bg-emerald-500 disabled:opacity-50"
                disabled={!canUse || ticketLoading}
              >
                Triage Ticket
              </button>
            </form>

            {ticketResponse && (
              <div className="mt-4 border border-gray-100 dark:border-gray-800 rounded-lg p-4 text-sm text-gray-800 dark:text-gray-200">
                <p className="font-semibold">Classification: {ticketResponse.classification}</p>
                <ul className="list-disc ml-4 mt-2 space-y-1">
                  {ticketResponse.suggested_actions.map((action) => (
                    <li key={action}>{action}</li>
                  ))}
                </ul>
                <p className="mt-3">
                  Auto Attempt:{' '}
                  {ticketResponse.auto_resolution_attempted ? 'Attempted' : 'Not attempted'}
                  {' • '}
                  {ticketResponse.requires_human_review ? 'Escalation recommended' : 'Resolved'}
                </p>
                <p className="mt-2 italic text-gray-600 dark:text-gray-400">
                  Customer Note: {ticketResponse.customer_facing_summary}
                </p>
              </div>
            )}
          </section>
        </div>
      </FeaturePreview>
    </div>
  );
};

export default AIAssistantHub;

