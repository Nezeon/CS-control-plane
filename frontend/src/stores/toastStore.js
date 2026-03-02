import { create } from 'zustand'

let toastId = 0

const useToastStore = create((set) => ({
  toasts: [],

  addToast: ({ type = 'info', title, message, duration = 6000 }) => {
    const id = ++toastId
    set((state) => ({
      toasts: [...state.toasts, { id, type, title, message }].slice(-5),
    }))
    if (duration > 0) {
      setTimeout(() => {
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        }))
      }, duration)
    }
    return id
  },

  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id),
    }))
  },
}))

export default useToastStore
