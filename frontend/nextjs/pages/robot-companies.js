import { useState, useEffect } from 'react';
import Head from 'next/head';

export default function RobotCompanies() {
  const [companies, setCompanies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadStats();
    loadCompanies();
  }, [filter]);

  async function loadStats() {
    try {
      const res = await fetch('http://localhost:8000/api/robot-companies/stats');
      const data = await res.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  }

  async function loadCompanies() {
    setLoading(true);
    try {
      let url = 'http://localhost:8000/api/robot-companies/';
      
      if (filter === 'hot') {
        url = 'http://localhost:8000/api/robot-companies/hot-leads';
      } else if (filter === 'chinese-no-us') {
        url = 'http://localhost:8000/api/robot-companies/chinese-companies?us_presence=none';
      } else if (filter === 'needs-distribution') {
        url = 'http://localhost:8000/api/robot-companies/needs-distribution';
      } else if (filter === 'wave_2') {
        url = 'http://localhost:8000/api/robot-companies/?market_entry_wave=wave_2';
      }

      const res = await fetch(url);
      const data = await res.json();
      
      if (data.companies) {
        setCompanies(data.companies);
      } else if (data.hot_leads) {
        setCompanies(data.hot_leads);
      }
    } catch (error) {
      console.error('Failed to load companies:', error);
    }
    setLoading(false);
  }

  const filteredCompanies = companies.filter(comp => 
    search ? comp.company_name.toLowerCase().includes(search.toLowerCase()) : true
  );

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', padding: '40px 20px' }}>
      <Head>
        <title>Robots Ready Companies | Ready For Robots</title>
      </Head>

      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '30px' }}>
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: '600', 
            marginBottom: '8px',
            color: '#10B981'
          }}>
            Robots Ready Companies
          </h1>
          <p style={{ fontSize: '14px', color: '#737373' }}>
            200+ robotics companies • Chinese → U.S. market entry focus
          </p>
        </div>

        {/* Stats - Inline Text */}
        {stats && (
          <div style={{ 
            marginBottom: '30px',
            padding: '16px 0',
            borderBottom: '1px solid #262626',
            fontSize: '14px',
            color: '#a3a3a3'
          }}>
            <span style={{ marginRight: '24px' }}>
              Total: <span style={{ color: '#fff', fontWeight: '500' }}>{stats.total_companies}</span>
            </span>
            <span style={{ marginRight: '24px' }}>
              Chinese: <span style={{ color: '#fff', fontWeight: '500' }}>{stats.chinese_companies}</span>
            </span>
            <span style={{ marginRight: '24px' }}>
              Hot Leads: <span style={{ color: '#10B981', fontWeight: '600' }}>{stats.hot_leads}</span>
            </span>
            <span style={{ marginRight: '24px' }}>
              Needs Distribution: <span style={{ color: '#fff', fontWeight: '500' }}>{stats.needs_distribution}</span>
            </span>
            <span>
              No U.S. Presence: <span style={{ color: '#10B981', fontWeight: '600' }}>{stats.no_us_presence}</span>
            </span>
          </div>
        )}

        {/* Filters - Minimal Inline */}
        <div style={{ 
          marginBottom: '24px',
          paddingBottom: '16px',
          borderBottom: '1px solid #262626'
        }}>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
            <label style={{ fontSize: '13px', color: '#737373' }}>
              Filter:
            </label>
            <select 
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{
                padding: '6px 10px',
                background: 'transparent',
                border: '1px solid #404040',
                borderRadius: '6px',
                color: '#a3a3a3',
                fontSize: '13px',
                cursor: 'pointer'
              }}
            >
              <option value="all">All Companies</option>
              <option value="hot">Hot Leads (score ≥ 80)</option>
              <option value="chinese-no-us">Chinese (No U.S. Presence)</option>
              <option value="needs-distribution">Needs Distribution</option>
              <option value="wave_2">Wave 2 (2024-2026 Expansion)</option>
            </select>

            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search companies..."
              style={{
                flex: '1',
                minWidth: '200px',
                padding: '6px 10px',
                background: 'transparent',
                border: '1px solid #404040',
                borderRadius: '6px',
                color: '#fff',
                fontSize: '13px'
              }}
            />
          </div>
        </div>

        {/* Companies Table - Minimal Border-Only */}
        <div style={{ 
          border: '1px solid #262626',
          borderRadius: '6px',
          overflow: 'hidden'
        }}>
          {loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#525252', fontSize: '14px' }}>
              Loading companies...
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #262626' }}>
                  <th style={thStyle}>Score</th>
                  <th style={thStyle}>Company</th>
                  <th style={thStyle}>Type</th>
                  <th style={thStyle}>Country</th>
                  <th style={thStyle}>U.S. Presence</th>
                  <th style={thStyle}>Urgency</th>
                  <th style={thStyle}>Wave</th>
                  <th style={thStyle}>Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredCompanies.map((comp, idx) => (
                  <tr 
                    key={comp.id}
                    style={{ 
                      borderBottom: idx < filteredCompanies.length - 1 ? '1px solid #1a1a1a' : 'none'
                    }}
                  >
                    <td style={tdStyle}>
                      <span style={{
                        color: comp.lead_score >= 85 ? '#10B981' : comp.lead_score >= 70 ? '#F59E0B' : '#737373',
                        fontWeight: '600',
                        fontSize: '14px'
                      }}>
                        {comp.lead_score}
                      </span>
                    </td>
                    <td style={{...tdStyle, color: '#fff', fontWeight: '500'}}>
                      {comp.company_name}
                      {comp.lead_score >= 90 && <span style={{ marginLeft: '6px', fontSize: '12px' }}>⭐</span>}
                    </td>
                    <td style={tdStyle}>
                      <span style={{
                        color: '#a3a3a3',
                        fontSize: '13px'
                      }}>
                        {comp.robot_type}
                      </span>
                    </td>
                    <td style={{...tdStyle, color: '#a3a3a3'}}>{comp.country}</td>
                    <td style={tdStyle}>
                      {comp.us_presence === 'none' ? (
                        <span style={{ color: '#F59E0B', fontSize: '13px' }}>None</span>
                      ) : comp.us_presence === 'office' ? (
                        <span style={{ color: '#10B981', fontSize: '13px' }}>Office</span>
                      ) : (
                        <span style={{ color: '#06B6D4', fontSize: '13px' }}>Distributor</span>
                      )}
                    </td>
                    <td style={tdStyle}>
                      {comp.distributor_urgency === 'high' ? (
                        <span style={{ color: '#EF4444', fontSize: '13px', fontWeight: '500' }}>HIGH</span>
                      ) : comp.distributor_urgency === 'medium' ? (
                        <span style={{ color: '#F59E0B', fontSize: '13px' }}>Medium</span>
                      ) : (
                        <span style={{ color: '#525252', fontSize: '13px' }}>Low</span>
                      )}
                    </td>
                    <td style={tdStyle}>
                      <span style={{ 
                        color: comp.market_entry_wave === 'wave_2' ? '#10B981' : 
                               comp.market_entry_wave === 'wave_3' ? '#06B6D4' : '#525252',
                        fontSize: '13px'
                      }}>
                        {comp.market_entry_wave?.replace('wave_', 'Wave ')}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      <span style={{
                        color: comp.outreach_status === 'partnership' ? '#10B981' :
                               comp.outreach_status === 'meeting_scheduled' ? '#06B6D4' :
                               comp.outreach_status === 'responded' ? '#F59E0B' :
                               comp.outreach_status === 'contacted' ? '#a3a3a3' : '#525252',
                        fontSize: '12px'
                      }}>
                        {comp.outreach_status?.replace('_', ' ') || 'not contacted'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div style={{ marginTop: '16px', color: '#525252', fontSize: '13px' }}>
          {filteredCompanies.length} companies
        </div>
      </div>
    </div>
  );
}

const thStyle = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: '11px',
  fontWeight: '500',
  color: '#737373',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
  background: 'transparent'
};

const tdStyle = {
  padding: '12px 16px',
  fontSize: '13px',
  color: '#a3a3a3'
};