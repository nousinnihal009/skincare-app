import React, { useState, useEffect } from 'react';
import { searchDoctors } from '../api';

interface Doctor {
  id: number;
  name: string;
  specialty: string;
  subspecialty: string;
  rating: number;
  reviews: number;
  experience_years: number;
  hospital: string;
  address: string;
  city: string;
  state: string;
  phone: string;
  email: string;
  availability: string;
  accepts_insurance: boolean;
  telemedicine: boolean;
  bio: string;
}

const DoctorFinder: React.FC = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [loading, setLoading] = useState(true);
  const [specialty, setSpecialty] = useState('');
  const [city, setCity] = useState('');

  const fetchDoctors = async () => {
    setLoading(true);
    try {
      const res = await searchDoctors({ specialty: specialty || undefined, city: city || undefined });
      setDoctors(res.doctors || []);
    } catch { setDoctors([]); }
    setLoading(false);
  };

  useEffect(() => { fetchDoctors(); }, []);

  const renderStars = (rating: number) => {
    return '★'.repeat(Math.round(rating)) + '☆'.repeat(5 - Math.round(rating));
  };

  return (
    <div className="page-container" style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div className="page-header">
        <h1 className="page-title animate-fade-in-up">👨‍⚕️ Find a Dermatologist</h1>
        <p className="page-subtitle animate-fade-in-up stagger-1">
          Connect with board-certified dermatologists for professional evaluation and treatment.
        </p>
      </div>

      {/* Search Filters */}
      <div className="glass-card animate-fade-in-up stagger-2" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'end' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '6px', display: 'block' }}>Specialty</label>
            <input className="input-field" placeholder="e.g. Melanoma, Acne, Psoriasis" value={specialty} onChange={e => setSpecialty(e.target.value)} id="doctor-specialty" />
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <label style={{ color: 'var(--dark-200)', fontSize: '0.85rem', marginBottom: '6px', display: 'block' }}>City</label>
            <input className="input-field" placeholder="e.g. New York, Los Angeles" value={city} onChange={e => setCity(e.target.value)} id="doctor-city" />
          </div>
          <button className="btn-primary" onClick={fetchDoctors} style={{ height: '46px' }} id="doctor-search">Search</button>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <div className="spinner" style={{ margin: '0 auto' }} />
        </div>
      ) : doctors.length === 0 ? (
        <div className="glass-card" style={{ textAlign: 'center', padding: '40px' }}>
          <p style={{ color: 'var(--dark-200)' }}>No doctors found matching your criteria. Try adjusting your search.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {doctors.map((doc, i) => (
            <div key={doc.id} className="glass-card doctor-card animate-fade-in-up" style={{ animationDelay: `${i * 0.1}s`, opacity: 0 }}>
              <div className="doctor-avatar">
                {doc.name.split(' ').map(n => n[0]).join('').slice(0, 2)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <h3 style={{ color: 'white', fontWeight: 700, fontSize: '1.1rem', marginBottom: '4px' }}>{doc.name}</h3>
                    <p style={{ color: 'var(--primary-300)', fontSize: '0.9rem', fontWeight: 500 }}>{doc.specialty} — {doc.subspecialty}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ color: '#fbbf24', fontSize: '0.9rem', letterSpacing: '2px' }}>{renderStars(doc.rating)}</div>
                    <p style={{ color: 'var(--dark-200)', fontSize: '0.8rem' }}>{doc.rating} ({doc.reviews} reviews)</p>
                  </div>
                </div>

                <p style={{ color: 'var(--dark-200)', fontSize: '0.9rem', margin: '12px 0', lineHeight: 1.5 }}>{doc.bio}</p>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '12px' }}>
                  <span className="badge badge-blue">{doc.experience_years} yrs experience</span>
                  {doc.telemedicine && <span className="badge badge-green">Telemedicine</span>}
                  {doc.accepts_insurance && <span className="badge badge-purple">Accepts Insurance</span>}
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', fontSize: '0.85rem', color: 'var(--dark-200)' }}>
                  <span>📍 {doc.city}, {doc.state}</span>
                  <span>🕐 {doc.availability}</span>
                  <span>📞 {doc.phone}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="disclaimer" style={{ marginTop: '24px' }}>
        <span>⚠️</span>
        <span>This is a sample directory for demonstration. Please verify doctor credentials and availability independently.</span>
      </div>
    </div>
  );
};

export default DoctorFinder;
