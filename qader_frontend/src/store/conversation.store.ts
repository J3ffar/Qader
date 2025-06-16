// src/store/conversation.store.ts
import { create } from "zustand";
import { AITone, CustomMessageType } from "@/types/api/conversation.types";
import { UnifiedQuestion } from "@/types/api/study.types";

interface ConversationState {
  sessionId: number | null;
  messages: CustomMessageType[];
  activeTestQuestion: UnifiedQuestion | null; // <-- RENAMED for clarity
  isSending: boolean;
  aiTone: AITone;
  setSessionId: (id: number | null) => void;
  setMessages: (messages: CustomMessageType[]) => void;
  addMessage: (message: CustomMessageType) => void;
  setIsSending: (status: boolean) => void;
  setAiTone: (tone: AITone) => void;
  setActiveTestQuestion: (question: UnifiedQuestion | null) => void; // <-- RENAMED
  resetConversation: () => void;
}

const initialState = {
  sessionId: null,
  messages: [],
  activeTestQuestion: null, // <-- RENAMED
  isSending: false,
  aiTone: "cheerful" as AITone,
};

export const useConversationStore = create<ConversationState>((set) => ({
  ...initialState,
  setSessionId: (id) => set({ sessionId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setIsSending: (status) => set({ isSending: status }),
  setAiTone: (tone) => set({ aiTone: tone }),
  setActiveTestQuestion: (question) => set({ activeTestQuestion: question }), // <-- RENAMED
  resetConversation: () => set(initialState),
}));
