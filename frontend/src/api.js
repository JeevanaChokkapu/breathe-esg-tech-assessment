import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api"
});

export function setApiContext({ tenantSlug, analystEmail }) {
  api.defaults.headers.common["X-Tenant-Slug"] = tenantSlug;
  api.defaults.headers.common["X-Analyst-Email"] = analystEmail;
}

export async function fetchDataSources() {
  const { data } = await api.get("/data-sources/");
  return data.results || data;
}

export async function fetchRecords({ status, suspicious }) {
  const { data } = await api.get("/records/", {
    params: { status: status || undefined, suspicious: suspicious ? "true" : undefined }
  });
  return data.results || data;
}

export async function fetchAuditEvents(recordId) {
  if (!recordId) return [];
  const { data } = await api.get("/audit-events/", { params: { target_id: recordId } });
  return data.results || data;
}

export async function uploadCsv({ kind, dataSourceId, file }) {
  if (!dataSourceId) throw new Error("Choose a data source before uploading.");
  if (!file) throw new Error("Choose a CSV file before uploading.");
  const form = new FormData();
  form.append("data_source", dataSourceId);
  form.append("file", file);
  const path = kind === "utility" ? "/ingest/utility-csv/" : "/ingest/sap-csv/";
  const { data } = await api.post(path, form);
  return data;
}

export async function ingestTravelJson({ dataSourceId, payload }) {
  if (!dataSourceId) throw new Error("Choose a data source before ingesting travel data.");
  const parsed = JSON.parse(payload);
  const { data } = await api.post("/ingest/travel-json/", { ...parsed, data_source: dataSourceId });
  return data;
}

export async function createReview({ recordId, reviewer, decision, notes }) {
  const { data } = await api.post("/reviews/", {
    normalized_record: recordId,
    reviewer,
    decision,
    notes
  });
  return data;
}
