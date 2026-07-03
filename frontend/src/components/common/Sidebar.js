import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Activity, LogOut, Menu, X, Bell } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';

export default function Sidebar({ navItems, role }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/');
  };

  const handleNotifications = () => {
    toast('You are all caught up — no new notifications.', { icon: '🔔' });
  };

  const Nav = () => (
    <>
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-4 py-5 border-b border-slate-100">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center flex-shrink-0">
          <Activity className="w-5 h-5 text-white" />
        </div>
        <span className="text-lg font-bold text-slate-900">Alpha<span className="text-primary-600">-Cure</span></span>
      </div>

      {/* User info */}
      <div className="px-4 py-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-400 to-teal-400 flex items-center justify-center flex-shrink-0">
            <span className="text-white font-bold text-sm">{user?.name?.[0]?.toUpperCase()}</span>
          </div>
          <div className="overflow-hidden">
            <p className="font-semibold text-slate-800 text-sm truncate">{user?.name}</p>
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${role === 'doctor' ? 'bg-violet-50 text-violet-700' : 'bg-primary-50 text-primary-700'}`}>
              {role === 'doctor' ? '🩺 Doctor' : '👤 Patient'}
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map(({ to, icon: Icon, label }) => (
          <Link key={to} to={to} onClick={() => setOpen(false)}
            className={`sidebar-link ${location.pathname === to ? 'active' : ''}`}>
            <Icon className="w-4 h-4 flex-shrink-0" />
            {label}
          </Link>
        ))}
      </nav>

      {/* Logout */}
      <div className="px-3 py-4 border-t border-slate-100">
        <button onClick={handleLogout} className="sidebar-link w-full text-red-500 hover:bg-red-50 hover:text-red-600">
          <LogOut className="w-4 h-4" /> Logout
        </button>
      </div>
    </>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-slate-100 min-h-screen fixed left-0 top-0 z-30">
        <Nav />
      </aside>

      {/* Mobile header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-40 bg-white border-b border-slate-100 h-14 flex items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center">
            <Activity className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-slate-900">Alpha<span className="text-primary-600">-Cure</span></span>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleNotifications}
            className="relative p-2 rounded-xl hover:bg-slate-100"
            aria-label="Show notifications"
          >
            <Bell className="w-5 h-5 text-slate-600" />
          </button>
          <button
            type="button"
            onClick={() => setOpen(p => !p)}
            className="p-2 rounded-xl hover:bg-slate-100"
            aria-label={open ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={open}
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/30" onClick={() => setOpen(false)} />
          <aside className="absolute left-0 top-0 bottom-0 w-72 bg-white flex flex-col shadow-2xl">
            <Nav />
          </aside>
        </div>
      )}
    </>
  );
}
