export function Card({ className = '', children }) {
  return <section className={`panel ${className}`}>{children}</section>
}

export function CardHeader({ className = '', children }) {
  return <header className={className}>{children}</header>
}

export function CardTitle({ className = '', children }) {
  return <h2 className={className}>{children}</h2>
}

export function CardContent({ className = '', children }) {
  return <div className={className}>{children}</div>
}
