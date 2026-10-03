import type { ReactNode } from 'react'

import { cx } from '../lib/cx'
import styles from './ButtonLink.module.css'

interface ButtonLinkProps {
  href: string
  variant?: 'solid' | 'line' | 'inverse' | 'inverseLine'
  /** Зовнішнє посилання: нова вкладка й підказка для скрінрідера */
  external?: boolean
  /** Додатковий текст лише для скрінрідера */
  hiddenSuffix?: string | undefined
  children: ReactNode
  className?: string | undefined
}

export function ButtonLink({ href, variant = 'solid', external = false, hiddenSuffix, children, className }: ButtonLinkProps) {
  const externalProps = external ? { target: '_blank', rel: 'noopener' } : {}
  return (
    <a className={cx(styles.button, styles[variant], className)} href={href} {...externalProps}>
      {children}
      {hiddenSuffix ? <span className="visually-hidden"> {hiddenSuffix}</span> : null}
    </a>
  )
}
