import { AlertTriangle, CheckCircle2, Clock, FileUp, History, RefreshCw, XCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { createReview, fetchAuditEvents, fetchDataSources, fetchRecords, ingestTravelJson, setApiContext, uploadCsv } from "./api";

const defaultTenant = "demo-corp";
const defaultAnalyst = "analyst@example.com";

export default function App() {
  const queryClient = useQueryClient();
  const [tenantSlug, setTenantSlug] = useState(defaultTenant);
  const [analystEmail, setAnalystEmail] = useState(defaultAnalyst);
  const [status, setStatus] = useState("pending");
  const [suspicious, setSuspicious] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  setApiContext({ tenantSlug, analystEmail });

  useEffect(() => {
    setApiContext({ tenantSlug, analystEmail });
  }, [tenantSlug, analystEmail]);

  const recordsQuery = useQuery({
    queryKey: ["records", tenantSlug, status, suspicious],
    queryFn: () => fetchRecords({ status, suspicious })
  });

  const records = recordsQuery.data || [];
  const selected = useMemo(() => records.find((record) => record.id === selectedId) || records[0], [records, selectedId]);

  const auditQuery = useQuery({
    queryKey: ["audit", tenantSlug, selected?.id],
    queryFn: () => fetchAuditEvents(selected?.id),
    enabled: Boolean(selected?.id)
  });

  const reviewMutation = useMutation({
    mutationFn: createReview,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["records"] });
      queryClient.invalidateQueries({ queryKey: ["audit"] });
    }
  });

  return (
    <main className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div>
            <h1 className="text-xl font-semibold text-ink">ESG Ingestion Workbench</h1>
            <p className="text-sm text-steel">Raw provenance, validation issues, review decisions, and audit history.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <input className="h-9 border border-line px-3 text-sm" value={tenantSlug} onChange={(event) => setTenantSlug(event.target.value)} />
            <input className="h-9 border border-line px-3 text-sm" value={analystEmail} onChange={(event) => setAnalystEmail(event.target.value)} />
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-4 px-5 py-5 lg:grid-cols-[320px_minmax(0,1fr)]">
        <aside className="space-y-4">
          <UploadPanel />
          <QueueFilters status={status} setStatus={setStatus} suspicious={suspicious} setSuspicious={setSuspicious} refresh={() => recordsQuery.refetch()} />
          <RecordList records={records} selectedId={selected?.id} setSelectedId={setSelectedId} isLoading={recordsQuery.isLoading} />
        </aside>

        <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <RecordDetail record={selected} />
          <div className="space-y-4">
            <IssueTable record={selected} />
            <ApprovalPanel
              record={selected}
              analystEmail={analystEmail}
              onDecision={(decision, notes) =>
                reviewMutation.mutate({ recordId: selected.id, reviewer: analystEmail, decision, notes })
              }
              isSubmitting={reviewMutation.isPending}
              error={reviewMutation.error}
            />
            <AuditTimeline events={auditQuery.data || []} />
          </div>
        </section>
      </section>
    </main>
  );
}

function UploadPanel() {
  const [kind, setKind] = useState("sap");
  const [dataSourceId, setDataSourceId] = useState("");
  const [file, setFile] = useState(null);
  const [payload, setPayload] = useState('{"expenses": []}');
  const queryClient = useQueryClient();

  const sourcesQuery = useQuery({
    queryKey: ["data-sources"],
    queryFn: fetchDataSources
  });
  const sourceTypeByKind = {
    sap: "sap_csv",
    utility: "utility_csv",
    travel: "travel_json"
  };
  const dataSources = (sourcesQuery.data || []).filter((source) => source.source_type === sourceTypeByKind[kind]);

  const csvMutation = useMutation({
    mutationFn: uploadCsv,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["records"] })
  });
  const travelMutation = useMutation({
    mutationFn: ingestTravelJson,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["records"] })
  });

  const submit = () => {
    if (kind === "travel") {
      travelMutation.mutate({ dataSourceId, payload });
    } else {
      csvMutation.mutate({ kind, dataSourceId, file });
    }
  };

  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center gap-2">
        <FileUp size={18} />
        <h2 className="font-semibold">Ingestion</h2>
      </div>
      <label className="label">Source type</label>
      <select className="mt-1 h-9 w-full border border-line px-2" value={kind} onChange={(event) => {
        setKind(event.target.value);
        setDataSourceId("");
      }}>
        <option value="sap">SAP fuel CSV</option>
        <option value="utility">Utility electricity CSV</option>
        <option value="travel">Travel JSON</option>
      </select>
      <label className="label mt-3 block">Data source</label>
      <select className="mt-1 h-9 w-full border border-line px-2" value={dataSourceId} onChange={(event) => setDataSourceId(event.target.value)}>
        <option value="">Choose source</option>
        {dataSources.map((source) => (
          <option key={source.id} value={source.id}>
            {source.name}
          </option>
        ))}
      </select>
      {kind === "travel" ? (
        <textarea className="mt-3 h-28 w-full border border-line p-2 text-sm" value={payload} onChange={(event) => setPayload(event.target.value)} />
      ) : (
        <input className="mt-3 w-full text-sm" type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0])} />
      )}
      <button className="mt-3 flex h-9 w-full items-center justify-center gap-2 bg-mint px-3 text-sm font-semibold text-white disabled:opacity-50" onClick={submit} disabled={!dataSourceId || (kind !== "travel" && !file)}>
        <FileUp size={16} /> Ingest
      </button>
      {sourcesQuery.isError && <p className="mt-2 text-sm text-coral">Could not load data sources. Check that the backend is running and CORS is configured.</p>}
      {(csvMutation.error || travelMutation.error) && <p className="mt-2 text-sm text-coral">{csvMutation.error?.message || travelMutation.error?.message}</p>}
      {(csvMutation.isSuccess || travelMutation.isSuccess) && <p className="mt-2 text-sm text-mint">Ingestion completed. Refreshing review queue.</p>}
    </div>
  );
}

function QueueFilters({ status, setStatus, suspicious, setSuspicious, refresh }) {
  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold">Review queue</h2>
        <button className="border border-line p-2" onClick={refresh} title="Refresh records">
          <RefreshCw size={16} />
        </button>
      </div>
      <select className="h-9 w-full border border-line px-2" value={status} onChange={(event) => setStatus(event.target.value)}>
        <option value="">All statuses</option>
        <option value="pending">Pending</option>
        <option value="needs_changes">Needs changes</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
      </select>
      <label className="mt-3 flex items-center gap-2 text-sm">
        <input type="checkbox" checked={suspicious} onChange={(event) => setSuspicious(event.target.checked)} />
        Suspicious rows only
      </label>
    </div>
  );
}

function RecordList({ records, selectedId, setSelectedId, isLoading }) {
  return (
    <div className="panel max-h-[480px] overflow-auto">
      {isLoading && <div className="p-4 text-sm text-steel">Loading records...</div>}
      {!isLoading && records.length === 0 && <div className="p-4 text-sm text-steel">No records match the current filters.</div>}
      {records.map((record) => (
        <button
          key={record.id}
          className={`block w-full border-b border-line p-3 text-left text-sm ${selectedId === record.id ? "bg-panel" : "bg-white"}`}
          onClick={() => setSelectedId(record.id)}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="font-semibold">{record.source_reference || "No source reference"}</span>
            <StatusBadge status={record.review_status} />
          </div>
          <div className="mt-1 text-steel">{record.data_source_name}</div>
          <div className="mt-1 text-xs text-steel">
            {record.normalized_quantity ?? "-"} {record.normalized_unit}
          </div>
        </button>
      ))}
    </div>
  );
}

function RecordDetail({ record }) {
  if (!record) return <div className="panel p-5 text-sm text-steel">Select a record to inspect.</div>;
  return (
    <div className="panel p-5">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">{record.source_reference || record.id}</h2>
          <p className="text-sm text-steel">{record.category?.scope} / {record.category?.name}</p>
        </div>
        <StatusBadge status={record.review_status} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <ValueBlock title="Normalized values" data={{
          quantity: `${record.normalized_quantity ?? "-"} ${record.normalized_unit}`,
          activity_date: record.activity_date || "-",
          period: record.period_start ? `${record.period_start} to ${record.period_end}` : "-",
          facility_code: record.facility_code || "-",
          vendor_name: record.vendor_name || "-"
        }} />
        <ValueBlock title="Original raw values" data={record.original_values || {}} />
        <ValueBlock title="Edited values" data={record.edited_values || {}} />
        <ValueBlock title="Source metadata" data={{ provenance: record.provenance, route: record.route }} />
      </div>
    </div>
  );
}

function ValueBlock({ title, data }) {
  return (
    <div className="border border-line bg-panel p-3">
      <h3 className="mb-2 text-sm font-semibold">{title}</h3>
      <pre className="max-h-64 overflow-auto whitespace-pre-wrap break-words text-xs leading-5 text-ink">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}

function IssueTable({ record }) {
  const issues = record?.validation_issues || [];
  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center gap-2">
        <AlertTriangle size={18} />
        <h2 className="font-semibold">Validation issues</h2>
      </div>
      <div className="space-y-2">
        {issues.length === 0 && <p className="text-sm text-steel">No open issues on this record.</p>}
        {issues.map((issue) => (
          <div key={issue.id} className="border border-line p-2 text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-semibold">{issue.rule_code}</span>
              <span className={issue.severity === "error" ? "text-coral" : "text-amber"}>{issue.severity}</span>
            </div>
            <p className="mt-1 text-steel">{issue.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function ApprovalPanel({ record, analystEmail, onDecision, isSubmitting, error }) {
  const [notes, setNotes] = useState("");
  const disabled = !record || record.locked_at || isSubmitting;
  return (
    <div className="panel p-4">
      <h2 className="mb-3 font-semibold">Approval</h2>
      <textarea className="h-20 w-full border border-line p-2 text-sm" value={notes} onChange={(event) => setNotes(event.target.value)} placeholder={`Notes by ${analystEmail}`} />
      <div className="mt-3 grid grid-cols-3 gap-2">
        <button className="flex h-9 items-center justify-center gap-1 bg-mint text-sm font-semibold text-white disabled:opacity-50" disabled={disabled} onClick={() => onDecision("approved", notes)}>
          <CheckCircle2 size={15} /> Approve
        </button>
        <button className="flex h-9 items-center justify-center gap-1 bg-amber text-sm font-semibold text-white disabled:opacity-50" disabled={disabled} onClick={() => onDecision("needs_changes", notes)}>
          <Clock size={15} /> Hold
        </button>
        <button className="flex h-9 items-center justify-center gap-1 bg-coral text-sm font-semibold text-white disabled:opacity-50" disabled={disabled} onClick={() => onDecision("rejected", notes)}>
          <XCircle size={15} /> Reject
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-coral">{error.response?.data?.detail || error.response?.data?.non_field_errors?.join(" ") || error.message}</p>}
    </div>
  );
}

function AuditTimeline({ events }) {
  return (
    <div className="panel p-4">
      <div className="mb-3 flex items-center gap-2">
        <History size={18} />
        <h2 className="font-semibold">Audit timeline</h2>
      </div>
      <div className="space-y-3">
        {events.length === 0 && <p className="text-sm text-steel">No audit events yet.</p>}
        {events.map((event) => (
          <div key={event.id} className="border-l-2 border-mint pl-3 text-sm">
            <div className="font-semibold">{event.event_type}</div>
            <div className="text-xs text-steel">{event.occurred_at} - {event.actor || "system"}</div>
            <p className="mt-1 text-steel">{event.summary}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const tone = status === "approved" ? "bg-mint text-white" : status === "rejected" ? "bg-coral text-white" : "bg-panel text-ink";
  return <span className={`px-2 py-1 text-xs font-semibold ${tone}`}>{status}</span>;
}
