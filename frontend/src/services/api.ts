import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

export interface SubjectProfile {
  subject_id: string;
  name: string;
  available_quadrants: string[];
  created_at: string;
}

export interface DatasetIngestResult {
  subject_id: string;
  name: string;
  processed_count: number;
  valid_faces_count: number;
  discarded_count: number;
  quadrants_covered: string[];
}

export interface RenderJobResult {
  job_id: string;
  subject_id: string;
  target_image_path: string;
  mode: string;
  params: {
    identity_weight: number;
    wavelet_high_pass: number;
    codeformer_fidelity: number;
    occlusion_masking: boolean;
    source_quadrant: string | null;
  };
  status: string;
  progress: number;
  current_step: string;
  output_path: string | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface SystemStatus {
  status: string;
  vram: {
    total_mb: number;
    allocated_mb: number;
    reserved_mb: number;
    free_mb: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    free_gb: number;
  };
  models_dir: string;
  datasets_dir: string;
  outputs_dir: string;
}

export const api = {
  getSystemStatus: async (): Promise<SystemStatus> => {
    const res = await apiClient.get<SystemStatus>("/system/status");
    return res.data;
  },

  updateSystemPaths: async (paths: {
    models_dir?: string;
    datasets_dir?: string;
    outputs_dir?: string;
  }): Promise<SystemStatus> => {
    const res = await apiClient.post<SystemStatus>("/system/config/paths", paths);
    return res.data;
  },

  listSubjects: async (): Promise<SubjectProfile[]> => {
    const res = await apiClient.get<SubjectProfile[]>("/dataset/subjects");
    return res.data;
  },

  ingestDataset: async (
    subjectId: string,
    name: string,
    minSharpness: number,
    files: File[]
  ): Promise<DatasetIngestResult> => {
    const formData = new FormData();
    formData.append("subject_id", subjectId);
    formData.append("name", name);
    formData.append("min_sharpness", minSharpness.toString());
    files.forEach((file) => formData.append("images", file));

    const res = await apiClient.post<DatasetIngestResult>(
      "/dataset/ingest",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return res.data;
  },

  executeRender: async (
    subjectId: string,
    targetFile: File,
    mode: "EXPRESS" | "STUDIO_PRO",
    params: {
      identity_weight: number;
      wavelet_high_pass: number;
      codeformer_fidelity: number;
      occlusion_masking: boolean;
      source_quadrant?: string | null;
    }
  ): Promise<RenderJobResult> => {
    const formData = new FormData();
    formData.append("subject_id", subjectId);
    formData.append("mode", mode);
    formData.append("identity_weight", params.identity_weight.toString());
    formData.append("wavelet_high_pass", params.wavelet_high_pass.toString());
    formData.append("codeformer_fidelity", params.codeformer_fidelity.toString());
    formData.append("occlusion_masking", params.occlusion_masking ? "true" : "false");
    if (params.source_quadrant) {
      formData.append("source_quadrant", params.source_quadrant);
    }
    formData.append("target_image", targetFile);

    const res = await apiClient.post<RenderJobResult>("/render/execute", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  getJobStatus: async (jobId: string): Promise<RenderJobResult> => {
    const res = await apiClient.get<RenderJobResult>(`/render/job/${jobId}`);
    return res.data;
  },

  getSSEUrl: (jobId: string): string => `${API_BASE_URL}/render/stream/${jobId}`,
};
