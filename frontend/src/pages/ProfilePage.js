import React, { useState } from 'react';
import {
  Brain, Activity, FileText, MessageCircle, MapPin,
  User, Save, Stethoscope, Phone, Calendar, Droplets
} from 'lucide-react';
import Sidebar from '../components/common/Sidebar';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import toast from 'react-hot-toast';

const PATIENT_NAV = [
  { to: '/dashboard', icon: Activity, label: 'Dashboard' },
  { to: '/predict', icon: Brain, label: 'Cancer Detection' },
  { to: '/reports', icon: FileText, label: 'My Reports' },
  { to: '/chat', icon: MessageCircle, label: 'Chat & Consult' },
  { to: '/hospitals', icon: MapPin, label: 'Nearby Hospitals' },
  { to: '/profile', icon: User, label: 'My Profile' },
];

const DOCTOR_NAV = [
  { to: '/doctor', icon: Activity, label: 'Dashboard' },
  { to: '/chat', icon: MessageCircle, label: 'Patient Chat' },
  { to: '/profile', icon: User, label: 'My Profile' },
];

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || '',
    phone: user?.phone || '',
    specialization: user?.specialization || '',
    profile: {
      age: user?.profile?.age || '',
      gender: user?.profile?.gender || '',
      blood_group: user?.profile?.blood_group || '',
      address: user?.profile?.address || '',
      emergency_contact: user?.profile?.emergency_contact || '',
    }
  });

  const set = (k) => (e) => setForm(p => ({ ...p, [k]: e.target.value }));
  const setProfile = (k) => (e) => setForm(p => ({ ...p, profile: { ...p.profile, [k]: e.target.value } }));

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put('/user/profile', form);
      updateUser({ name: form.name, phone: form.phone });
      toast.success('Profile updated successfully!');
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const isDoctor = user?.role === 'doctor';
  const navItems = isDoctor ? DOCTOR_NAV : PATIENT_NAV;

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={navItems} role={user?.role} />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-3xl mx-auto p-6 space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Profile</h1>
            <p className="text-slate-500 text-sm mt-1">Manage your personal and medical information</p>
          </div>

          {/* Avatar card */}
          <div className="card flex items-center gap-5">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center text-white text-2xl font-bold flex-shrink-0">
              {user?.name?.[0]?.toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900">{user?.name}</h2>
              <p className="text-slate-500 text-sm">{user?.email}</p>
              <span className={`inline-block mt-1 text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                isDoctor ? 'bg-violet-50 text-violet-700' : 'bg-primary-50 text-primary-700'
              }`}>
                {isDoctor ? '🩺 Doctor' : '👤 Patient'}
              </span>
            </div>
          </div>

          {/* Basic Info */}
          <div className="card">
            <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
              <User className="w-4 h-4 text-primary-500" /> Basic Information
            </h3>
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <label className="label">Full Name</label>
                <input className="input-field" value={form.name} onChange={set('name')} placeholder="Your full name" />
              </div>
              <div>
                <label className="label">Phone Number</label>
                <div className="relative">
                  <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input className="input-field pl-10" value={form.phone} onChange={set('phone')} placeholder="+91 98765 43210" />
                </div>
              </div>
              {isDoctor && (
                <div className="sm:col-span-2">
                  <label className="label">Specialization</label>
                  <div className="relative">
                    <Stethoscope className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <select className="input-field pl-10" value={form.specialization} onChange={set('specialization')}>
                      <option value="">Select specialization</option>
                      {['Oncology', 'Surgical Oncology', 'Medical Oncology', 'Radiation Oncology',
                        'Hematology', 'Gynecologic Oncology', 'Pediatric Oncology', 'General Medicine'].map(s => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Medical Info (patients only) */}
          {!isDoctor && (
            <div className="card">
              <h3 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-primary-500" /> Medical Information
              </h3>
              <div className="grid sm:grid-cols-2 gap-4">
                <div>
                  <label className="label">Age</label>
                  <div className="relative">
                    <Calendar className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input type="number" className="input-field pl-10" value={form.profile.age}
                      onChange={setProfile('age')} placeholder="35" min="1" max="120" />
                  </div>
                </div>
                <div>
                  <label className="label">Gender</label>
                  <select className="input-field" value={form.profile.gender} onChange={setProfile('gender')}>
                    <option value="">Select gender</option>
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="label">Blood Group</label>
                  <div className="relative">
                    <Droplets className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <select className="input-field pl-10" value={form.profile.blood_group} onChange={setProfile('blood_group')}>
                      <option value="">Select blood group</option>
                      {['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'].map(bg => (
                        <option key={bg} value={bg}>{bg}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="label">Emergency Contact</label>
                  <div className="relative">
                    <Phone className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input className="input-field pl-10" value={form.profile.emergency_contact}
                      onChange={setProfile('emergency_contact')} placeholder="+91 98765 43210" />
                  </div>
                </div>
                <div className="sm:col-span-2">
                  <label className="label">Address</label>
                  <textarea className="input-field resize-none" rows={2}
                    value={form.profile.address} onChange={setProfile('address')}
                    placeholder="Your home address" />
                </div>
              </div>
            </div>
          )}

          {/* Account Info (read-only) */}
          <div className="card bg-slate-50">
            <h3 className="font-bold text-slate-700 mb-3 text-sm">Account Details</h3>
            <div className="space-y-2">
              {[['Email', user?.email], ['Role', user?.role?.charAt(0).toUpperCase() + user?.role?.slice(1)],
                ['Account Status', 'Verified ✓']].map(([label, value]) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-slate-500">{label}</span>
                  <span className="font-medium text-slate-700">{value}</span>
                </div>
              ))}
            </div>
          </div>

          <button onClick={handleSave} disabled={saving} className="btn-primary py-3 px-8">
            {saving ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Saving...
              </span>
            ) : <><Save className="w-4 h-4" /> Save Changes</>}
          </button>
        </div>
      </main>
    </div>
  );
}
