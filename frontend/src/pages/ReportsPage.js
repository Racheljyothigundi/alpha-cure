import React, { useState, useEffect } from 'react';
import {
  Brain, Activity, FileText, MessageCircle, MapPin,
  Download, Clock, AlertTriangle, CheckCircle, TrendingUp
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import api from '../services/api';
import toast from 'react-hot-toast';

const NAV = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/predict', icon: Brain, label: 'Cancer Detection' },
  { to: '/reports', icon: FileText, label: 'My Reports' },
  { to: '/chat', icon: MessageCircle, label: 'Chat & Consult' },
  { to: '/hospitals', icon: MapPin, label: 'Nearby Hospitals' },
  { to: '/profile', icon: Activity, label: 'My Profile' },
];

const RISK_CONFIG = {
  LOW: { badge: 'badge-low', icon: CheckCircle, color: 'text-green-600', bg: 'bg-green-50' },
  MODERATE: { badge: 'badge-moderate', icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50' },
  HIGH: { badge: 'badge-high', icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50' },
  CRITICAL: { badge: 'badge-critical', icon: AlertTriangle, color: 'text-purple-600', bg: 'bg-purple-50' },
};

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  useEffect(() => {
    api.get('/reports/')
      .then(r => setReports(r.data.reports || []))
      .catch(() => toast.error('Failed to load reports'))
      .finally(() => setLoading(false));
  }, []);

  const downloadReport = async (id, label) => {
    setDownloading(id);
    try {
      const res = await api.get(`/reports/download/${id}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `AlphaCure_Report_${id.slice(0, 8)}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Failed to download report');
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={NAV} role="patient" />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-5xl mx-auto p-6 space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Reports</h1>
            <p className="text-slate-500 text-sm mt-1">Download AI-generated PDF reports for your records</p>
          </div>

          {/* Summary stats */}
          {!loading && reports.length > 0 && (
            <div className="grid sm:grid-cols-3 gap-4">
              <div className="card flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-primary-50 flex items-center justify-center flex-shrink-0">
                  <TrendingUp className="w-5 h-5 text-primary-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-slate-900">{reports.length}</p>
                  <p className="text-xs text-slate-500">Total Assessments</p>
                </div>
              </div>
              <div className="card flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-slate-900">
                    {reports.filter(r => r.risk_level === 'LOW').length}
                  </p>
                  <p className="text-xs text-slate-500">Normal Results</p>
                </div>
              </div>
              <div className="card flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                </div>
                <div>
                  <p className="text-xl font-bold text-slate-900">
                    {reports.filter(r => ['HIGH', 'CRITICAL'].includes(r.risk_level)).length}
                  </p>
                  <p className="text-xs text-slate-500">High Risk Flags</p>
                </div>
              </div>
            </div>
          )}

          {/* Reports list */}
          {loading ? (
            <div className="card flex items-center justify-center py-16">
              <div className="w-8 h-8 border-4 border-primary-100 border-t-primary-500 rounded-full animate-spin" />
            </div>
          ) : reports.length === 0 ? (
            <div className="card text-center py-16">
              <FileText className="w-12 h-12 text-slate-200 mx-auto mb-3" />
              <p className="font-semibold text-slate-600">No reports yet</p>
              <p className="text-sm text-slate-400 mt-1">Complete a cancer assessment to generate your first report</p>
            </div>
          ) : (
            <div className="space-y-3">
              {reports.map(report => {
                const cfg = RISK_CONFIG[report.risk_level] || RISK_CONFIG.LOW;
                const Icon = cfg.icon;
                return (
                  <div key={report.id} className="card flex items-center gap-4 hover:shadow-card-hover transition-all duration-200">
                    <div className={`w-11 h-11 rounded-2xl ${cfg.bg} flex items-center justify-center flex-shrink-0`}>
                      <Icon className={`w-5 h-5 ${cfg.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-slate-900 truncate">{report.label}</p>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-xs text-slate-500">
                          Confidence: <strong className="text-slate-700">{report.confidence}%</strong>
                        </span>
                        <span className="text-slate-300">•</span>
                        <span className="flex items-center gap-1 text-xs text-slate-500">
                          <Clock className="w-3 h-3" />
                          {new Date(report.date).toLocaleDateString('en-IN', {
                            day: 'numeric', month: 'short', year: 'numeric',
                            hour: '2-digit', minute: '2-digit'
                          })}
                        </span>
                      </div>
                    </div>
                    <span className={cfg.badge}>{report.risk_level}</span>
                    <button
                      onClick={() => downloadReport(report.id, report.label)}
                      disabled={downloading === report.id}
                      className="btn-secondary text-sm px-4 py-2 ml-2">
                      {downloading === report.id ? (
                        <span className="w-4 h-4 border-2 border-primary-300 border-t-primary-600 rounded-full animate-spin" />
                      ) : <><Download className="w-4 h-4" /> PDF</>}
                    </button>
                  </div>
                );
              })}
            </div>
          )}

          {/* Info box */}
          <div className="rounded-2xl bg-primary-50 border border-primary-100 p-5">
            <h3 className="font-semibold text-primary-900 mb-1">📄 About Your Reports</h3>
            <p className="text-sm text-primary-700 leading-relaxed">
              Each PDF report includes your patient information, AI prediction results, confidence scores, 
              class probabilities, personalized AI recommendations, and a medical disclaimer. 
              Share these with your doctor for informed consultations.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
