import { create } from 'zustand'

const useSettingsStore = create((set) => ({
  reducedMotion: localStorage.getItem('reducedMotion') === 'true',

  toggleReducedMotion: () =>
    set((state) => {
      const next = !state.reducedMotion
      localStorage.setItem('reducedMotion', String(next))

      if (next) {
        document.documentElement.classList.add('reduce-motion')
      } else {
        document.documentElement.classList.remove('reduce-motion')
      }

      return { reducedMotion: next }
    }),

  initialize: () => {
    const saved = localStorage.getItem('reducedMotion') === 'true'
    if (saved) {
      document.documentElement.classList.add('reduce-motion')
    }
    return saved
  },
}))

export default useSettingsStore
