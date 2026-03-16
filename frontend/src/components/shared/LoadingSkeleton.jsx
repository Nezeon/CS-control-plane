export default function LoadingSkeleton({ variant = 'card', count = 1 }) {
  const cls = variant === 'card' ? 'h-32 w-full rounded-xl' : 'h-3 rounded w-3/4'
  return (
    <div className={count > 1 ? 'flex flex-col gap-3' : ''}>
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className={`skeleton ${cls}`} />
      ))}
    </div>
  )
}
