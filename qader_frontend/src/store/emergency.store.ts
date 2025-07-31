import { create } from "zustand";
import {
  SuggestedPlan,
  UnifiedQuestion,
  EmergencyModeCompleteResponse,
} from "@/types/api/study.types";

type SessionStatus = "setup" | "active" | "completing" | "completed";

interface EmergencyModeState {
  sessionStatus: SessionStatus;
  sessionId: number | null;
  suggestedPlan: SuggestedPlan | null;
  questions: UnifiedQuestion[];
  currentQuestionIndex: number;
  isCalmModeActive: boolean;
  sessionResults: EmergencyModeCompleteResponse | null;

  startNewSession: (sessionId: number, plan: SuggestedPlan) => void;
  setQuestions: (questions: UnifiedQuestion[]) => void;
  goToNextQuestion: () => void;
  setCompleting: () => void;
  completeSession: (results: EmergencyModeCompleteResponse) => void;
  endSession: () => void;
  setCalmMode: (isActive: boolean) => void;
}

const initialState = {
  sessionStatus: "setup" as SessionStatus,
  sessionId: null,
  suggestedPlan: null,
  questions: [],
  currentQuestionIndex: 0,
  isCalmModeActive: false,
  sessionResults: null,
};

export const useEmergencyModeStore = create<EmergencyModeState>((set) => ({
  ...initialState,

  startNewSession: (sessionId, plan) =>
    set({
      sessionStatus: "active",
      sessionId,
      suggestedPlan: plan,
      questions: [],
      currentQuestionIndex: 0,
      sessionResults: null,
    }),

  setQuestions: (questions) => set({ questions }),

  goToNextQuestion: () => {
    set((state) => ({
      currentQuestionIndex: state.currentQuestionIndex + 1,
    }));
  },

  setCompleting: () => set({ sessionStatus: "completing" }),

  completeSession: (results) => {
    set({
      sessionStatus: "completed",
      sessionResults: results,
      questions: [],
      currentQuestionIndex: 0,
    });
  },

  // endSession now resets everything back to the setup screen
  endSession: () => set(initialState),

  setCalmMode: (isActive) => set({ isCalmModeActive: isActive }),
}));
