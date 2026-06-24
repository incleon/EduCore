export function Button({ variant = 'primary', size, className = '', type = 'button', children, ...props }) {
  const style = variant === 'ghost' || variant === 'outline' ? 'secondary-button' : 'primary-button'
  return <button type={type} className={`${style} ${size === 'sm' ? 'button-small' : ''} ${className}`} {...props}>{children}</button>
}
