import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, MessageCircle, User, Users,
  AlertTriangle, BarChart3, TrendingUp, FileText, Clock
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const NAV = [
  { to: '/doctor', icon: Activity, label: 'Dashboard' },
  { to: '/chat', icon: MessageCircle, label: 'Patient Chat' },
  { to: '/profile', icon: User, label: 'My Profile' },
];

const RISK_COLORS_MAP = { LOW: '#16a34a', MODERATE: '#d97706', HIGH: '#dc2626', CRITICAL: '#7c3aed' };
const RISK_CONFIG = {
  LOW: 'badge-low', MODERATE: 'badge-moderate', HIGH: 'badge-high', CRITICAL: 'badge-critical'
};

function StatCard({ icon: Icon, label, value, color = 'text-primary-600', bg = 'bg-primary-50' }) {
  return (
    <div className="card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center flex-shrink-0`}>
        <Icon className={`w-6 h-6 ${color}`} />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        <p className="text-sm text-slate-500 font-medium">{label}</p>
      </div>
    </div>
  );
}

export default function DoctorDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get('/doctor/stats').then(r => setStats(r.data)),
      api.get('/doctor/patients').then(r => setPatients(r.data.patients || []))
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  // Chart data from patients
  const riskDistribution = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'].map(level => {
    const count = patients.reduce((acc, p) =>
      acc + p.predictions.filter(pr => pr.risk_level === level).length, 0);
    return { name: level, count, fill: RISK_COLORS_MAP[level] };
  });

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good Morning' : hour < 17 ? 'Good Afternoon' : 'Good Evening';

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={NAV} role="doctor" />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-6xl mx-auto p-6 space-y-6">

          {/* Header */}
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500 font-medium">{greeting}, Doctor 👋</p>
              <h1 className="text-2xl font-bold text-slate-900 mt-0.5">Dr. {user?.name}</h1>
              <p className="text-slate-500 text-sm mt-1">{user?.specialization || 'Oncology'} • Alpha-Cure Platform</p>
            </div>
            <Link to="/chat" className="btn-primary">
              <MessageCircle className="w-4 h-4" /> Patient Chats
            </Link>
          </div>

          {/* Stats */}
          {loading ? (
            <div className="grid sm:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="card h-20 animate-pulse bg-slate-100" />
              ))}
            </div>
          ) : (
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard icon={Users} label="Total Patients" value={stats?.total_patients ?? 0}
                color="text-primary-600" bg="bg-primary-50" />
              <StatCard icon={BarChart3} label="Total Assessments" value={stats?.total_predictions ?? 0}
                color="text-teal-600" bg="bg-teal-50" />
              <StatCard icon={AlertTriangle} label="High Risk Patients" value={stats?.high_risk_patients ?? 0}
                color="text-red-600" bg="bg-red-50" />
              <StatCard icon={TrendingUp} label="Consultations" value={stats?.consultations_accepted ?? 0}
                color="text-violet-600" bg="bg-violet-50" />
            </div>
          )}

          {/* Charts */}
          {!loading && (
            <div className="grid lg:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="font-bold text-slate-900 mb-4">Risk Distribution</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={riskDistribution} barSize={40}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
                    <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                      {riskDistribution.map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="card">
                <h3 className="font-bold text-slate-900 mb-4">Risk Overview</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={riskDistribution.filter(d => d.count > 0)} dataKey="count" nameKey="name"
                      cx="50%" cy="50%" innerRadius={55} outerRadius={85} paddingAngle={4}>
                      {riskDistribution.filter(d => d.count > 0).map((entry, i) => (
                        <Cell key={i} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 16px rgba(0,0,0,0.1)' }} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-wrap gap-3 mt-2 justify-center">
                  {riskDistribution.map(({ name, fill, count }) => (
                    <div key={name} className="flex items-center gap-1.5 text-xs text-slate-600">
                      <div className="w-2.5 h-2.5 rounded-full" style={{ background: fill }} />
                      {name} ({count})
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* High Risk Patients Table */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900">High Risk Patients</h2>
              <span className="text-xs text-slate-400 bg-slate-100 px-3 py-1 rounded-full">Requires attention</span>
            </div>

            {loading ? (
              <div className="card flex items-center justify-center py-12">
                <div className="w-8 h-8 border-4 border-primary-100 border-t-primary-500 rounded-full animate-spin" />
              </div>
            ) : patients.length === 0 ? (
              <div className="card text-center py-12">
                <Users className="w-12 h-12 text-slate-200 mx-auto mb-3" />
                <p className="font-semibold text-slate-600">No high-risk patients</p>
                <p className="text-sm text-slate-400 mt-1">Patients with high/critical risk assessments will appear here</p>
              </div>
            ) : (
              <div className="card p-0 overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-50 border-b border-slate-100">
                      <tr>
                        {['Patient', 'Contact', 'Latest Diagnosis', 'Risk', 'Date', 'Action'].map(h => (
                          <th key={h} className="px-5 py-3.5 text-left text-xs font-bold text-slate-500 uppercase tracking-wider">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50">
                      {patients.map(patient => {
                        const latest = patient.predictions[0];
                        return (
                          <tr key={patient.id} className="hover:bg-slate-50/50 transition-colors">
                            <td className="px-5 py-4">
                              <div className="flex items-center gap-3">
                                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                                  {patient.name[0]}
                                </div>
                                <div>
                                  <p className="font-semibold text-slate-900 text-sm">{patient.name}</p>
                                  <p className="text-xs text-slate-500">{patient.email}</p>
                                </div>
                              </div>
                            </td>
                            <td className="px-5 py-4 text-sm text-slate-600">{patient.phone || '—'}</td>
                            <td className="px-5 py-4">
                              <p className="text-sm font-medium text-slate-800">{latest?.label || '—'}</p>
                              <p className="text-xs text-slate-500">Conf: {latest?.confidence}%</p>
                            </td>
                            <td className="px-5 py-4">
                              {latest && <span className={RISK_CONFIG[latest.risk_level]}>{latest.risk_level}</span>}
                            </td>
                            <td className="px-5 py-4 text-xs text-slate-500">
                              {latest && (
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3" />
                                  {new Date(latest.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                                </span>
                              )}
                            </td>
                            <td className="px-5 py-4">
                              <Link to={`/chat?patient=${patient.id}`} className="btn-secondary text-xs px-3 py-1.5">
                                <MessageCircle className="w-3.5 h-3.5" /> Chat
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="rounded-2xl bg-violet-50 border border-violet-100 p-4">
            <p className="text-sm text-violet-700 leading-relaxed">
              <strong>Clinical Note:</strong> Patient risk assessments are generated by Alpha-Cure's AI model trained on clinical data. 
              All results require professional medical evaluation before any treatment decisions.
            </p>
          </div>

        </div>
      </main>
    </div>
  );
}
