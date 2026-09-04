import { create } from "zustand";
import { SubjectProfile, SystemStatus, api } from "@/services/api";

interface AppState {
  subjects: SubjectProfile[];
  selectedSubjectId: string | null;
  systemStatus: SystemStatus | null;
  isLoading: boolean;
  error: string | null;

  fetchSubjects: () => Promise<void>;
  fetchSystemStatus: () => Promise<void>;
  selectSubject: (id: string) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  subjects: [],
  selectedSubjectId: null,
  systemStatus: null,
  isLoading: false,
  error: null,

  fetchSubjects: async () => {
    try {
      set({ isLoading: true, error: null });
      const subjects = await api.listSubjects();
      set({
        subjects,
        selectedSubjectId: get().selectedSubjectId || (subjects.length > 0 ? subjects[0].subject_id : null),
        isLoading: false,
      });
    } catch (err: any) {
      set({ error: err?.message || "Failed to load subjects", isLoading: false });
    }
  },

  fetchSystemStatus: async () => {
    try {
      const status = await api.getSystemStatus();
      set({ systemStatus: status });
    } catch (err: any) {
      console.error("Failed to load system status", err);
    }
  },

  selectSubject: (id: string) => {
    set({ selectedSubjectId: id });
  },
}));
