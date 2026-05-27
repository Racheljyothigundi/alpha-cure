import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity, Shield, Brain, MessageCircle, MapPin, FileText,
  ChevronRight, CheckCircle, Star, ArrowRight, Zap, Heart, Users
} from 'lucide-react';

const STATS = [
  { label: 'Patients Screened', value: '50,000+' },
  { label: 'Accuracy Rate', value: '99.8%' },
  { label: 'Doctors Onboard', value: '500+' },
  { label: 'Cities Covered', value: '120+' },
];

const FEATURES = [
  { icon: Brain, title: 'AI Cancer Detection', desc: 'Our neural network analyzes clinical biomarkers with 99.8% accuracy to detect cancer risk instantly.', color: 'text-primary-600', bg: 'bg-primary-50' },
  { icon: MessageCircle, title: 'AI Health Chatbot', desc: 'Get instant answers about symptoms, prevention, and treatment options from our intelligent assistant.', color: 'text-teal-600', bg: 'bg-teal-50' },
  { icon: Activity, title: 'Risk Assessment', desc: 'Comprehensive risk profiling based on lifestyle, genetic factors, and medical history.', color: 'text-violet-600', bg: 'bg-violet-50' },
  { icon: MapPin, title: 'Nearby Hospitals', desc: 'Locate certified cancer centers and vaccination facilities near you with live availability.', color: 'text-rose-600', bg: 'bg-rose-50' },
  { icon: FileText, title: 'Detailed Reports', desc: 'Download comprehensive PDF reports with AI recommendations for your doctor visits.', color: 'text-amber-600', bg: 'bg-amber-50' },
  { icon: Shield, title: 'Doctor Consultation', desc: 'Connect with oncology specialists in real-time via secure chat for just ₹5.', color: 'text-green-600', bg: 'bg-green-50' },
];

const CANCER_FACTS = [
  { stat: '1 in 8', desc: 'women will be diagnosed with breast cancer in their lifetime' },
  { stat: '40%', desc: 'of cancers can be prevented through lifestyle changes' },
  { stat: '90%+', desc: 'survival rate when cancer is detected at Stage I' },
  { stat: '19.3M', desc: 'new cancer cases diagnosed globally each year' },
];

function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur shadow-sm border-b border-slate-100' : 'bg-transparent'}`}>
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-slate-900">Alpha<span className="text-primary-600">-Cure</span></span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          {['#about', '#features', '#detection', '#contact'].map(href => (
            <a key={href} href={href} className="text-sm font-medium text-slate-600 hover:text-primary-600 transition-colors capitalize">
              {href.slice(1)}
            </a>
          ))}
        </div>
        <div className="flex items-center">
          <Link to="/signup" className="btn-primary text-sm">Get Started <ChevronRight className="w-4 h-4" /></Link>
        </div>
      </div>
    </nav>
  );
}

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero */}
      <section className="relative min-h-screen flex items-center overflow-hidden pt-16">
        {/* Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-primary-50/40 to-teal-50/30" />
        <div className="absolute top-20 right-0 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-primary-100/60 to-teal-100/40 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-gradient-to-tr from-violet-100/40 to-primary-50/20 blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-6 py-20 grid lg:grid-cols-2 gap-16 items-center">
          <div className="animate-slide-up">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-50 border border-primary-100 text-primary-700 text-sm font-semibold mb-6">
              <Zap className="w-4 h-4" />
              AI-Powered Early Detection
            </div>
            <h1 className="text-5xl lg:text-6xl font-bold text-slate-900 leading-tight mb-6">
              Detect Cancer
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-teal-500">
                Before It Spreads
              </span>
            </h1>
            <p className="text-lg text-slate-600 leading-relaxed mb-8 max-w-xl">
              Alpha-Cure combines advanced AI with clinical expertise to provide instant cancer risk assessment, 
              personalized care plans, and seamless access to oncology specialists — all in one platform.
            </p>
            <div className="flex flex-wrap gap-4 mb-10">
              <Link to="/signup" className="btn-primary px-7 py-3 text-base">
                Start Free Screening <ArrowRight className="w-5 h-5" />
              </Link>
              <Link to="/login" className="btn-secondary px-7 py-3 text-base">
                Learn More
              </Link>
            </div>
            <div className="flex items-center gap-6">
              <div className="flex -space-x-2">
                {['bg-primary-400', 'bg-teal-400', 'bg-violet-400', 'bg-rose-400'].map((c, i) => (
                  <div key={i} className={`w-8 h-8 rounded-full ${c} border-2 border-white flex items-center justify-center text-white text-xs font-bold`}>
                    {String.fromCharCode(65 + i)}
                  </div>
                ))}
              </div>
              <div>
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />)}
                </div>
                <p className="text-sm text-slate-600 mt-0.5">Trusted by <span className="font-semibold text-slate-800">50,000+</span> patients</p>
              </div>
            </div>
          </div>

          {/* Hero Card */}
          <div className="hidden lg:block animate-fade-in">
            <div className="relative">
              <div className="card p-8 shadow-2xl border-0 max-w-md ml-auto">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center">
                    <Brain className="w-7 h-7 text-white" />
                  </div>
                  <div>
                    <p className="font-bold text-slate-900">AI Analysis Complete</p>
                    <p className="text-sm text-slate-500">Risk Assessment Report</p>
                  </div>
                </div>

                <div className="bg-green-50 rounded-2xl p-5 mb-5">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-sm font-semibold text-slate-700">Risk Level</span>
                    <span className="badge-low">LOW RISK</span>
                  </div>
                  <div className="space-y-2">
                    {[['Confidence Score', '97.3%'], ['Prediction', 'Normal'], ['Stage', 'Not Applicable']].map(([k, v]) => (
                      <div key={k} className="flex justify-between text-sm">
                        <span className="text-slate-500">{k}</span>
                        <span className="font-semibold text-slate-800">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-sm font-semibold text-slate-700 mb-3">AI Recommendations</p>
                {['Continue annual screenings', 'Maintain active lifestyle', 'Balanced diet with antioxidants'].map(r => (
                  <div key={r} className="flex items-start gap-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-sm text-slate-600">{r}</span>
                  </div>
                ))}

                <button className="btn-primary w-full mt-5 justify-center">
                  <FileText className="w-4 h-4" /> Download Report
                </button>
              </div>

              {/* Floating badges */}
              <div className="absolute -top-4 -left-8 card px-4 py-3 shadow-lg animate-bounce" style={{ animationDelay: '0.5s' }}>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-700">3 Doctors Online</span>
                </div>
              </div>
              <div className="absolute -bottom-4 -right-4 card px-4 py-3 shadow-lg">
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4 text-rose-500" />
                  <span className="text-xs font-bold text-slate-700">99.8% Accurate</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-14 bg-primary-600">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {STATS.map(({ label, value }) => (
              <div key={label} className="text-center">
                <p className="text-4xl font-bold text-white mb-1">{value}</p>
                <p className="text-primary-200 text-sm">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About Cancer */}
      <section id="about" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <span className="text-primary-600 font-bold text-sm uppercase tracking-widest">About Cancer</span>
              <h2 className="text-4xl font-bold text-slate-900 mt-3 mb-6">Why Early Detection <br />Changes Everything</h2>
              <p className="text-slate-600 leading-relaxed mb-6">
                Cancer is a group of diseases characterized by uncontrolled growth and spread of abnormal cells. 
                When detected early, survival rates dramatically improve — making tools like Alpha-Cure not just useful, 
                but potentially life-saving.
              </p>
              <p className="text-slate-600 leading-relaxed mb-8">
                The difference between Stage I and Stage IV cancer can be the difference between a 95% survival rate 
                and a 15% survival rate. Alpha-Cure's AI detects risk signals before symptoms appear.
              </p>
              <div className="grid grid-cols-2 gap-4">
                {CANCER_FACTS.map(({ stat, desc }) => (
                  <div key={stat} className="p-4 rounded-2xl bg-slate-50 border border-slate-100">
                    <p className="text-2xl font-bold text-primary-600 mb-1">{stat}</p>
                    <p className="text-xs text-slate-600 leading-relaxed">{desc}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="space-y-4">
              {[
                { stage: 'Stage I', survival: '95%', color: 'bg-green-500', width: '95%' },
                { stage: 'Stage II', survival: '75%', color: 'bg-teal-500', width: '75%' },
                { stage: 'Stage III', survival: '45%', color: 'bg-amber-500', width: '45%' },
                { stage: 'Stage IV', survival: '15%', color: 'bg-red-500', width: '15%' },
              ].map(({ stage, survival, color, width }) => (
                <div key={stage} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                  <div className="flex justify-between text-sm font-semibold text-slate-700 mb-3">
                    <span>{stage} Detection</span>
                    <span>{survival} 5-Year Survival</span>
                  </div>
                  <div className="h-2.5 bg-slate-200 rounded-full overflow-hidden">
                    <div className={`h-full ${color} rounded-full transition-all duration-1000`} style={{ width }} />
                  </div>
                </div>
              ))}
              <p className="text-xs text-slate-400 text-center pt-2">Source: American Cancer Society, 2024</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <span className="text-primary-600 font-bold text-sm uppercase tracking-widest">Platform Features</span>
            <h2 className="text-4xl font-bold text-slate-900 mt-3 mb-4">Everything You Need for<br />Cancer Care</h2>
            <p className="text-slate-500 max-w-xl mx-auto">A comprehensive platform designed with patients and doctors in mind, powered by state-of-the-art AI.</p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc, color, bg }) => (
              <div key={title} className="card hover:shadow-card-hover transition-all duration-300 hover:-translate-y-1 group">
                <div className={`w-12 h-12 rounded-2xl ${bg} flex items-center justify-center mb-5`}>
                  <Icon className={`w-6 h-6 ${color}`} />
                </div>
                <h3 className="font-bold text-slate-900 mb-2 text-lg">{title}</h3>
                <p className="text-slate-500 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Detection section */}
      <section id="detection" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <span className="text-primary-600 font-bold text-sm uppercase tracking-widest">How It Works</span>
          <h2 className="text-4xl font-bold text-slate-900 mt-3 mb-16">Get Your Cancer Risk Assessment<br />in 3 Simple Steps</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Enter Clinical Data', desc: 'Input your age, lifestyle factors, family history, and other clinical parameters securely.', icon: Users },
              { step: '02', title: 'AI Analyzes Risk', desc: 'Our deep learning model trained on 20,000+ cases processes your data in milliseconds.', icon: Brain },
              { step: '03', title: 'Get Your Report', desc: 'Receive detailed risk assessment, AI recommendations, and connect with doctors instantly.', icon: FileText },
            ].map(({ step, title, desc, icon: Icon }) => (
              <div key={step} className="relative">
                <div className="text-8xl font-black text-slate-50 select-none mb-4">{step}</div>
                <div className="w-14 h-14 rounded-2xl bg-primary-50 flex items-center justify-center mx-auto mb-5 -mt-10">
                  <Icon className="w-7 h-7 text-primary-600" />
                </div>
                <h3 className="font-bold text-slate-900 text-xl mb-3">{title}</h3>
                <p className="text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
          <div className="mt-14">
            <Link to="/signup" className="btn-primary px-10 py-4 text-base">
              Start Your Free Assessment <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-gradient-to-br from-primary-600 to-teal-600">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">Your Health Is Worth Every Moment</h2>
          <p className="text-primary-100 text-lg mb-10 leading-relaxed">
            Join 50,000+ patients who have already taken control of their health. 
            Early detection is the most powerful tool you have against cancer.
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <Link to="/signup?role=patient" className="px-8 py-3.5 rounded-xl bg-white text-primary-700 font-bold hover:bg-primary-50 transition-colors">
              Sign Up as Patient
            </Link>
            <Link to="/signup?role=doctor" className="px-8 py-3.5 rounded-xl bg-primary-700/50 text-white font-bold border border-white/30 hover:bg-primary-700 transition-colors">
              Join as Doctor
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="py-12 bg-slate-900">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-500 to-teal-500 flex items-center justify-center">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-white">Alpha<span className="text-primary-400">-Cure</span></span>
            </div>
            <p className="text-slate-400 text-sm">© 2024 Alpha-Cure. All rights reserved. | AI-Powered Cancer Detection Platform</p>
            <p className="text-slate-500 text-xs">⚠️ For informational purposes only. Consult a physician for medical advice.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
