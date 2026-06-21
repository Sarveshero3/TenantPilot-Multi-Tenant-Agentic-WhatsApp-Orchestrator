import type { Tenant } from '../types'
import './TenantSidebar.css'

interface TenantSidebarProps {
  backendOnline: boolean | null
  loading: boolean
  selectedTenantId: string
  tenants: Tenant[]
  onSelectTenant: (tenantId: string) => void
}

function initials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()
}

export function TenantSidebar({
  backendOnline,
  loading,
  selectedTenantId,
  tenants,
  onSelectTenant,
}: TenantSidebarProps) {
  const statusLabel = backendOnline === null ? 'Checking API' : backendOnline ? 'API online' : 'API offline'
  const statusClass = backendOnline === null ? '' : backendOnline ? 'online' : 'offline'

  return (
    <aside className="panel tenant-sidebar">
      <div className="tenant-brand">
        <div className="brand-mark">TP</div>
        <div>
          <h1>TenantPilot</h1>
          <p>Agentic WhatsApp Orchestrator</p>
        </div>
      </div>

      <div className="tenant-health pill">
        <span className={`dot ${statusClass}`} />
        {statusLabel}
      </div>

      <div className="panel-header tenant-header">
        <p className="panel-eyebrow">Tenants</p>
        <h2 className="panel-title">Workspace selector</h2>
        <p className="panel-subtitle">Switch brands to inspect live sessions and outbound replies.</p>
      </div>

      <div className="tenant-list scroll-region">
        {loading && (
          <div className="skeleton-list" aria-label="Loading tenants">
            <div className="skeleton-card" />
            <div className="skeleton-card" />
          </div>
        )}

        {!loading && tenants.length === 0 && (
          <div className="empty-state">
            <strong>No tenants found</strong>
            <span>Seed the backend database, then refresh this dashboard.</span>
          </div>
        )}

        {!loading &&
          tenants.map((tenant) => (
            <button
              className={`tenant-card${tenant.tenant_id === selectedTenantId ? ' tenant-card-active' : ''}`}
              key={tenant.tenant_id}
              type="button"
              onClick={() => onSelectTenant(tenant.tenant_id)}
            >
              <span className="tenant-avatar">{initials(tenant.name)}</span>
              <span className="tenant-copy">
                <span className="tenant-name">{tenant.name}</span>
                <span className="tenant-meta">{tenant.media_keys.length} media assets</span>
              </span>
              <span className="tenant-status-dot" aria-hidden="true" />
            </button>
          ))}
      </div>
    </aside>
  )
}
