import { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { supabase } from '../lib/supabase';

export default function RobotCompanies() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [companies, setCompanies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [workflowModal, setWorkflowModal] = useState(null);
  const [workflowForm, setWorkflowForm] = useState({
    workflow_stage: '',
    next_action: '',
    next_action_date: '',
    assigned_to: '',
    workflow_notes: '',
    blockers: ''
  });
  const [emailModal, setEmailModal] = useState(null);
  const [emailContent, setEmailContent] = useState(null);
  const [loadingEmail, setLoadingEmail] = useState(false);

  // Admin authentication check
  useEffect(() => {
    async function checkAdmin() {
      if (!supabase) {
        // No Supabase = local dev mode, allow access
        setIsAdmin(true);
        setCheckingAuth(false);
        return;
      }

      const { data: { user } } = await supabase.auth.getUser();
      
      if (!user) {
        // Not logged in, redirect to login
        router.push('/login?redirect=/robot-companies');
        return;
      }

      // Check if user is admin (you can customize this logic)
      // For now, check if email matches admin emails
      const adminEmails = ['admin@readyforrobots.com', 'robert@readyforrobots.com'];
      const userIsAdmin = adminEmails.includes(user.email);

      if (!userIsAdmin) {
        // Not an admin, redirect to homepage
        alert('Access denied. This page is for administrators only.');
        router.push('/');
        return;
      }

      setIsAdmin(true);
      setCheckingAuth(false);
    }

    checkAdmin();
  }, [router]);

  useEffect(() => {
    if (!checkingAuth && isAdmin) {
      loadStats();
      loadCompanies();
    }
  }, [filter, checkingAuth, isAdmin]);

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

  function openWorkflowModal(company) {
    setWorkflowModal(company);
    setWorkflowForm({
      workflow_stage: company.workflow_stage || '',
      next_action: company.next_action || '',
      next_action_date: company.next_action_date ? company.next_action_date.split('T')[0] : '',
      assigned_to: company.assigned_to || '',
      workflow_notes: '',
      blockers: company.blockers || ''
    });
  }

  async function saveWorkflow() {
    if (!workflowModal) return;
    
    try {
      const res = await fetch(`http://localhost:8000/api/robot-companies/${workflowModal.id}/workflow`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workflowForm)
      });
      
      if (res.ok) {
        setWorkflowModal(null);
        loadCompanies(); // Refresh list
      }
    } catch (error) {
      console.error('Failed to update workflow:', error);
    }
  }

  async function generateEmail(company, templateType) {
    setEmailModal(company);
    setLoadingEmail(true);
    setEmailContent(null);
    
    try {
      const res = await fetch(`http://localhost:8000/api/robot-companies/${company.id}/email?template_type=${templateType}`);
      const data = await res.json();
      setEmailContent(data.email);
    } catch (error) {
      console.error('Failed to generate email:', error);
      setEmailContent({ error: 'Failed to generate email' });
    }
    setLoadingEmail(false);
  }

  function copyEmail() {
    if (!emailContent) return;
    const fullEmail = `Subject: ${emailContent.subject}\n\n${emailContent.body}`;
    navigator.clipboard.writeText(fullEmail);
    alert('Email copied to clipboard!');
  }

  // Show loading state while checking authentication
  if (checkingAuth) {
    return (
      <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ marginBottom: '16px', fontSize: '18px', color: '#10B981' }}>🔒 Checking admin access...</div>
        </div>
      </div>
    );
  }

  // Don't render page content if not admin
  if (!isAdmin) {
    return null;
  }

  return (
    <div style={{ minHeight: '100vh', background: '#0a0a0a', color: '#fff', padding: '40px 20px' }}>
      <Head>
        <title>[ADMIN] Robot Companies | Ready For Robots</title>
      </Head>

      <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
        {/* Admin Badge */}
        <div style={{ 
          background: '#10B981', 
          color: '#000', 
          padding: '8px 16px', 
          borderRadius: '4px', 
          display: 'inline-block',
          fontSize: '11px',
          fontWeight: '600',
          letterSpacing: '0.5px',
          marginBottom: '20px'
        }}>
          🔒 ADMIN ONLY
        </div>

        {/* Header */}
        <div style={{ marginBottom: '30px' }}>
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: '600', 
            marginBottom: '8px',
            color: '#10B981'
          }}>
            [Robot Ready] Companies
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
                  <th style={thStyle}>U.S. Presence</th>
                  <th style={thStyle}>Urgency</th>
                  <th style={thStyle}>Workflow</th>
                  <th style={thStyle}>Next Action</th>
                  <th style={thStyle}>Actions</th>
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
                      {comp.workflow_stage ? (
                        <span style={{
                          color: comp.workflow_stage === 'partnership' ? '#10B981' :
                                 comp.workflow_stage === 'demo' ? '#06B6D4' :
                                 comp.workflow_stage === 'proposal' ? '#F59E0B' : '#a3a3a3',
                          fontSize: '12px',
                          textTransform: 'capitalize'
                        }}>
                          {comp.workflow_stage}
                        </span>
                      ) : (
                        <span style={{ color: '#525252', fontSize: '12px' }}>—</span>
                      )}
                    </td>
                    <td style={{...tdStyle, maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                      {comp.next_action ? (
                        <span style={{ color: '#a3a3a3', fontSize: '12px' }}>
                          {comp.next_action}
                          {comp.next_action_date && (
                            <span style={{ marginLeft: '6px', color: '#525252' }}>
                              ({new Date(comp.next_action_date).toLocaleDateString()})
                            </span>
                          )}
                        </span>
                      ) : (
                        <span style={{ color: '#525252', fontSize: '12px' }}>—</span>
                      )}
                    </td>
                    <td style={tdStyle}>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button
                          onClick={() => generateEmail(comp, 'intro')}
                          style={{
                            background: 'transparent',
                            border: '1px solid #404040',
                            color: '#06B6D4',
                            padding: '6px 12px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={e => e.target.style.borderColor = '#06B6D4'}
                          onMouseLeave={e => e.target.style.borderColor = '#404040'}
                        >
                          📧 Email
                        </button>
                        <button
                          onClick={() => openWorkflowModal(comp)}
                          style={{
                            background: 'transparent',
                            border: '1px solid #404040',
                            color: '#10B981',
                            padding: '6px 12px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s'
                          }}
                          onMouseEnter={e => e.target.style.borderColor = '#10B981'}
                          onMouseLeave={e => e.target.style.borderColor = '#404040'}
                        >
                          Workflow
                        </button>
                      </div>
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

      {/* Email Modal */}
      {emailModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div style={{
            background: '#0a0a0a',
            border: '1px solid #262626',
            borderRadius: '8px',
            padding: '32px',
            maxWidth: '800px',
            width: '100%',
            maxHeight: '90vh',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '600', color: '#06B6D4' }}>
                📧 Email Introduction: {emailModal.company_name}
              </h2>
              <button
                onClick={() => setEmailModal(null)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#737373',
                  fontSize: '24px',
                  cursor: 'pointer',
                  padding: '0'
                }}
              >
                ×
              </button>
            </div>

            {/* Template Type Selector */}
            <div style={{ marginBottom: '20px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              {['intro', 'demo', 'proposal', 'followup', 'hot_lead'].map(type => (
                <button
                  key={type}
                  onClick={() => generateEmail(emailModal, type)}
                  style={{
                    background: 'transparent',
                    border: '1px solid #404040',
                    color: '#10B981',
                    padding: '8px 16px',
                    borderRadius: '4px',
                    fontSize: '13px',
                    cursor: 'pointer',
                    textTransform: 'capitalize'
                  }}
                >
                  {type.replace('_', ' ')}
                </button>
              ))}
            </div>

            {loadingEmail ? (
              <div style={{ padding: '40px', textAlign: 'center', color: '#525252' }}>
                Generating personalized email...
              </div>
            ) : emailContent && !emailContent.error ? (
              <div>
                {/* Subject */}
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '8px' }}>
                    Subject
                  </label>
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    borderRadius: '4px',
                    padding: '12px',
                    fontSize: '14px',
                    color: '#fff',
                    fontWeight: '500'
                  }}>
                    {emailContent.subject}
                  </div>
                </div>

                {/* Body */}
                <div style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '8px' }}>
                    Email Body
                  </label>
                  <div style={{
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    borderRadius: '4px',
                    padding: '16px',
                    fontSize: '14px',
                    color: '#a3a3a3',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'monospace',
                    lineHeight: '1.6',
                    maxHeight: '400px',
                    overflow: 'auto'
                  }}>
                    {emailContent.body}
                  </div>
                </div>

                {/* Follow-up reminder */}
                {emailContent.suggested_followup_days && (
                  <div style={{
                    background: '#1a1a1a',
                    border: '1px solid #262626',
                    borderRadius: '4px',
                    padding: '12px',
                    fontSize: '13px',
                    color: '#F59E0B',
                    marginBottom: '20px'
                  }}>
                    💡 Suggested follow-up: {emailContent.suggested_followup_days} days
                  </div>
                )}

                {/* Action Buttons */}
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button
                    onClick={copyEmail}
                    style={{
                      flex: 1,
                      background: 'transparent',
                      border: '1px solid #06B6D4',
                      color: '#06B6D4',
                      padding: '12px 24px',
                      borderRadius: '4px',
                      fontSize: '14px',
                      fontWeight: '500',
                      cursor: 'pointer'
                    }}
                  >
                    📋 Copy to Clipboard
                  </button>
                  <button
                    onClick={() => setEmailModal(null)}
                    style={{
                      background: 'transparent',
                      border: '1px solid #404040',
                      color: '#a3a3a3',
                      padding: '12px 24px',
                      borderRadius: '4px',
                      fontSize: '14px',
                      cursor: 'pointer'
                    }}
                  >
                    Close
                  </button>
                </div>
              </div>
            ) : emailContent?.error ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#EF4444' }}>
                {emailContent.error}
              </div>
            ) : null}
          </div>
        </div>
      )}

      {/* Workflow Modal */}
      {workflowModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0,0,0,0.8)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: '#0a0a0a',
            border: '1px solid #262626',
            borderRadius: '8px',
            padding: '32px',
            maxWidth: '600px',
            width: '90%'
          }}>
            <h2 style={{ 
              fontSize: '20px', 
              fontWeight: '600', 
              color: '#10B981', 
              marginBottom: '20px' 
            }}>
              Workflow: {workflowModal.company_name}
            </h2>

            <div style={{ display: 'grid', gap: '16px' }}>
              {/* Workflow Stage */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Workflow Stage
                </label>
                <select
                  value={workflowForm.workflow_stage}
                  onChange={e => setWorkflowForm({...workflowForm, workflow_stage: e.target.value})}
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                >
                  <option value="">Select stage...</option>
                  <option value="research">Research</option>
                  <option value="outreach">Outreach</option>
                  <option value="demo">Demo Scheduled</option>
                  <option value="proposal">Proposal Sent</option>
                  <option value="negotiation">Negotiation</option>
                  <option value="partnership">Partnership</option>
                </select>
              </div>

              {/* Next Action */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Next Action
                </label>
                <input
                  type="text"
                  value={workflowForm.next_action}
                  onChange={e => setWorkflowForm({...workflowForm, next_action: e.target.value})}
                  placeholder="e.g., Send partnership intro email"
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Next Action Date */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Next Action Date
                </label>
                <input
                  type="date"
                  value={workflowForm.next_action_date}
                  onChange={e => setWorkflowForm({...workflowForm, next_action_date: e.target.value})}
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Assigned To */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Assigned To
                </label>
                <input
                  type="text"
                  value={workflowForm.assigned_to}
                  onChange={e => setWorkflowForm({...workflowForm, assigned_to: e.target.value})}
                  placeholder="e.g., Sales Team, Technical Team"
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Workflow Notes */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Add Note
                </label>
                <textarea
                  value={workflowForm.workflow_notes}
                  onChange={e => setWorkflowForm({...workflowForm, workflow_notes: e.target.value})}
                  placeholder="Log activity, notes, outcomes..."
                  rows={3}
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px',
                    resize: 'vertical'
                  }}
                />
              </div>

              {/* Blockers */}
              <div>
                <label style={{ display: 'block', fontSize: '13px', color: '#737373', marginBottom: '6px' }}>
                  Blockers
                </label>
                <input
                  type="text"
                  value={workflowForm.blockers}
                  onChange={e => setWorkflowForm({...workflowForm, blockers: e.target.value})}
                  placeholder="What's preventing progress?"
                  style={{
                    width: '100%',
                    background: '#0a0a0a',
                    border: '1px solid #404040',
                    color: '#fff',
                    padding: '10px',
                    borderRadius: '4px',
                    fontSize: '14px'
                  }}
                />
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
                <button
                  onClick={saveWorkflow}
                  style={{
                    flex: 1,
                    background: 'transparent',
                    border: '1px solid #10B981',
                    color: '#10B981',
                    padding: '12px 24px',
                    borderRadius: '4px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer'
                  }}
                >
                  Save Workflow
                </button>
                <button
                  onClick={() => setWorkflowModal(null)}
                  style={{
                    flex: 1,
                    background: 'transparent',
                    border: '1px solid #404040',
                    color: '#a3a3a3',
                    padding: '12px 24px',
                    borderRadius: '4px',
                    fontSize: '14px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
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