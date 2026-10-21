import React, { useState } from 'react';
import {
  User,
  Mail,
  School,
  BookOpen,
  GraduationCap,
  Save,
  ShieldCheck,
  Calendar,
  CheckCircle2,
  Clock,
  Target,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import Card from '../components/common/Card';
import Button from '../components/common/Button';

export const Profile = () => {
  const { user, updateUserProfile } = useAuth();
  const { success } = useToast();

  const [formData, setFormData] = useState({
    full_name: user?.full_name || 'Alex Rivera',
    email: user?.email || 'student@university.edu',
    college: user?.college || 'School of Engineering',
    major: user?.major || 'Computer Science',
    target_study_hours: '2',
    academic_goal: 'Prepare for midterm examinations and build mastery in core engineering subjects.',
  });

  const [saving, setSaving] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setSaving(true);
    setTimeout(() => {
      updateUserProfile(formData);
      setSaving(false);
      success('Student profile updated successfully!');
    }, 400);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-300">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-tight">Student Profile</h1>
        <p className="text-sm text-slate-400 mt-1">
          Manage your academic background, degree program, and daily study targets.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left Col: Identity Card */}
        <div className="space-y-6">
          <Card className="p-6 text-center space-y-4">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 text-white font-extrabold text-2xl mx-auto flex items-center justify-center shadow-xl shadow-indigo-600/30">
              {formData.full_name ? formData.full_name.slice(0, 2).toUpperCase() : 'ST'}
            </div>

            <div>
              <h3 className="text-base font-bold text-white">{formData.full_name}</h3>
              <p className="text-xs text-slate-400">{formData.email}</p>
              <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium">
                <GraduationCap className="w-3.5 h-3.5" />
                <span>{formData.major}</span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800 text-left space-y-2 text-xs text-slate-400">
              <div className="flex items-center justify-between">
                <span>Institution:</span>
                <span className="font-semibold text-slate-200">{formData.college}</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Account Role:</span>
                <span className="font-semibold text-indigo-400">Verified Student</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Isolation Level:</span>
                <span className="font-semibold text-emerald-400">Strictly Isolated</span>
              </div>
            </div>
          </Card>

          {/* Privacy Reassurance */}
          <div className="p-4 rounded-2xl bg-indigo-950/20 border border-indigo-500/20 space-y-2">
            <div className="flex items-center gap-2 text-indigo-400 text-xs font-semibold">
              <ShieldCheck className="w-4 h-4" />
              <span>Data Protection Guarantee</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Your uploaded notes, vector embeddings, chat transcripts, and quizzes are strictly partitioned by your student ID. Cross-user access is blocked at the database query level.
            </p>
          </div>
        </div>

        {/* Right 2 Cols: Form Edit */}
        <div className="md:col-span-2">
          <Card
            title="Academic Information"
            subtitle="Details used to calibrate AI study suggestions"
            icon={User}
          >
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    required
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    College / University
                  </label>
                  <input
                    type="text"
                    name="college"
                    value={formData.college}
                    onChange={handleChange}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                    Major / Concentration
                  </label>
                  <input
                    type="text"
                    name="major"
                    value={formData.major}
                    onChange={handleChange}
                    className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Daily Study Goal (Hours)
                </label>
                <input
                  type="number"
                  min="1"
                  max="12"
                  name="target_study_hours"
                  value={formData.target_study_hours}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Academic Focus & Learning Objective
                </label>
                <textarea
                  rows={3}
                  name="academic_goal"
                  value={formData.academic_goal}
                  onChange={handleChange}
                  className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3.5 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <div className="pt-4 flex justify-end">
                <Button
                  type="submit"
                  variant="primary"
                  loading={saving}
                  icon={Save}
                >
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
