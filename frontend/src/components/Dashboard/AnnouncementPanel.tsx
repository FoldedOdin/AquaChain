import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Megaphone, Send, Users, Clock, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';
import { notificationService, AnnouncementPayload, AnnouncementRecord } from '../../services/notificationService';
import { formatRelativeTime } from '../../utils/dateFormat';

type AudienceOption = 'all' | 'consumer' | 'technician';
type MessageType = 'info' | 'warning' | 'error' | 'success';

const AUDIENCE_OPTIONS: { value: AudienceOption; label: string }[] = [
  { value: 'all', label: 'All Users' },
  { value: 'consumer', label: 'Consumers Only' },
  { value: 'technician', label: 'Technicians Only' },
];

const TYPE_OPTIONS: { value: MessageType; label: string; icon: React.ReactNode; color: string }[] = [
  { value: 'info', label: 'Info', icon: <Info className="w-4 h-4" />, color: 'text-blue-600 bg-blue-50 border-blue-200' },
  { value: 'success', label: 'Success', icon: <CheckCircle className="w-4 h-4" />, color: 'text-green-600 bg-green-50 border-green-200' },
  { value: 'warning', label: 'Warning', icon: <AlertTriangle className="w-4 h-4" />, color: 'text-amber-600 bg-amber-50 border-amber-200' },
  { value: 'error', label: 'Critical', icon: <XCircle className="w-4 h-4" />, color: 'text-red-600 bg-red-50 border-red-200' },
];

const AnnouncementPanel: React.FC = () => {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [audience, setAudience] = useState<AudienceOption>('all');
  const [type, setType] = useState<MessageType>('info');
  const [isSending, setIsSending] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const [history, setHistory] = useState<AnnouncementRecord[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const loadHistory = useCallback(async () => {
    setIsLoadingHistory(true);
    try {
      const records = await notificationService.listAnnouncements();
      setHistory(records);
    } catch (e) {
      // non-fatal — history is supplementary
      console.warn('Could not load announcement history:', e);
    } finally {
      setIsLoadingHistory(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleSend = useCallback(async () => {
    if (!title.trim() || !message.trim()) {
      setErrorMsg('Title and message are required.');
      return;
    }
    setIsSending(true);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const payload: AnnouncementPayload = { title: title.trim(), message: message.trim(), type, audience };
      const result = await notificationService.broadcastAnnouncement(payload);
      setSuccessMsg(`Announcement sent to ${result.sent} user(s).`);
      setTitle('');
      setMessage('');
      setAudience('all');
      setType('info');
      loadHistory();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to send announcement.');
    } finally {
      setIsSending(false);
    }
  }, [title, message, type, audience, loadHistory]);

  const selectedType = TYPE_OPTIONS.find(t => t.value === type)!;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* Compose */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Megaphone className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Send Announcement</h2>
            <p className="text-sm text-gray-500">Broadcast a message to users in the system</p>
          </div>
        </div>

        <div className="space-y-4">
          {/* Audience + Type row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Users className="w-4 h-4 inline mr-1" />
                Audience
              </label>
              <select
                value={audience}
                onChange={e => setAudience(e.target.value as AudienceOption)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                {AUDIENCE_OPTIONS.map(o => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message Type</label>
              <div className="flex gap-2 flex-wrap">
                {TYPE_OPTIONS.map(o => (
                  <button
                    key={o.value}
                    onClick={() => setType(o.value)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
                      type === o.value ? o.color + ' ring-2 ring-offset-1 ring-current' : 'text-gray-600 bg-gray-50 border-gray-200 hover:bg-gray-100'
                    }`}
                  >
                    {o.icon}
                    {o.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Title */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Scheduled Maintenance on March 25"
              maxLength={120}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
            <textarea
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="Write your announcement here..."
              rows={4}
              maxLength={1000}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
            />
            <p className="text-xs text-gray-400 mt-1 text-right">{message.length}/1000</p>
          </div>

          {/* Preview */}
          {(title || message) && (
            <div className={`rounded-lg border p-4 ${selectedType.color}`}>
              <div className="flex items-center gap-2 mb-1">
                {selectedType.icon}
                <span className="text-sm font-semibold">{title || 'Preview title'}</span>
              </div>
              <p className="text-sm">{message || 'Preview message...'}</p>
              <p className="text-xs mt-2 opacity-70">
                To: {AUDIENCE_OPTIONS.find(a => a.value === audience)?.label}
              </p>
            </div>
          )}

          {/* Feedback */}
          {successMsg && (
            <div className="flex items-center gap-2 text-green-700 bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm">
              <CheckCircle className="w-4 h-4 shrink-0" />
              {successMsg}
            </div>
          )}
          {errorMsg && (
            <div className="flex items-center gap-2 text-red-700 bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm">
              <XCircle className="w-4 h-4 shrink-0" />
              {errorMsg}
            </div>
          )}

          <button
            onClick={handleSend}
            disabled={isSending || !title.trim() || !message.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-4 h-4" />
            {isSending ? 'Sending...' : 'Send Announcement'}
          </button>
        </div>
      </div>

      {/* History */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-semibold text-gray-900 flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            Past Announcements
          </h3>
          <button onClick={loadHistory} className="text-xs text-purple-600 hover:underline">Refresh</button>
        </div>

        {isLoadingHistory ? (
          <p className="text-sm text-gray-500">Loading...</p>
        ) : history.length === 0 ? (
          <p className="text-sm text-gray-500">No announcements sent yet.</p>
        ) : (
          <div className="space-y-3">
            {history.map(a => {
              const typeOpt = TYPE_OPTIONS.find(t => t.value === a.type) || TYPE_OPTIONS[0];
              const audienceLabel = AUDIENCE_OPTIONS.find(o => o.value === a.audience)?.label || a.audience;
              return (
                <div key={a.announcementId} className={`rounded-lg border p-4 ${typeOpt.color}`}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      {typeOpt.icon}
                      <span className="text-sm font-semibold">{a.title}</span>
                    </div>
                    <span className="text-xs opacity-60 shrink-0">{formatRelativeTime(new Date(a.createdAt))}</span>
                  </div>
                  <p className="text-sm mt-1">{a.message}</p>
                  <p className="text-xs mt-2 opacity-60">Sent to: {audienceLabel}</p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default AnnouncementPanel;
