import { m } from 'framer-motion'

const pageVariants = {
  initial: {
    opacity: 0,
    y: 12,
  },
  enter: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: [0.16, 1, 0.3, 1],
      when: 'beforeChildren',
      staggerChildren: 0.06,
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: {
      duration: 0.2,
      ease: [0.4, 0, 1, 1],
    },
  },
}

export default function PageTransition({ children, className }) {
  return (
    <m.div
      variants={pageVariants}
      initial="initial"
      animate="enter"
      exit="exit"
      className={className}
    >
      {children}
    </m.div>
  )
}
