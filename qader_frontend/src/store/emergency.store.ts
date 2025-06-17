import { create } from "zustand";
import { SuggestedPlan, UnifiedQuestion } from "@/types/api/study.types";

interface EmergencyModeState {
  sessionId: number | null;
  suggestedPlan: SuggestedPlan | null;
  questions: UnifiedQuestion[];
  currentQuestionIndex: number;
  isSessionActive: boolean;
  isCalmModeActive: boolean;
  isSharedWithAdmin: boolean;

  startNewSession: (sessionId: number, plan: SuggestedPlan) => void;
  setQuestions: (questions: UnifiedQuestion[]) => void;
  goToNextQuestion: () => void;
  endSession: () => void;
  setCalmMode: (isActive: boolean) => void;
  setSharedWithAdmin: (isShared: boolean) => void;
}

const initialState = {
  sessionId: null,
  suggestedPlan: null,
  questions: [],
  currentQuestionIndex: 0,
  isSessionActive: false,
  isCalmModeActive: false,
  isSharedWithAdmin: false,
};

export const useEmergencyModeStore = create<EmergencyModeState>((set, get) => ({
  ...initialState,

  startNewSession: (sessionId, plan) =>
    set({
      sessionId,
      suggestedPlan: plan,
      isSessionActive: true,
      currentQuestionIndex: 0,
      questions: [], // Reset questions for the new session
    }),

  setQuestions: (questions) => set({ questions }),

  goToNextQuestion: () => {
    if (get().currentQuestionIndex < get().questions.length - 1) {
      set((state) => ({
        currentQuestionIndex: state.currentQuestionIndex + 1,
      }));
    } else {
      // Handle end of quiz by resetting state but keeping plan for review
      set({ isSessionActive: false, questions: [], currentQuestionIndex: 0 });
    }
  },

  endSession: () => set(initialState),

  setCalmMode: (isActive) => set({ isCalmModeActive: isActive }),
  setSharedWithAdmin: (isShared) => set({ isSharedWithAdmin: isShared }),
}));
