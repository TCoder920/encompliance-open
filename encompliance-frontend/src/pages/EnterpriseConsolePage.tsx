/*
  Description: Enterprise console for RBAC, multi-facility analytics, and policy distribution.
*/

import React, { useEffect, useState } from 'react';
import FeaturePreview from '../components/ui/FeaturePreview';
import ErrorMessage from '../components/ErrorMessage';
import enterpriseService, {
  CrossFacilityAnalytics,
  RolePayload,
  RoleAssignmentPayload,
  PolicyDistributionPayload,
  EscalationPolicy,
  EscalationPolicyPayload,
  EscalationStepPayload,
  OverrideRequest,
} from '../services/enterpriseService';

const EnterpriseConsolePage: React.FC = () => {
  const [analytics, setAnalytics] = useState<CrossFacilityAnalytics | null>(null);
  const [rolePayload, setRolePayload] = useState<RolePayload>({ name: '', permissions: [] });
  const [assignmentPayload, setAssignmentPayload] = useState<RoleAssignmentPayload>({
    user_id: 0,
    role_id: 0,
  });
  const [distributionPayload, setDistributionPayload] = useState<PolicyDistributionPayload>({
    policy_id: 0,
    facility_ids: [],
  });
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [escalations, setEscalations] = useState<EscalationPolicy[]>([]);
  const [escalationPayload, setEscalationPayload] = useState<EscalationPolicyPayload>({
    name: '',
    incidentType: '',
    description: '',
    steps: [],
  });
  const [newStep, setNewStep] = useState<EscalationStepPayload>({
    delayMinutes: 0,
    channel: 'email',
    targetRole: 'facility_admin',
  });
  const [overrideRequests, setOverrideRequests] = useState<OverrideRequest[]>([]);
  const [overrideAction, setOverrideAction] = useState<string>('policy_override');
  const [overridePayloadRaw, setOverridePayloadRaw] = useState<string>('{}');
  const [overrideNotes, setOverrideNotes] = useState<string>('');

  useEffect(() => {
    (async () => {
      try {
        const data = await enterpriseService.fetchAnalytics();
        setAnalytics(data);
      } catch (err) {
        console.error('Analytics fetch failed', err);
        setError('Unable to load analytics.');
      }
      try {
        const policyList = await enterpriseService.fetchEscalationPolicies();
        setEscalations(policyList);
      } catch (err) {
        console.error('Escalation policy fetch failed', err);
      }
      try {
        const requests = await enterpriseService.fetchOverrideRequests('pending');
        setOverrideRequests(requests);
      } catch (err) {
        console.error('Override request fetch failed', err);
      }
    })();
  }, []);

  const handleCreateRole = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await enterpriseService.createRole(rolePayload);
      setRolePayload({ name: '', permissions: [] });
      setStatus('Role created.');
    } catch (err) {
      console.error('Role creation failed', err);
      setError('Unable to create role.');
    }
  };

  const handleAssignRole = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await enterpriseService.assignRole(assignmentPayload);
      setStatus('Role assigned.');
    } catch (err) {
      console.error('Assignment failed', err);
      setError('Unable to assign role.');
    }
  };

  const handlePolicyDistribution = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await enterpriseService.distributePolicy(distributionPayload);
      setStatus('Policy distribution queued.');
    } catch (err) {
      console.error('Distribution failed', err);
      setError('Unable to distribute policy.');
    }
  };

  const handleAddStep = () => {
    setEscalationPayload((prev) => ({
      ...prev,
      steps: [...prev.steps, newStep],
    }));
    setNewStep({
      delayMinutes: 0,
      channel: 'email',
      targetRole: 'facility_admin',
    });
  };

  const handleCreateEscalation = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const created = await enterpriseService.createEscalationPolicy(escalationPayload);
      setStatus('Escalation policy created.');
      setEscalations((prev) => [created, ...prev]);
      setEscalationPayload({
        name: '',
        incidentType: '',
        description: '',
        steps: [],
      });
    } catch (err) {
      console.error('Escalation policy creation failed', err);
      setError('Unable to create escalation policy.');
    }
  };

  const handleTriggerEscalation = async (policyId: number) => {
    try {
      await enterpriseService.triggerEscalationTest(policyId);
      setStatus('Escalation test triggered.');
    } catch (err) {
      console.error('Escalation trigger failed', err);
      setError('Failed to trigger escalation.');
    }
  };

  const handleSubmitOverride = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      let parsedPayload = {};
      if (overridePayloadRaw.trim()) {
        parsedPayload = JSON.parse(overridePayloadRaw);
      }
      await enterpriseService.submitOverrideRequest({
        actionType: overrideAction,
        payload: parsedPayload,
      });
      setStatus('Override request submitted.');
      setOverridePayloadRaw('{}');
    } catch (err) {
      console.error('Override request failed', err);
      setError('Unable to submit override request. Ensure payload is valid JSON.');
    }
  };

  const handleResolveOverride = async (requestId: number, action: 'approve' | 'reject') => {
    try {
      await enterpriseService.resolveOverrideRequest(requestId, action, overrideNotes || undefined);
      setStatus(`Override ${action}d.`);
      const updated = await enterpriseService.fetchOverrideRequests('pending');
      setOverrideRequests(updated);
    } catch (err) {
      console.error('Override resolution failed', err);
      setError('Unable to resolve override request.');
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Enterprise Console</h1>
      {error && <ErrorMessage message={error} />}
      {status && <div className="text-sm text-emerald-600">{status}</div>}

      <FeaturePreview featureKey="enterprise_console">
        <section className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
          <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-white">Cross-Facility Analytics</h2>
          {analytics ? (
            <div className="space-y-2 text-sm text-gray-700 dark:text-gray-200">
              <p>Total facilities: {analytics.total_facilities}</p>
              <p>Staff count: {analytics.staff_count}</p>
              <p>Pending policy distributions: {analytics.policy_distribution_pending}</p>
              <table className="w-full mt-3 text-xs">
                <thead>
                  <tr className="text-left">
                    <th>Facility</th>
                    <th>Staff</th>
                    <th>Open Policies</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.facilities.map((facility) => (
                    <tr key={facility.facility_id}>
                      <td>{facility.facility_name}</td>
                      <td>{facility.active_staff}</td>
                      <td>{facility.open_policies}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Loading analytics...</p>
          )}
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <form
            className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-2"
            onSubmit={handleCreateRole}
          >
            <h3 className="font-semibold">Create Role</h3>
            <input
              type="text"
              placeholder="Role name"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={rolePayload.name}
              onChange={(e) => setRolePayload((prev) => ({ ...prev, name: e.target.value }))}
              required
            />
            <input
              type="text"
              placeholder="Permissions comma separated"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              onChange={(e) =>
                setRolePayload((prev) => ({
                  ...prev,
                  permissions: e.target.value.split(',').map((p) => p.trim()),
                }))
              }
            />
            <button className="px-3 py-2 rounded-lg bg-blue-600 text-white text-sm font-semibold">Create</button>
          </form>

          <form
            className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-2"
            onSubmit={handleAssignRole}
          >
            <h3 className="font-semibold">Assign Role</h3>
            <input
              type="number"
              placeholder="User ID"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={assignmentPayload.user_id || ''}
              onChange={(e) => setAssignmentPayload((prev) => ({ ...prev, user_id: Number(e.target.value) }))}
              required
            />
            <input
              type="number"
              placeholder="Role ID"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={assignmentPayload.role_id || ''}
              onChange={(e) => setAssignmentPayload((prev) => ({ ...prev, role_id: Number(e.target.value) }))}
              required
            />
            <input
              type="number"
              placeholder="Facility ID (optional)"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={assignmentPayload.facility_id || ''}
              onChange={(e) =>
                setAssignmentPayload((prev) => ({ ...prev, facility_id: Number(e.target.value) || undefined }))
              }
            />
            <button className="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-semibold">Assign</button>
          </form>

          <form
            className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-2"
            onSubmit={handlePolicyDistribution}
          >
            <h3 className="font-semibold">Policy Distribution</h3>
            <input
              type="number"
              placeholder="Policy ID"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={distributionPayload.policy_id || ''}
              onChange={(e) =>
                setDistributionPayload((prev) => ({ ...prev, policy_id: Number(e.target.value) }))
              }
              required
            />
            <input
              type="text"
              placeholder="Facility IDs (comma separated)"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              onChange={(e) =>
                setDistributionPayload((prev) => ({
                  ...prev,
                  facility_ids: e.target.value
                    .split(',')
                    .map((id) => Number(id.trim()))
                    .filter(Boolean),
                }))
              }
              required
            />
            <textarea
              placeholder="Notes"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[60px]"
              onChange={(e) => setDistributionPayload((prev) => ({ ...prev, notes: e.target.value }))}
            />
            <button className="px-3 py-2 rounded-lg bg-purple-600 text-white text-sm font-semibold">Distribute</button>
          </form>
        </section>

        <section className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <form
            className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-3"
            onSubmit={handleCreateEscalation}
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">Escalation Rule Builder</h3>
            <input
              type="text"
              placeholder="Policy name"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={escalationPayload.name}
              onChange={(e) => setEscalationPayload((prev) => ({ ...prev, name: e.target.value }))}
              required
            />
            <input
              type="text"
              placeholder="Incident type (e.g., task_overdue)"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={escalationPayload.incidentType}
              onChange={(e) => setEscalationPayload((prev) => ({ ...prev, incidentType: e.target.value }))}
              required
            />
            <textarea
              placeholder="Description"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={escalationPayload.description}
              onChange={(e) => setEscalationPayload((prev) => ({ ...prev, description: e.target.value }))}
            />
            <div className="rounded-lg border border-dashed border-gray-300 p-3 space-y-2">
              <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">Add escalation step</p>
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  min={0}
                  placeholder="Delay (minutes)"
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-2 py-1 text-sm"
                  value={newStep.delayMinutes}
                  onChange={(e) => setNewStep((prev) => ({ ...prev, delayMinutes: Number(e.target.value) }))}
                />
                <select
                  className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-2 py-1 text-sm"
                  value={newStep.channel}
                  onChange={(e) => setNewStep((prev) => ({ ...prev, channel: e.target.value }))}
                >
                  <option value="email">Email</option>
                  <option value="sms">SMS</option>
                  <option value="push">Push</option>
                  <option value="pager">Pager</option>
                </select>
              </div>
              <input
                type="text"
                placeholder="Target role (facility_admin, organization_manager)"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-2 py-1 text-sm"
                value={newStep.targetRole || ''}
                onChange={(e) => setNewStep((prev) => ({ ...prev, targetRole: e.target.value }))}
              />
              <textarea
                placeholder="Message template"
                className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-2 py-1 text-sm"
                value={newStep.messageTemplate || ''}
                onChange={(e) => setNewStep((prev) => ({ ...prev, messageTemplate: e.target.value }))}
              />
              <button
                type="button"
                onClick={handleAddStep}
                className="w-full rounded-lg border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200"
              >
                Add Step
              </button>
            </div>
            {escalationPayload.steps.length > 0 && (
              <div className="rounded-lg border border-gray-200 p-3 text-xs text-gray-600 dark:border-gray-800 dark:text-gray-200">
                <p className="font-semibold mb-2">Configured Steps</p>
                <ol className="list-decimal pl-4 space-y-1">
                  {escalationPayload.steps.map((step, index) => (
                    <li key={`${step.channel}-${index}`}>
                      {step.channel} after {step.delayMinutes}m → {step.targetRole || 'custom target'}
                    </li>
                  ))}
                </ol>
              </div>
            )}
            <button className="w-full rounded-lg bg-orange-600 px-3 py-2 text-sm font-semibold text-white">
              Create Escalation Policy
            </button>
          </form>

          <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">Existing Policies</h3>
            {escalations.length === 0 ? (
              <p className="text-sm text-gray-500">No policies configured.</p>
            ) : (
              <div className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
                {escalations.map((policy) => (
                  <div key={policy.id} className="rounded-lg border border-gray-100 dark:border-gray-800 p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">{policy.name}</p>
                        <p className="text-xs text-gray-500">Incident: {policy.incidentType}</p>
                      </div>
                      <button
                        onClick={() => handleTriggerEscalation(policy.id)}
                        className="rounded-md border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-200"
                      >
                        Send Test
                      </button>
                    </div>
                    <ul className="mt-2 text-xs text-gray-500">
                      {policy.steps.map((step) => (
                        <li key={step.id}>
                          Step {step.stepNumber}: {step.channel} after {step.delayMinutes}m
                        </li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        <section className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <form
            className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-3"
            onSubmit={handleSubmitOverride}
          >
            <h3 className="font-semibold text-gray-900 dark:text-white">Request Manager Override</h3>
            <input
              type="text"
              placeholder="Action type"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={overrideAction}
              onChange={(e) => setOverrideAction(e.target.value)}
              required
            />
            <textarea
              placeholder='Payload JSON (e.g., {"policyId":123})'
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm min-h-[100px]"
              value={overridePayloadRaw}
              onChange={(e) => setOverridePayloadRaw(e.target.value)}
            />
            <button className="w-full rounded-lg bg-slate-800 px-3 py-2 text-sm font-semibold text-white">
              Submit Override Request
            </button>
          </form>

          <div className="bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 rounded-xl p-4 space-y-3">
            <h3 className="font-semibold text-gray-900 dark:text-white">Pending Override Requests</h3>
            {overrideRequests.length === 0 ? (
              <p className="text-sm text-gray-500">No pending overrides.</p>
            ) : (
              <div className="space-y-3 text-sm text-gray-600 dark:text-gray-300">
                {overrideRequests.map((request) => (
                  <div key={request.id} className="rounded-lg border border-gray-100 dark:border-gray-800 p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white">{request.action_type}</p>
                        <p className="text-xs text-gray-500">
                          Requested by user {request.requested_by_user_id} on{' '}
                          {new Date(request.created_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={() => handleResolveOverride(request.id, 'approve')}
                          className="rounded-md border border-gray-300 px-2 py-1 text-xs font-semibold text-emerald-600 hover:bg-gray-50 dark:border-gray-600"
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          onClick={() => handleResolveOverride(request.id, 'reject')}
                          className="rounded-md border border-gray-300 px-2 py-1 text-xs font-semibold text-red-600 hover:bg-gray-50 dark:border-gray-600"
                        >
                          Reject
                        </button>
                      </div>
                    </div>
                    <pre className="mt-2 overflow-x-auto rounded bg-gray-100 p-2 text-xs dark:bg-gray-800">
                      {JSON.stringify(request.payload, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
            <textarea
              placeholder="Resolution notes"
              className="w-full rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/80 px-3 py-2 text-sm"
              value={overrideNotes}
              onChange={(e) => setOverrideNotes(e.target.value)}
            />
          </div>
        </section>
      </FeaturePreview>
    </div>
  );
};

export default EnterpriseConsolePage;

