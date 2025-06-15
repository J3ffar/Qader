import { create } from "zustand";
import { AITone, CustomMessageType } from "@/types/api/conversation.types";
import { UnifiedQuestion } from "@/types/api/study.types";

interface ConversationState {
  sessionId: number | null;
  messages: CustomMessageType[];
  currentTestQuestion: UnifiedQuestion | null;
  isSending: boolean;
  aiTone: AITone;
  setSessionId: (id: number | null) => void;
  setMessages: (messages: CustomMessageType[]) => void;
  addMessage: (message: CustomMessageType) => void;
  setIsSending: (status: boolean) => void;
  setAiTone: (tone: AITone) => void;
  setCurrentTestQuestion: (question: UnifiedQuestion | null) => void;
  resetConversation: () => void;
}

const initialState = {
  sessionId: null,
  messages: [],
  currentTestQuestion: null,
  isSending: false,
  aiTone: "cheerful" as AITone,
};

export const useConversationStore = create<ConversationState>((set, get) => ({
  ...initialState,
  setSessionId: (id) => set({ sessionId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setIsSending: (status) => set({ isSending: status }),
  setAiTone: (tone) => set({ aiTone: tone }),
  setCurrentTestQuestion: (question) => set({ currentTestQuestion: question }),
  resetConversation: () => set(initialState),
}));
