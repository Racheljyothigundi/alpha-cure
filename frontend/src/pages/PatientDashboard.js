import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Brain, FileText, MessageCircle, MapPin, Activity,
  TrendingUp, AlertTriangle, CheckCircle, Clock, ArrowRight
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

const NAV = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/predict', icon: Brain, label: 'Cancer Detection' },
  { to: '/reports', icon: FileText, label: 'My Reports' },
  { to: '/chat', icon: MessageCircle, label: 'Chat & Consult' },
  { to: '/hospitals', icon: MapPin, label: 'Nearby Hospitals' },
  { to: '/profile', icon: Activity, label: 'My Profile' },
];

const RISK_CONFIG = {
  LOW: { color: 'text-green-600', bg: 'bg-green-50', border: 'border-green-100', badge: 'badge-low', icon: CheckCircle },
  MODERATE: { color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-100', badge: 'badge-moderate', icon: AlertTriangle },
  HIGH: { color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-100', badge: 'badge-high', icon: AlertTriangle },
  CRITICAL: { color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-100', badge: 'badge-critical', icon: AlertTriangle },
};

function StatCard({ icon: Icon, label, value, sub, color = 'text-primary-600', bg = 'bg-primary-50' }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center flex-shrink-0`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm font-medium text-slate-600">{label}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, title, desc, color, bg }) {
  return (
    <Link to={to} className="card hover:shadow-card-hover transition-all duration-300 hover:-translate-y-0.5 group flex items-start gap-4">
      <div className={`w-11 h-11 rounded-2xl ${bg} flex items-center justify-center flex-shrink-0`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-900 group-hover:text-primary-700 transition-colors">{title}</p>
        <p className="text-sm text-slate-500 mt-0.5 leading-relaxed">{desc}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-primary-500 transition-colors flex-shrink-0 mt-1" />
    </Link>
  );
}

export default function PatientDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ total_predictions: 0, high_risk_count: 0, recent_predictions: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/user/dashboard')
      .then(r => setStats(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={NAV} role="patient" />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-5xl mx-auto p-6 space-y-6">

          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">{greeting} 👋</p>
              <h1 className="text-2xl font-bold text-slate-900 mt-0.5">{user?.name}</h1>
              <p className="text-slate-500 text-sm mt-1">Here's your health overview</p>
            </div>
            <Link to="/predict" className="btn-primary">
              <Brain className="w-4 h-4" /> New Scan
            </Link>
          </div>

          {/* Stats */}
          <div className="grid sm:grid-cols-3 gap-4">
            <StatCard icon={Activity} label="Total Assessments" value={stats.total_predictions}
              sub="AI cancer screenings" color="text-primary-600" bg="bg-primary-50" />
            <StatCard icon={AlertTriangle} label="High Risk Flags" value={stats.high_risk_count}
              sub="Requires attention" color="text-red-600" bg="bg-red-50" />
            <StatCard icon={CheckCircle} label="Normal Results" value={Math.max(0, stats.total_predictions - stats.high_risk_count)}
              sub="No immediate concern" color="text-green-600" bg="bg-green-50" />
          </div>

          {/* Quick Actions */}
          <div>
            <h2 className="text-lg font-bold text-slate-900 mb-4">Quick Actions</h2>
            <div className="grid sm:grid-cols-2 gap-4">
              <QuickAction to="/predict" icon={Brain} title="Start Cancer Detection"
                desc="Enter clinical parameters for instant AI risk assessment"
                color="text-primary-600" bg="bg-primary-50" />
              <QuickAction to="/chat" icon={MessageCircle} title="Ask the AI Chatbot"
                desc="Get answers about symptoms, prevention & treatment"
                color="text-teal-600" bg="bg-teal-50" />
              <QuickAction to="/hospitals" icon={MapPin} title="Find Nearby Hospitals"
                desc="Locate cancer centers and vaccination clinics near you"
                color="text-rose-600" bg="bg-rose-50" />
              <QuickAction to="/reports" icon={FileText} title="Download Reports"
                desc="View and download your AI-generated PDF health reports"
                color="text-amber-600" bg="bg-amber-50" />
            </div>
          </div>

          {/* Recent Predictions */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900">Recent Assessments</h2>
              <Link to="/reports" className="text-sm text-primary-600 font-semibold hover:text-primary-700">View all →</Link>
            </div>

            {loading ? (
              <div className="card flex items-center justify-center py-12">
                <div className="w-8 h-8 border-4 border-primary-100 border-t-primary-500 rounded-full animate-spin" />
              </div>
            ) : stats.recent_predictions.length === 0 ? (
              <div className="card text-center py-12">
                <Brain className="w-12 h-12 text-slate-200 mx-auto mb-3" />
                <p className="font-semibold text-slate-600">No assessments yet</p>
                <p className="text-sm text-slate-400 mt-1 mb-5">Run your first cancer risk assessment to get started</p>
                <Link to="/predict" className="btn-primary inline-flex">
                  <Brain className="w-4 h-4" /> Start Assessment
                </Link>
              </div>
            ) : (
              <div className="space-y-3">
                {stats.recent_predictions.map(pred => {
                  const cfg = RISK_CONFIG[pred.risk_level] || RISK_CONFIG.LOW;
                  const Icon = cfg.icon;
                  return (
                    <div key={pred._id} className={`card border ${cfg.border} flex items-center gap-4`}>
                      <div className={`w-10 h-10 rounded-xl ${cfg.bg} flex items-center justify-center flex-shrink-0`}>
                        <Icon className={`w-5 h-5 ${cfg.color}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-slate-900 truncate">{pred.label}</p>
                        <div className="flex items-center gap-3 mt-0.5">
                          <span className="text-xs text-slate-500">Confidence: <strong>{pred.confidence}%</strong></span>
                          <span className="text-slate-300">•</span>
                          <span className="flex items-center gap-1 text-xs text-slate-500">
                            <Clock className="w-3 h-3" />
                            {new Date(pred.timestamp).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                          </span>
                        </div>
                      </div>
                      <span className={cfg.badge}>{pred.risk_level}</span>
                      <Link to="/reports" className="btn-secondary text-xs px-3 py-1.5 ml-2 hidden sm:flex">
                        <FileText className="w-3.5 h-3.5" /> Report
                      </Link>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Health Tips Banner */}
          <div className="rounded-2xl bg-gradient-to-r from-primary-600 to-teal-500 p-6 text-white">
            <div className="flex items-start gap-4">
              <TrendingUp className="w-8 h-8 text-white/70 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-bold text-lg mb-1">💡 Health Tip of the Day</h3>
                <p className="text-primary-100 text-sm leading-relaxed">
                  Regular cancer screening can increase survival rates by up to 90% for many cancer types.
                  Early detection is your strongest defense — schedule a comprehensive screening today.
                </p>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}
