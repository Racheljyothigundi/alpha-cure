import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Brain, Activity, FileText, MessageCircle, MapPin,
  CheckCircle, AlertTriangle, ChevronRight, Info, Loader,
  Upload, X, Image as ImageIcon
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

const RISK_STYLES = {
  LOW: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    title: 'text-green-700',
    badge: 'bg-green-100 text-green-800',
    icon: CheckCircle,
    iconColor: 'text-green-600',
    barColor: 'bg-green-500',
  },
  MODERATE: {
    bg: 'bg-amber-50',
    border: 'border-amber-200',
    title: 'text-amber-700',
    badge: 'bg-amber-100 text-amber-800',
    icon: AlertTriangle,
    iconColor: 'text-amber-600',
    barColor: 'bg-amber-500',
  },
  HIGH: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    title: 'text-red-700',
    badge: 'bg-red-100 text-red-800',
    icon: AlertTriangle,
    iconColor: 'text-red-600',
    barColor: 'bg-red-500',
  },
  CRITICAL: {
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    title: 'text-purple-700',
    badge: 'bg-purple-100 text-purple-800',
    icon: AlertTriangle,
    iconColor: 'text-purple-600',
    barColor: 'bg-purple-500',
  },
};

const FIELDS = [
  { key: 'age', label: 'Age (years)', type: 'number', placeholder: '45', min: 1, max: 120, info: 'Patient age in years' },
  { key: 'gender', label: 'Gender', type: 'select', options: [['0', 'Female'], ['1', 'Male']], info: '0 = Female, 1 = Male' },
  { key: 'bmi', label: 'BMI', type: 'number', placeholder: '24.5', min: 10, max: 60, step: '0.1', info: 'Body Mass Index (weight in kg / height in m^2)' },
  { key: 'smoking', label: 'Smoking Status', type: 'select', options: [['0', 'Non-smoker'], ['1', 'Smoker']], info: 'Current or former smoking habit' },
  { key: 'genetic_risk', label: 'Genetic Risk', type: 'select', options: [['0', 'Low'], ['1', 'Medium'], ['2', 'High']], info: 'Family history of cancer (0=Low, 1=Med, 2=High)' },
  { key: 'physical_activity', label: 'Physical Activity (hrs/week)', type: 'number', placeholder: '3', min: 0, max: 20, step: '0.5', info: 'Average hours of exercise per week' },
  { key: 'alcohol_intake', label: 'Alcohol Intake (units/week)', type: 'number', placeholder: '2', min: 0, max: 30, step: '0.5', info: 'Weekly alcohol consumption in units' },
  { key: 'cancer_history', label: 'Personal Cancer History', type: 'select', options: [['0', 'No Prior Cancer'], ['1', 'Prior Cancer Diagnosed']], info: 'Any previous cancer diagnosis' },
  { key: 'diagnosis', label: 'Prior Diagnosis Status', type: 'select', options: [['0', 'None'], ['1', 'Diagnosed Previously']], info: 'Any prior formal diagnosis' },
];

const DEFAULT_FORM = {
  age: '',
  gender: '0',
  bmi: '',
  smoking: '0',
  genetic_risk: '0',
  physical_activity: '',
  alcohol_intake: '',
  cancer_history: '0',
  diagnosis: '0',
};

const IMAGE_MODEL_FALLBACK = [
  {
    key: 'skin_lesion',
    title: 'Skin Lesion Screening',
    dataset: 'DermaMNIST',
    model_name: 'MobileNetV2 (DermaMNIST)',
    input_hint: 'Upload a close-up skin lesion photo in bright, even lighting.',
    note: 'Visible skin-lesion images only.',
    short_note: 'Visible skin-lesion images only.',
    available: false,
  },
  {
    key: 'breast_ultrasound',
    title: 'Breast Ultrasound Screening',
    dataset: 'BreastMNIST',
    model_name: 'MobileNetV2 (BreastMNIST)',
    input_hint: 'Upload a breast ultrasound image or ultrasound crop.',
    note: 'Breast ultrasound images only.',
    short_note: 'Breast ultrasound images only.',
    available: false,
  },
  {
    key: 'colorectal_histology',
    title: 'Colorectal Pathology Tile Screening',
    dataset: 'PathMNIST',
    model_name: 'MobileNetV2 (PathMNIST)',
    input_hint: 'Upload a colorectal pathology tile or microscope crop.',
    note: 'Pathology tile images only.',
    short_note: 'Pathology tile images only.',
    available: false,
  },
];

function ResultCard({ result, title, details = [], footnote }) {
  const style = RISK_STYLES[result.risk_level] || RISK_STYLES.LOW;
  const Icon = style.icon;

  return (
    <div className={`rounded-2xl border-2 ${style.border} ${style.bg} p-6 animate-slide-up`}>
      <div className="flex items-start justify-between mb-5 gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-12 h-12 rounded-2xl bg-white flex items-center justify-center shadow-sm flex-shrink-0">
            <Icon className={`w-7 h-7 ${style.iconColor}`} />
          </div>
          <div className="min-w-0">
            <p className="text-xs font-bold uppercase tracking-widest text-slate-500">{title}</p>
            <h3 className={`text-lg font-bold ${style.title} mt-0.5 break-words`}>{result.label}</h3>
          </div>
        </div>
        <span className={`px-3 py-1.5 rounded-full text-xs font-bold whitespace-nowrap ${style.badge}`}>
          {result.risk_level} RISK
        </span>
      </div>

      {details.length > 0 && (
        <div className="bg-white rounded-xl p-4 mb-4 shadow-sm space-y-1">
          {details.map((detail) => (
            <p key={detail} className="text-sm text-slate-600">{detail}</p>
          ))}
        </div>
      )}

      <div className="bg-white rounded-xl p-4 mb-4 shadow-sm">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-semibold text-slate-700">Confidence Score</span>
          <span className="text-xl font-black text-slate-900">{result.confidence}%</span>
        </div>
        <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${style.barColor} rounded-full transition-all duration-1000`}
            style={{ width: `${result.confidence}%` }}
          />
        </div>
      </div>

      {result.probabilities && Object.keys(result.probabilities).length > 0 && (
        <div className="bg-white rounded-xl p-4 mb-4 shadow-sm">
          <p className="text-sm font-semibold text-slate-700 mb-3">Class Probabilities</p>
          {Object.entries(result.probabilities).map(([label, prob]) => (
            <div key={label} className="mb-2 last:mb-0">
              <div className="flex justify-between text-xs text-slate-600 mb-1 gap-2">
                <span className="truncate">{label}</span>
                <span className="font-bold flex-shrink-0">{(prob * 100).toFixed(1)}%</span>
              </div>
              <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary-400 rounded-full" style={{ width: `${prob * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="bg-white rounded-xl p-4 shadow-sm">
        <p className="text-sm font-bold text-slate-800 mb-3">AI Recommendations</p>
        <div className="space-y-2">
          {result.suggestions?.map((suggestion, index) => (
            <div key={index} className="flex items-start gap-2">
              <ChevronRight className={`w-4 h-4 ${style.iconColor} flex-shrink-0 mt-0.5`} />
              <p className="text-sm text-slate-600 leading-relaxed">{suggestion}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-3 mt-5">
        <Link to="/reports" className="btn-secondary flex-1 justify-center text-sm py-2.5">
          <FileText className="w-4 h-4" /> View Report
        </Link>
        <Link to="/chat" className="btn-primary flex-1 justify-center text-sm py-2.5">
          <MessageCircle className="w-4 h-4" /> Talk to Doctor
        </Link>
      </div>

      {footnote && (
        <p className="text-xs text-slate-400 text-center mt-4">{footnote}</p>
      )}
    </div>
  );
}

function LoadingCard({ title, description }) {
  return (
    <div className="card text-center py-10">
      <div className="w-16 h-16 rounded-full bg-primary-50 flex items-center justify-center mx-auto mb-4">
        <Brain className="w-8 h-8 text-primary-400 animate-pulse" />
      </div>
      <p className="font-semibold text-slate-700">{title}</p>
      <p className="text-sm text-slate-400 mt-1">{description}</p>
      <div className="mt-4 h-1.5 bg-slate-100 rounded-full overflow-hidden mx-8">
        <div className="h-full bg-primary-500 rounded-full animate-pulse w-3/4" />
      </div>
    </div>
  );
}

export default function PredictionPage() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [clinicalResult, setClinicalResult] = useState(null);
  const [imageResult, setImageResult] = useState(null);
  const [clinicalLoading, setClinicalLoading] = useState(false);
  const [imageLoading, setImageLoading] = useState(false);
  const [showInfo, setShowInfo] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [imageModels, setImageModels] = useState(IMAGE_MODEL_FALLBACK);
  const [imageModelsLoading, setImageModelsLoading] = useState(true);
  const [selectedModelKey, setSelectedModelKey] = useState('skin_lesion');

  const set = (key) => (event) => setForm((prev) => ({ ...prev, [key]: event.target.value }));

  useEffect(() => {
    let active = true;

    const loadImageModels = async () => {
      try {
        const response = await api.get('/image-models');
        if (!active) {
          return;
        }

        const models = response.data?.models?.length ? response.data.models : IMAGE_MODEL_FALLBACK;
        setImageModels(models);
        const firstAvailable = models.find((model) => model.available) || models[0];
        if (firstAvailable) {
          setSelectedModelKey((current) => {
            const stillExists = models.some((model) => model.key === current);
            return stillExists ? current : firstAvailable.key;
          });
        }
      } catch (error) {
        if (active) {
          setImageModels(IMAGE_MODEL_FALLBACK);
          toast.error('Could not load image screening models.');
        }
      } finally {
        if (active) {
          setImageModelsLoading(false);
        }
      }
    };

    loadImageModels();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
  }, [imagePreview]);

  const selectedModel = imageModels.find((model) => model.key === selectedModelKey) || imageModels[0];

  const scrollToResults = () => {
    setTimeout(() => {
      document.getElementById('results-section')?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const clearImageSelection = () => {
    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }
    setImagePreview('');
    setImageFile(null);
  };

  const selectImageModel = (modelKey) => {
    setSelectedModelKey(modelKey);
    clearImageSelection();
    setImageResult(null);
  };

  const handleClinicalSubmit = async (event) => {
    event.preventDefault();
    const required = ['age', 'bmi', 'physical_activity', 'alcohol_intake'];
    for (const key of required) {
      if (!form[key] && form[key] !== 0) {
        toast.error(`Please enter a value for ${key}`);
        return;
      }
    }

    setClinicalLoading(true);
    setClinicalResult(null);
    try {
      const payload = Object.fromEntries(
        Object.entries(form).map(([key, value]) => [key, parseFloat(value) || 0])
      );
      const response = await api.post('/predict', payload);
      setClinicalResult(response.data);
      toast.success('Clinical analysis complete!');
      scrollToResults();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Prediction failed. Please try again.');
    } finally {
      setClinicalLoading(false);
    }
  };

  const handleImagePick = (event) => {
    const nextFile = event.target.files?.[0];
    if (!nextFile) {
      return;
    }

    if (!nextFile.type.startsWith('image/')) {
      toast.error('Please choose an image file.');
      return;
    }

    if (imagePreview) {
      URL.revokeObjectURL(imagePreview);
    }

    setImageFile(nextFile);
    setImagePreview(URL.createObjectURL(nextFile));
    setImageResult(null);
  };

  const handleImageSubmit = async (event) => {
    event.preventDefault();
    if (!selectedModel?.available) {
      toast.error('This image model is not available yet.');
      return;
    }

    if (!imageFile) {
      toast.error('Please upload an image first.');
      return;
    }

    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('model_key', selectedModelKey);

    setImageLoading(true);
    setImageResult(null);
    try {
      const response = await api.post('/predict-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setImageResult(response.data);
      toast.success('Image screening complete!');
      scrollToResults();
    } catch (error) {
      toast.error(error.response?.data?.error || 'Image prediction failed. Please try another image.');
    } finally {
      setImageLoading(false);
    }
  };

  const resetClinical = () => {
    setForm(DEFAULT_FORM);
    setClinicalResult(null);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar navItems={NAV} role="patient" />
      <main className="lg:ml-64 pt-14 lg:pt-0">
        <div className="max-w-6xl mx-auto p-6">
          <div className="mb-6">
            <div className="flex items-center gap-3 mb-1">
              <div className="w-10 h-10 rounded-2xl bg-primary-50 flex items-center justify-center">
                <Brain className="w-6 h-6 text-primary-600" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900">Cancer Detection</h1>
            </div>
            <p className="text-slate-500 text-sm ml-13">
              Use the clinical assessment or try one of the image-based screening models for skin, breast ultrasound, or colorectal pathology demos.
            </p>
          </div>

          <div className="grid lg:grid-cols-5 gap-6">
            <div className="lg:col-span-3 space-y-6">
              <div className="card">
                <div className="flex items-center gap-2 mb-6 pb-4 border-b border-slate-100">
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                  <h2 className="font-bold text-slate-900">Clinical Parameters</h2>
                  <span className="ml-auto text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded-lg">
                    9 features | ANN Model
                  </span>
                </div>

                <form onSubmit={handleClinicalSubmit} className="space-y-4">
                  {FIELDS.map((field) => (
                    <div key={field.key} className="relative">
                      <div className="flex items-center gap-1.5 mb-1.5">
                        <label className="label mb-0">{field.label}</label>
                        <button
                          type="button"
                          onClick={() => setShowInfo(showInfo === field.key ? null : field.key)}
                          className="text-slate-300 hover:text-primary-400 transition-colors"
                        >
                          <Info className="w-3.5 h-3.5" />
                        </button>
                      </div>
                      {showInfo === field.key && (
                        <div className="mb-2 px-3 py-2 rounded-lg bg-primary-50 text-xs text-primary-700 border border-primary-100">
                          {field.info}
                        </div>
                      )}
                      {field.type === 'select' ? (
                        <select className="input-field" value={form[field.key]} onChange={set(field.key)}>
                          {field.options.map(([value, label]) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      ) : (
                        <input
                          type="number"
                          className="input-field"
                          placeholder={field.placeholder}
                          min={field.min}
                          max={field.max}
                          step={field.step || '1'}
                          value={form[field.key]}
                          onChange={set(field.key)}
                          required
                        />
                      )}
                    </div>
                  ))}

                  <div className="flex gap-3 pt-2">
                    <button type="submit" className="btn-primary flex-1 justify-center py-3" disabled={clinicalLoading}>
                      {clinicalLoading ? (
                        <span className="flex items-center gap-2">
                          <Loader className="w-4 h-4 animate-spin" />
                          Analyzing...
                        </span>
                      ) : (
                        <><Brain className="w-4 h-4" /> Run Clinical Analysis</>
                      )}
                    </button>
                    <button type="button" onClick={resetClinical} className="btn-secondary px-4">Reset</button>
                  </div>
                </form>
              </div>

              <div className="card">
                <div className="flex items-center gap-2 mb-4 pb-4 border-b border-slate-100">
                  <div className="w-2 h-2 rounded-full bg-cyan-500" />
                  <h2 className="font-bold text-slate-900">Image-Based Screening</h2>
                  <span className="ml-auto text-xs text-slate-400 bg-slate-50 px-2 py-1 rounded-lg">
                    3 models | upload-based
                  </span>
                </div>

                {imageModelsLoading ? (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">
                    Loading image screening models...
                  </div>
                ) : (
                  <>
                    <div className="grid md:grid-cols-3 gap-3 mb-4">
                      {imageModels.map((model) => {
                        const isSelected = model.key === selectedModelKey;
                        return (
                          <button
                            key={model.key}
                            type="button"
                            onClick={() => selectImageModel(model.key)}
                            className={`text-left rounded-2xl border p-4 transition-all ${
                              isSelected
                                ? 'border-primary-400 bg-primary-50 shadow-sm'
                                : 'border-slate-200 bg-white hover:border-primary-200'
                            }`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <p className="font-semibold text-slate-900 leading-snug">{model.title}</p>
                                <p className="text-xs text-slate-500 mt-1">{model.dataset}</p>
                              </div>
                              <span className={`text-[10px] font-bold px-2 py-1 rounded-full ${model.available ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>
                                {model.available ? 'READY' : 'OFFLINE'}
                              </span>
                            </div>
                            <p className="text-xs text-slate-500 mt-3 leading-relaxed">{model.short_note || model.note}</p>
                          </button>
                        );
                      })}
                    </div>

                    <form onSubmit={handleImageSubmit} className="space-y-4">
                      <div className="rounded-2xl border border-dashed border-primary-200 bg-primary-50/50 p-5">
                        <div className="flex items-start gap-3">
                          <div className="w-11 h-11 rounded-2xl bg-white flex items-center justify-center shadow-sm flex-shrink-0">
                            <ImageIcon className="w-5 h-5 text-primary-500" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-semibold text-slate-900">{selectedModel?.title || 'Select an image model'}</p>
                            <p className="text-sm text-slate-500 mt-1">
                              {selectedModel?.input_hint || 'Choose an image model to see upload guidance.'}
                            </p>
                            <p className="text-xs text-slate-400 mt-2">
                              {selectedModel?.model_name || 'Model metadata will appear here once loaded.'}
                            </p>
                          </div>
                        </div>

                        <label className="block mt-4">
                          <span className="sr-only">Choose image</span>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleImagePick}
                            className="block w-full text-sm text-slate-500 file:mr-4 file:rounded-xl file:border-0 file:bg-primary-600 file:px-4 file:py-2.5 file:font-semibold file:text-white hover:file:bg-primary-700"
                          />
                        </label>

                        <div className="mt-3 text-xs text-slate-500 space-y-1">
                          <p>{selectedModel?.note || 'This AI result is a demo aid and not a medical diagnosis.'}</p>
                          {!selectedModel?.available && (
                            <p>This model is not currently available from the backend.</p>
                          )}
                        </div>
                      </div>

                      {imagePreview && (
                        <div className="rounded-2xl border border-slate-200 bg-white p-4">
                          <div className="flex items-center justify-between gap-3 mb-3">
                            <div className="min-w-0">
                              <p className="font-semibold text-slate-900 truncate">{imageFile?.name}</p>
                              <p className="text-xs text-slate-500">Preview before screening</p>
                            </div>
                            <button
                              type="button"
                              onClick={clearImageSelection}
                              className="text-slate-400 hover:text-slate-600 transition-colors"
                              aria-label="Remove selected image"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                          <img
                            src={imagePreview}
                            alt="Selected image preview"
                            className="w-full max-h-72 object-contain rounded-2xl bg-slate-50"
                          />
                        </div>
                      )}

                      <div className="flex gap-3 pt-1">
                        <button type="submit" className="btn-primary flex-1 justify-center py-3" disabled={imageLoading || !selectedModel?.available}>
                          {imageLoading ? (
                            <span className="flex items-center gap-2">
                              <Loader className="w-4 h-4 animate-spin" />
                              Screening image...
                            </span>
                          ) : (
                            <><Upload className="w-4 h-4" /> Run Image Screening</>
                          )}
                        </button>
                        <button type="button" onClick={clearImageSelection} className="btn-secondary px-4">
                          Clear
                        </button>
                      </div>
                    </form>
                  </>
                )}
              </div>
            </div>

            <div className="lg:col-span-2 space-y-4" id="results-section">
              {!clinicalResult && !imageResult && !clinicalLoading && !imageLoading && (
                <>
                  <div className="card border-primary-100">
                    <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                      <Info className="w-4 h-4 text-primary-500" /> Clinical Risk Model
                    </h3>
                    <div className="space-y-3 text-sm text-slate-600">
                      <p>Our clinical model analyzes structured patient inputs and produces a multi-class cancer risk estimate.</p>
                      <ul className="space-y-1.5">
                        {[
                          '9 structured biomarkers',
                          'ANN-based clinical risk classification',
                          'Risk levels from LOW to CRITICAL',
                          'Designed for quick triage and follow-up guidance',
                        ].map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="card border-cyan-100">
                    <h3 className="font-bold text-slate-900 mb-3 flex items-center gap-2">
                      <Info className="w-4 h-4 text-cyan-500" /> Image Screening Models
                    </h3>
                    <div className="space-y-3 text-sm text-slate-600">
                      <p>The project now includes three image-based demo models alongside the clinical form.</p>
                      <ul className="space-y-1.5">
                        {[
                          'Skin lesion screening with DermaMNIST',
                          'Breast ultrasound screening with BreastMNIST',
                          'Colorectal pathology tile screening with PathMNIST',
                          'Each model expects its own image type and is for demo use only',
                        ].map((item) => (
                          <li key={item} className="flex items-start gap-2">
                            <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                            {item}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </>
              )}

              {clinicalLoading && (
                <LoadingCard
                  title="Analyzing your clinical data..."
                  description="AI is processing the 9 patient biomarkers."
                />
              )}

              {imageLoading && (
                <LoadingCard
                  title="Screening your uploaded image..."
                  description={selectedModel?.title || 'The selected image model is extracting visual features.'}
                />
              )}

              {clinicalResult && (
                <ResultCard
                  result={clinicalResult}
                  title="Clinical Risk Assessment"
                  footnote="AI assessment only. Always consult a qualified physician for diagnosis."
                />
              )}

              {imageResult && (
                <ResultCard
                  result={imageResult}
                  title={imageResult.screening_title || 'Image Screening'}
                  details={[
                    `Model: ${imageResult.model_name}`,
                    `Dataset: ${imageResult.dataset}`,
                    `File: ${imageResult.filename}`,
                  ]}
                  footnote={imageResult.note}
                />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
