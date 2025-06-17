import { create } from "zustand";
import { EmergencyModeSession, UnifiedQuestion } from "@/types/api/study.types";

interface EmergencyModeState {
  session: EmergencyModeSession | null;
  questions: UnifiedQuestion[];
  currentQuestionIndex: number;
  isSessionActive: boolean;
  setSession: (session: EmergencyModeSession) => void;
  setQuestions: (questions: UnifiedQuestion[]) => void;
  goToNextQuestion: () => void;
  endSession: () => void;
  updateSessionSettings: (settings: Partial<EmergencyModeSession>) => void;
}

export const useEmergencyModeStore = create<EmergencyModeState>((set, get) => ({
  session: null,
  questions: [],
  currentQuestionIndex: 0,
  isSessionActive: false,
  setSession: (session) =>
    set({ session, isSessionActive: true, currentQuestionIndex: 0 }),
  setQuestions: (questions) => set({ questions }),
  goToNextQuestion: () => {
    if (get().currentQuestionIndex < get().questions.length - 1) {
      set((state) => ({
        currentQuestionIndex: state.currentQuestionIndex + 1,
      }));
    } else {
      // Handle end of quiz
      set({ isSessionActive: false }); // Or move to a "completed" state
    }
  },
  endSession: () =>
    set({
      session: null,
      questions: [],
      currentQuestionIndex: 0,
      isSessionActive: false,
    }),
  updateSessionSettings: (settings) => {
    set((state) => ({
      session: state.session ? { ...state.session, ...settings } : null,
    }));
  },
}));
